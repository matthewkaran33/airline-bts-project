"""Charts and dashboard preview for the BTS airline project, US domestic 2024.

Reads the route, carrier, monthly, and Chicago tables in data/ and writes PNGs
to charts/. Plain labels, no em dashes, consistent navy and gold palette.
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.gridspec import GridSpec

NAVY = "#1F4E79"
GOLD = "#C9A227"
RED = "#B42318"
GREY = "#6B7280"
LIGHT = "#E8EDF2"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "axes.edgecolor": "#9CA3AF",
    "axes.labelcolor": "#111111",
    "xtick.color": "#374151",
    "ytick.color": "#374151",
})

DATA = "/home/hatch/workspace/airline-bts-project/data"
CH = "/home/hatch/workspace/airline-bts-project/charts"

routes = pd.read_csv(f"{DATA}/route_level_2024.csv")
carriers = pd.read_csv(f"{DATA}/carrier_2024.csv")
monthly = pd.read_csv(f"{DATA}/monthly_2024.csv")
chicago = pd.read_csv(f"{DATA}/chicago_routes_2024.csv")

big = routes[(routes.sampled_passengers >= 500) & (routes.flights >= 500)].copy()
fare_big = routes[routes.sampled_passengers >= 500].copy()
carr = carriers.dropna(subset=["flights"]).sort_values("flights", ascending=False).head(12)


def save(fig, name):
    fig.tight_layout()
    fig.savefig(f"{CH}/{name}", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("wrote", name)


# 1. Most expensive routes ------------------------------------------------
top_fare = fare_big.nlargest(12, "avg_fare").iloc[::-1]
fig, ax = plt.subplots(figsize=(10, 6))
ax.barh(top_fare.origin + " to " + top_fare.dest, top_fare.avg_fare, color=NAVY)
for i, v in enumerate(top_fare.avg_fare):
    ax.text(v + 20, i, f"${v:,.0f}", va="center", fontsize=10)
ax.set_title("Most expensive routes by average fare, 2024")
ax.set_xlabel("Average fare, USD (passenger weighted)")
ax.set_xlim(0, top_fare.avg_fare.max() * 1.18)
save(fig, "top-fare-routes.png")

# 2. Fare vs delay scatter -------------------------------------------------
sample = big.sample(n=min(2500, len(big)), random_state=7)
fig, ax = plt.subplots(figsize=(10, 6))
ax.scatter(sample.avg_fare, sample.arr_del15_pct, s=14, alpha=0.35, color=NAVY)
ax.set_title("Paying more does not buy an on-time flight (r = 0.01)")
ax.set_xlabel("Average fare, USD")
ax.set_ylabel("Flights arriving 15+ min late, pct")
ax.set_xlim(0, 900)
save(fig, "fare-vs-delay.png")

# 3. Carrier reliability ---------------------------------------------------
carr_s = carr.sort_values("arr_del15_pct")
fig, ax = plt.subplots(figsize=(10, 6))
colors = [RED if v >= 25 else NAVY for v in carr_s.arr_del15_pct]
ax.barh(carr_s.carrier, carr_s.arr_del15_pct, color=colors)
for i, v in enumerate(carr_s.arr_del15_pct):
    ax.text(v + 0.5, i, f"{v:.1f}%", va="center", fontsize=10)
ax.set_title("Flights arriving 15+ min late by carrier, 2024")
ax.set_xlabel("Pct of operated flights")
ax.set_xlim(0, carr_s.arr_del15_pct.max() * 1.2)
save(fig, "carrier-delays.png")

# 4. Monthly trend ----------------------------------------------------------
fig, ax1 = plt.subplots(figsize=(10, 5.5))
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
ax1.plot(months, monthly.arr_del15_pct, color=NAVY, marker="o", linewidth=2.5,
         label="Arriving 15+ min late")
ax1.set_ylabel("Pct of operated flights")
ax1.set_title("2024 by month: July was the worst month, October the best")
ax2 = ax1.twinx()
ax2.bar(months, monthly.cancelled_pct, color=GOLD, alpha=0.75, label="Cancelled")
ax2.set_ylabel("Cancelled, pct of flights")
ax1.set_ylim(10, 32)
ax2.set_ylim(0, 4.5)
save(fig, "monthly-trend.png")

# 5. Chicago worst delays ----------------------------------------------------
chi_worst = chicago[(chicago.sampled_passengers >= 500) & (chicago.flights >= 500)]
chi_worst = chi_worst.nlargest(10, "arr_del15_pct").iloc[::-1]
fig, ax = plt.subplots(figsize=(10, 6))
ax.barh(chi_worst.origin + " to " + chi_worst.dest, chi_worst.arr_del15_pct, color=NAVY)
for i, v in enumerate(chi_worst.arr_del15_pct):
    ax.text(v + 0.6, i, f"{v:.1f}%", va="center", fontsize=10)
ax.set_title("Worst Chicago routes for delays, 2024")
ax.set_xlabel("Flights arriving 15+ min late, pct")
ax.set_xlim(0, chi_worst.arr_del15_pct.max() * 1.2)
save(fig, "chicago-delays.png")

# 6. Dashboard preview -------------------------------------------------------
fig = plt.figure(figsize=(16, 9))
gs = GridSpec(4, 4, figure=fig, hspace=0.55, wspace=0.35,
              left=0.05, right=0.98, top=0.86, bottom=0.06)
fig.suptitle("US Domestic Air Travel 2024: What a Ticket Costs, and What It Really Gets You",
             fontsize=17, fontweight="bold", x=0.05, ha="left", y=0.97)
fig.text(0.05, 0.925, "BTS DB1B fares plus On-Time reliability, 6,764 routes, 7.08 million flights",
         fontsize=11, color=GREY)

kpis = [("Average fare", "$233"), ("Flights", "7.08M"),
        ("Arriving 15+ min late", "20.8%"), ("Cancelled", "1.4%")]
for i, (label, value) in enumerate(kpis):
    ax = fig.add_subplot(gs[0, i])
    ax.axis("off")
    ax.add_patch(plt.Rectangle((0, 0), 1, 1, facecolor=LIGHT, edgecolor="none",
                               transform=ax.transAxes))
    ax.text(0.5, 0.62, value, ha="center", va="center", fontsize=22,
            fontweight="bold", transform=ax.transAxes)
    ax.text(0.5, 0.22, label, ha="center", va="center", fontsize=11,
            transform=ax.transAxes)

ax = fig.add_subplot(gs[1:3, 0:2])
ax.plot(months, monthly.arr_del15_pct, color=NAVY, marker="o", linewidth=2)
ax.set_title("Delayed 15+ min by month")
ax.set_ylabel("Pct of operated flights")

ax = fig.add_subplot(gs[1:3, 2:4])
tf = fare_big.nlargest(8, "avg_fare").iloc[::-1]
ax.barh(tf.origin + " to " + tf.dest, tf.avg_fare, color=NAVY)
ax.set_title("Most expensive routes, average fare")
ax.set_xlabel("USD")

ax = fig.add_subplot(gs[3, 0:2])
cs = carr.sort_values("arr_del15_pct").tail(8)
ax.barh(cs.carrier, cs.arr_del15_pct, color=NAVY)
ax.set_title("Most delayed carriers, pct 15+ min late")

ax = fig.add_subplot(gs[3, 2:4])
ax.scatter(sample.avg_fare, sample.arr_del15_pct, s=10, alpha=0.3, color=NAVY)
ax.set_title("Fare vs delay: no relationship (r = 0.01)")
ax.set_xlabel("Average fare, USD")
ax.set_ylabel("Pct 15+ min late")
ax.set_xlim(0, 900)

fig.savefig(f"{CH}/dashboard-preview.png", dpi=200, bbox_inches="tight")
print("wrote dashboard-preview.png")
