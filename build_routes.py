"""Build route level tables for the BTS airline project, US domestic 2024.

Inputs (BTS TranStats prezips, already downloaded):
  data/raw/Origin_and_Destination_Survey_DB1BMarket_2024_{1..4}.zip  (fares)
  data/raw/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2024_{1..12}.zip (reliability)

Outputs (data/):
  route_level_2024.csv   - one row per airport pair: fares, flights, delays, cancellations
  carrier_2024.csv       - one row per carrier: flights, delays, cancellations, avg fare
  monthly_2024.csv       - one row per month: flights, delays, cancellations
  chicago_routes_2024.csv - routes touching ORD or MDW
  findings.txt           - headline numbers for the README

Method notes (stated plainly, as they will appear in the README):
  - DB1B is a 10 percent sample of tickets. Passenger counts below are sampled
    passengers, not total passengers. Fares are weighted by passengers.
  - BTS guidance: fares under $50 are dropped before averaging, because those
    records are mostly taxes and fees with no base fare.
  - On-Time covers reporting carriers only (carriers with at least 1 percent of
    domestic scheduled passenger revenue). Delay averages skip cancelled and
    diverted flights, since those flights have no arrival delay.
  - A route is an airport pair in one direction (ORD to LAX is not LAX to ORD).
  - Load factor is NOT in this version: the T100 capacity file uses a different
    download route and is listed as a next step in the README.
"""

import glob
import os
import zipfile

import numpy as np
import pandas as pd

RAW = os.path.expanduser("~/workspace/airline-bts-project/data/raw")
OUT = os.path.expanduser("~/workspace/airline-bts-project/data")
os.makedirs(OUT, exist_ok=True)


def read_zip_csv(path, usecols=None, chunksize=None):
    """Read the single CSV inside a BTS prezip file."""
    with zipfile.ZipFile(path) as zf:
        names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        assert len(names) == 1, (path, names)
        return pd.read_csv(zf.open(names[0]), usecols=usecols, chunksize=chunksize,
                           low_memory=False)


def pick(df, candidates):
    """Return the first column in df whose lowercase name matches a candidate."""
    lower = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in lower:
            return lower[cand.lower()]
    raise KeyError(f"none of {candidates} in {list(df.columns)[:20]}")


# ---------------------------------------------------------------- DB1B fares
print("== DB1B Market 2024 (fares) ==")
fare_route_parts = []
fare_carrier_parts = []
fare_records_kept = 0
for path in sorted(glob.glob(os.path.join(RAW, "Origin_and_Destination_Survey_DB1BMarket_2024_*.zip"))):
    with zipfile.ZipFile(path) as zf:
        name = [n for n in zf.namelist() if n.lower().endswith(".csv")][0]
        with zf.open(name) as fh:
            header = pd.read_csv(fh, nrows=0)
    oc = pick(header, ["Origin"])
    dc = pick(header, ["Dest"])
    ocountry = pick(header, ["OriginCountry"])
    dcountry = pick(header, ["DestCountry"])
    pax = pick(header, ["Passengers"])
    fare = pick(header, ["MktFare"])
    dist = pick(header, ["MktDistance"])
    carrier = pick(header, ["RPCarrier"])
    print(os.path.basename(path), "->", oc, dc, pax, fare, dist, carrier, flush=True)
    with zipfile.ZipFile(path) as zf:
        name = [n for n in zf.namelist() if n.lower().endswith(".csv")][0]
        with zf.open(name) as fh:
            for chunk in pd.read_csv(
                    fh, usecols=[oc, dc, ocountry, dcountry, pax, fare, dist, carrier],
                    chunksize=300_000, low_memory=False):
                chunk = chunk.rename(columns={oc: "origin", dc: "dest", pax: "passengers",
                                              fare: "fare", dist: "distance", carrier: "carrier"})
                # Domestic only, real fares only (BTS $50 rule), positive passengers.
                chunk = chunk[(chunk[ocountry] == "US") & (chunk[dcountry] == "US")]
                chunk["passengers"] = pd.to_numeric(chunk.passengers, errors="coerce")
                chunk["fare"] = pd.to_numeric(chunk.fare, errors="coerce")
                chunk["distance"] = pd.to_numeric(chunk.distance, errors="coerce")
                chunk = chunk[(chunk.fare >= 50) & (chunk.passengers > 0)]
                if len(chunk) == 0:
                    continue
                fare_records_kept += len(chunk)
                chunk["fare_x_pax"] = chunk.fare * chunk.passengers
                chunk["dist_x_pax"] = chunk.distance * chunk.passengers
                # Aggregate per chunk so a full quarter never sits in memory.
                fare_route_parts.append(chunk.groupby(["origin", "dest"]).agg(
                    passengers=("passengers", "sum"),
                    fare_x_pax=("fare_x_pax", "sum"),
                    dist_x_pax=("dist_x_pax", "sum"),
                ).reset_index())
                fare_carrier_parts.append(chunk.groupby(["carrier"]).agg(
                    passengers=("passengers", "sum"),
                    fare_x_pax=("fare_x_pax", "sum"),
                ).reset_index())
    print("   kept so far:", f"{fare_records_kept:,}", flush=True)

print("DB1B total kept:", fare_records_kept)

# Route level fares: passenger weighted average fare.
_route = pd.concat(fare_route_parts, ignore_index=True).groupby(
    ["origin", "dest"], as_index=False).sum(numeric_only=True)
route_fare = _route
route_fare["avg_fare"] = route_fare.fare_x_pax / route_fare.passengers
route_fare["distance"] = route_fare.dist_x_pax / route_fare.passengers
route_fare["fare_per_mile"] = route_fare.avg_fare / route_fare.distance
route_fare = route_fare.rename(columns={"passengers": "sampled_passengers"})
route_fare = route_fare.drop(columns=["fare_x_pax", "dist_x_pax"])

# Carrier level fares.
_car = pd.concat(fare_carrier_parts, ignore_index=True).groupby(
    "carrier", as_index=False).sum(numeric_only=True)
carrier_fare = _car
carrier_fare["avg_fare"] = carrier_fare.fare_x_pax / carrier_fare.passengers
carrier_fare = carrier_fare.rename(columns={"passengers": "sampled_passengers"})
carrier_fare = carrier_fare.drop(columns=["fare_x_pax"])

# ------------------------------------------------------- On-Time reliability
print("== On-Time 2024 (reliability) ==")
route_parts = []
carrier_parts = []
monthly_parts = []
for path in sorted(glob.glob(os.path.join(RAW, "On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2024_*.zip"))):
    with zipfile.ZipFile(path) as zf:
        name = [n for n in zf.namelist() if n.lower().endswith(".csv")][0]
        with zf.open(name) as fh:
            header = pd.read_csv(fh, nrows=0)
    oc = pick(header, ["Origin"])
    dc = pick(header, ["Dest"])
    car = pick(header, ["Reporting_Airline", "Operating_Airline", "Carrier"])
    mon = pick(header, ["Month"])
    canc = pick(header, ["Cancelled"])
    div = pick(header, ["Diverted"])
    arrd = pick(header, ["ArrDelay"])
    depd = pick(header, ["DepDelay"])
    arr15 = pick(header, ["ArrDel15"])
    print(os.path.basename(path), "->", oc, dc, car, mon, canc, div, arrd, depd, arr15)
    with zipfile.ZipFile(path) as zf:
        name = [n for n in zf.namelist() if n.lower().endswith(".csv")][0]
        with zf.open(name) as fh:
            for chunk in pd.read_csv(fh, usecols=[oc, dc, car, mon, canc, div, arrd, depd, arr15],
                                     chunksize=200_000, low_memory=False):
                chunk = chunk.rename(columns={oc: "origin", dc: "dest", car: "carrier",
                                              mon: "month", canc: "cancelled", div: "diverted",
                                              arrd: "arr_delay", depd: "dep_delay", arr15: "arr_del15"})
                chunk["cancelled"] = pd.to_numeric(chunk.cancelled, errors="coerce").fillna(0)
                chunk["diverted"] = pd.to_numeric(chunk.diverted, errors="coerce").fillna(0)
                chunk["arr_delay"] = pd.to_numeric(chunk.arr_delay, errors="coerce")
                chunk["dep_delay"] = pd.to_numeric(chunk.dep_delay, errors="coerce")
                chunk["arr_del15"] = pd.to_numeric(chunk.arr_del15, errors="coerce")
                chunk["operated"] = ((chunk.cancelled == 0) & (chunk.diverted == 0)).astype(int)
                chunk["arr_del15_flag"] = (chunk.arr_del15 == 1).astype(int)
                route_parts.append(chunk.groupby(["origin", "dest"]).agg(
                    flights=("operated", "size"),
                    cancelled=("cancelled", "sum"),
                    diverted=("diverted", "sum"),
                    operated=("operated", "sum"),
                    arr_delay_sum=("arr_delay", "sum"),
                    arr_delay_n=("arr_delay", "count"),
                    dep_delay_sum=("dep_delay", "sum"),
                    dep_delay_n=("dep_delay", "count"),
                    arr_del15=("arr_del15_flag", "sum"),
                ).reset_index())
                carrier_parts.append(chunk.groupby(["carrier"]).agg(
                    flights=("operated", "size"),
                    cancelled=("cancelled", "sum"),
                    diverted=("diverted", "sum"),
                    operated=("operated", "sum"),
                    arr_delay_sum=("arr_delay", "sum"),
                    arr_delay_n=("arr_delay", "count"),
                    arr_del15=("arr_del15_flag", "sum"),
                ).reset_index())
                monthly_parts.append(chunk.groupby(["month"]).agg(
                    flights=("operated", "size"),
                    cancelled=("cancelled", "sum"),
                    diverted=("diverted", "sum"),
                    operated=("operated", "sum"),
                    arr_delay_sum=("arr_delay", "sum"),
                    arr_delay_n=("arr_delay", "count"),
                    arr_del15=("arr_del15_flag", "sum"),
                ).reset_index())
    print("   done", os.path.basename(path))


def combine(parts, keys):
    df = pd.concat(parts, ignore_index=True)
    num = [c for c in df.columns if c not in keys]
    return df.groupby(keys, as_index=False)[num].sum()


route_rel = combine(route_parts, ["origin", "dest"])
carrier_rel = combine(carrier_parts, ["carrier"])
monthly_rel = combine(monthly_parts, ["month"])

overall_arr_delay = route_rel.arr_delay_sum.sum() / route_rel.arr_delay_n.sum()

for df in (route_rel, carrier_rel, monthly_rel):
    df["cancelled_pct"] = 100 * df.cancelled / df.flights
    df["diverted_pct"] = 100 * df.diverted / df.flights
    df["avg_arr_delay_min"] = df.arr_delay_sum / df.arr_delay_n
    df["arr_del15_pct"] = 100 * df.arr_del15 / df.operated
    if "dep_delay_sum" in df.columns:
        df["avg_dep_delay_min"] = df.dep_delay_sum / df.dep_delay_n
    df.drop(columns=[c for c in ["arr_delay_sum", "arr_delay_n", "dep_delay_sum", "dep_delay_n"]
                     if c in df.columns], inplace=True)

# ------------------------------------------------------------- Merge and save
routes = route_fare.merge(route_rel, on=["origin", "dest"], how="inner")
routes = routes.sort_values("sampled_passengers", ascending=False)
routes.to_csv(os.path.join(OUT, "route_level_2024.csv"), index=False)

carriers = carrier_fare.merge(carrier_rel, on="carrier", how="outer")
carriers.to_csv(os.path.join(OUT, "carrier_2024.csv"), index=False)

monthly_rel = monthly_rel.sort_values("month")
monthly_rel.to_csv(os.path.join(OUT, "monthly_2024.csv"), index=False)

chi = routes[routes.origin.isin(["ORD", "MDW"]) | routes.dest.isin(["ORD", "MDW"])]
chi.to_csv(os.path.join(OUT, "chicago_routes_2024.csv"), index=False)

# ------------------------------------------------------------- Headline numbers
def wavg(df, val, w):
    return float((df[val] * df[w]).sum() / df[w].sum())

lines = []
lines.append(f"DB1B fare records kept (domestic, fare >= $50): {fare_records_kept:,}")
lines.append(f"Routes in merged table: {len(routes):,}")
lines.append(f"Total sampled passengers (DB1B 10 pct sample): {routes.sampled_passengers.sum():,.0f}")
lines.append(f"Total On-Time flights 2024: {route_rel.flights.sum():,.0f}")
lines.append(f"Overall passenger weighted avg fare: ${wavg(routes, 'avg_fare', 'sampled_passengers'):,.2f}")
lines.append(f"Overall cancelled pct: {100 * route_rel.cancelled.sum() / route_rel.flights.sum():.2f}%")
lines.append(f"Overall arrival delay 15+ pct (of operated): {100 * route_rel.arr_del15.sum() / route_rel.operated.sum():.2f}%")
lines.append(f"Overall avg arrival delay min: {overall_arr_delay:.2f}")
big = routes[routes.sampled_passengers >= 500]
lines.append(f"Routes with 500+ sampled passengers: {len(big):,}")
lines.append(f"Fare vs distance correlation (routes 500+ pax): {big[['avg_fare', 'distance']].corr().iloc[0, 1]:.3f}")
lines.append(f"Fare vs delay15 correlation (routes 500+ pax): {big[['avg_fare', 'arr_del15_pct']].corr().iloc[0, 1]:.3f}")
lines.append("")
lines.append("TOP 15 ROUTES BY AVG FARE (500+ sampled passengers):")
top = big.nlargest(15, "avg_fare")[["origin", "dest", "avg_fare", "sampled_passengers", "distance", "flights", "arr_del15_pct", "cancelled_pct"]]
lines.append(top.to_string(index=False))
lines.append("")
lines.append("TOP 15 ROUTES BY DELAY 15+ PCT (500+ sampled passengers, 500+ flights):")
big2 = big[big.flights >= 500]
topd = big2.nlargest(15, "arr_del15_pct")[["origin", "dest", "avg_fare", "sampled_passengers", "flights", "arr_del15_pct", "cancelled_pct"]]
lines.append(topd.to_string(index=False))
lines.append("")
lines.append("TOP 15 ROUTES BY CANCELLATION PCT (500+ sampled passengers, 500+ flights):")
topc = big2.nlargest(15, "cancelled_pct")[["origin", "dest", "avg_fare", "sampled_passengers", "flights", "arr_del15_pct", "cancelled_pct"]]
lines.append(topc.to_string(index=False))
lines.append("")
lines.append("CARRIERS (by flights):")
car = carriers.sort_values("flights", ascending=False)
lines.append(car.to_string(index=False))
lines.append("")
lines.append("MONTHLY 2024:")
lines.append(monthly_rel.to_string(index=False))
lines.append("")
lines.append("CHICAGO TOP 10 BY AVG FARE (500+ sampled passengers):")
chib = chi[chi.sampled_passengers >= 500].nlargest(10, "avg_fare")[["origin", "dest", "avg_fare", "sampled_passengers", "flights", "arr_del15_pct", "cancelled_pct"]]
lines.append(chib.to_string(index=False))
lines.append("")
lines.append("CHICAGO WORST 10 BY DELAY 15+ PCT (500+ sampled passengers, 500+ flights):")
chid = chi[(chi.sampled_passengers >= 500) & (chi.flights >= 500)].nlargest(10, "arr_del15_pct")[["origin", "dest", "avg_fare", "sampled_passengers", "flights", "arr_del15_pct", "cancelled_pct"]]
lines.append(chid.to_string(index=False))

with open(os.path.join(OUT, "findings.txt"), "w") as fh:
    fh.write("\n".join(lines) + "\n")
print("\n".join(lines[:12]))
print("Saved to", OUT)
