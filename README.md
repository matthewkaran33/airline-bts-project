# US Domestic Air Travel 2024: What a Ticket Costs, and What It Really Gets You

This report looks at United States domestic air travel in 2024 using two public data sets from the Bureau of Transportation Statistics (BTS). One set says what passengers paid. The other set says whether their flights left and arrived on time. Put together, they answer a plain question: when you pay more for a ticket, do you get a better trip?

The short answer is no. Across 6,764 routes, the link between what a route costs and how often its flights arrive late is basically zero. What you pay buys distance and a seat. It does not buy reliability.

# Travel Cost and Reliability Dashboard

## Project Overview

This project joins ticket fare data with flight reliability data for US domestic travel in 2024. The fare data comes from the BTS Airline Origin and Destination Survey (DB1B). The reliability data comes from the BTS Airline On-Time Performance data. The analysis covers 7,079,061 flights and 30,648,135 ticket records kept after cleaning.

The dashboard was built to help a traveler, or an analyst advising travelers, judge a route on both halves of the deal: the price and the chance the flight actually runs on time. A cheap ticket on a route that cancels 7 percent of the time is not the same deal as the same price on a route that cancels 1 percent of the time. This project makes that trade visible, route by route and carrier by carrier.

## Scenario

Air travel in the United States is sold on price. Search results sort by fare. Nothing on the booking page says that one route runs late twice as often as another, or that one carrier cancels three times as often as another. A traveler choosing between two flights sees the price gap and not the reliability gap.

This project starts from that gap. It treats the ticket price as only the first half of the cost of a trip. The second half is time: the chance of a late arrival, the chance of a cancellation, and the average delay when a flight does run late. A traveler who misses a connection or loses a day to a cancellation pays for that in ways the fare never shows.

The work uses 2024 because it is the most recent full year in both data sets, and because 2024 holds a useful stress test: the July 2024 summer meltdown, when delays and cancellations spiked across the whole system, and the calm October that followed. A method that cannot see both months is not measuring reliability at all.

## Strategic Purpose

The main goal of this project is to test whether price predicts reliability in US domestic air travel, and to show where the two come apart.

Three smaller goals sit under that one.

First, measure what routes really cost. That means a passenger weighted average fare per route, not a simple average of ticket prices, so that a route with ten thousand passengers counts more than a route with ten.

Second, measure how reliable each route and each carrier actually was. That means the share of flights arriving 15 or more minutes late, the share cancelled, and the average arrival delay in minutes.

Third, name the routes and carriers where the price story and the reliability story point in different directions. Those are the places where a traveler making a choice on price alone would get hurt, and where an analyst looking only at fares would miss the real story.

## Dashboard Preview

![Dashboard preview](charts/dashboard-preview.png)

## Data Sources

| Data set | What it holds | Coverage used here |
| --- | --- | --- |
| DB1B Market (BTS Airline Origin and Destination Survey) | A 10 percent sample of airline tickets, with origin airport, destination airport, passenger counts, and market fares | All four quarters of 2024, domestic markets only |
| Airline On-Time Performance (BTS) | One record per flight, with origin, destination, carrier, scheduled and actual times, delays, cancellations, and diversions | All twelve months of 2024, reporting carriers only |
| OpenFlights airport data | Airport codes used to check route labels | Reference only, no analysis fields taken from it |

Two facts about these sources shape everything in this report.

DB1B is a 10 percent sample of tickets. Passenger counts in this report are sampled passengers, not total passengers. A route with 113,281 sampled passengers carried roughly ten times that many real passengers. Fares, though, are not scaled up: the average fare on a route is the same whether you count the sample or the full market, as long as the sample is random, which BTS designs it to be.

On-Time data covers reporting carriers only. BTS requires on-time reporting from US carriers that hold at least 1 percent of domestic scheduled passenger revenue. Large carriers are all in. Some small carriers appear in the fare data but have no reliability data, because they fall below that line. Those carriers show fares in this project and blank reliability numbers, and the report says so wherever it matters instead of filling the gap with a guess.

## Data Preparation

The raw files were downloaded as prezipped CSVs from BTS TranStats: four DB1B Market files (one per quarter) and twelve On-Time files (one per month). The cleaning steps were:

- Kept domestic markets only. A market counted as domestic when both the origin country and the destination country were the United States. This keeps US territories in the data, because BTS counts them as domestic. That is why Guam and Pago Pago appear in the most expensive routes.
- Dropped fares under 50 dollars before averaging, following BTS guidance. Records below that line are mostly taxes and fees with no base fare attached, and keeping them would drag averages down for no real reason.
- Dropped records with zero or missing passengers, since a fare with no passengers behind it cannot be weighted.
- Turned the fare data into route totals. For each origin and destination pair, in one direction only, the project added up sampled passengers and passenger weighted fares. A route means one direction: Chicago O'Hare to New York LaGuardia is one route, and New York LaGuardia to Chicago O'Hare is a different one. Fares and delays often differ by direction, and averaging the two directions together would hide that.
- Turned the flight data into route totals the same way. For each origin and destination pair, the project counted flights, cancellations, diversions, flights arriving 15 or more minutes late, and total arrival delay minutes. Delay averages skip cancelled and diverted flights, because a flight that never arrived has no arrival delay to average.
- Joined the two route tables on origin and destination. The joined table holds 6,764 routes that appear in both data sets.
- Built three smaller tables from the joined data: one row per carrier, one row per month, and one table of routes touching Chicago O'Hare (ORD) or Chicago Midway (MDW).

Two practical notes on the build. The first run of the aggregation script ran out of memory, because it tried to hold whole quarters of ticket data at once. The script was rewritten to read each file in chunks of 300,000 rows and add up partial totals as it went, which fixed the problem. The second run failed on a column bug: the carrier and monthly tables do not carry departure delay sums, but the code asked for them. That was fixed too, and the third run finished clean. Both fixes are in the script, and the script is in this project so the whole build can be rerun.

## Key Performance Indicators (KPIs)

### Average Fare

The passenger weighted average fare across all domestic routes in 2024: **233.35 dollars**.

Passenger weighted means each ticket counts in proportion to how many passengers paid that fare. A route with 100,000 passengers moves the average far more than a route with 500. The middle route (the median across routes with 500 or more sampled passengers) averaged 234.72 dollars, close to the weighted average, which says the average is not being pulled around by a few giant routes.

### Total Flights

**7,079,061 flights** operated by reporting carriers in 2024.

### Delay Rate

**20.82 percent** of operated flights arrived 15 or more minutes late.

The median route (routes with 500 or more sampled passengers and 500 or more flights) ran late 20.26 percent of the time, close to the national rate. Delays were not confined to a few bad routes. They were spread across the whole system.

### Cancellation Rate

**1.36 percent** of flights were cancelled.

That average hides the real story, because cancellations bunch up hard on a small set of routes. The worst route cancelled 7.72 percent of its flights, more than five times the national rate.

### Average Arrival Delay

**7.10 minutes** across all operated flights.

Averages hide extremes. A flight that arrives 10 minutes early and a flight that arrives 3 hours late average out to a number that describes neither trip. That is why this report leans on the delay rate (the share of flights 15 or more minutes late) alongside the average, and why the route tables carry both.

## Dashboard Features

### Fare Analysis

- Average fare by route, passenger weighted, ranked highest to lowest
- Average fare by distance band, to test how much of the fare distance explains
- Cheapest routes and busiest routes side by side, so price and volume can be compared

### Reliability Analysis

- Delay rate by route: the share of flights arriving 15 or more minutes late
- Cancellation rate by route: the share of flights cancelled
- Monthly trend across 2024, so seasonal trouble shows up instead of being averaged away

### Carrier Analysis

- Delay rate, cancellation rate, and average fare for each reporting carrier
- Flight counts per carrier, so a small carrier with a bad rate is not read the same way as a large carrier with the same rate

### Chicago Focus

- The same fare and reliability tables cut down to routes touching O'Hare or Midway
- Chicago's priciest routes, worst delay routes, and worst cancellation routes listed separately

## Key Insights

### Paying more does not buy an on-time flight

Across routes with 500 or more sampled passengers and 500 or more flights, the correlation between average fare and the delay rate is 0.01. In plain words, there is no link at all. Expensive routes run late just as often as cheap ones.

The chart below makes the point visually. Each dot is a route. Fares run from under 100 dollars to over 800 dollars along the bottom. Delay rates run from under 10 percent to over 40 percent up the side. The dots form a flat cloud, not a slope. If paying more bought reliability, the cloud would tilt downward as fares rose. It does not tilt at all.

![Fare vs delay](charts/fare-vs-delay.png)

This is the single most useful finding in the project, because it cuts against how tickets are sold. A traveler who pays extra expecting a smoother trip is, on average, buying nothing of the kind. The extra money buys distance, or a popular departure time, or a carrier with a bigger network. It does not buy a flight that arrives on time more often.

### Distance explains only part of the fare

Across the same routes, the correlation between distance and average fare is 0.53. That is a real link, but a partial one. Distance explains roughly a quarter of the variation in fares from route to route, and the rest comes from other things: competition on the route, how many carriers fly it, the mix of business and leisure travelers, and hub pricing.

The distance bands show the same story in simpler form. Routes under 500 miles averaged 185.07 dollars. Routes from 500 to 999 miles averaged 206.02 dollars. Routes from 1,000 to 1,999 miles averaged 238.96 dollars. Routes of 2,000 miles or more averaged 347.64 dollars. Fares do rise with distance, but slowly: a route four times as long costs less than twice as much on average. And delay rates barely move across the bands at all, from 19.64 percent on the shortest routes to 20.44 percent on the longest. Longer flights are not less reliable. They are just longer.

### July 2024 was the worst month, and October the best

July 2024 was the worst month of the year on both measures that matter: 29.62 percent of flights arrived 15 or more minutes late, and 2.89 percent were cancelled, out of 634,613 flights. That is nearly one in three flights late and nearly one in thirty cancelled. May and June were bad too, at 26.41 percent and 24.94 percent late.

October had the lowest delay rate of the year at 13.20 percent late and 1.02 percent cancelled. November had the lowest cancellation rate at 0.46 percent. February was nearly as calm at 15.92 percent late and 0.58 percent cancelled.

January tells a different story from July. January had the highest cancellation rate of the year at 3.73 percent, but a middling delay rate of 24.06 percent. That pattern, many cancellations without extreme delays, fits winter weather: flights get cancelled outright rather than departing hours late. July fits summer system strain: flights still depart, but they run late in large numbers. The monthly table is worth reading as a whole, because the shape of trouble changes with the season.

![Monthly trend](charts/monthly-trend.png)

### The cheapest carriers are also among the least reliable, but the pattern is not clean

Average fares by carrier split into two clear groups. The ultra low cost carriers charge around 100 to 115 dollars on average: Allegiant at 102.00 dollars, Spirit at 113.40 dollars, Frontier at 113.41 dollars. The large legacy carriers charge around 285 to 305 dollars: American at 286.61 dollars, United at 300.28 dollars, Delta at 305.33 dollars. Southwest sits between the groups at 211.44 dollars, and JetBlue at 214.55 dollars.

Reliability splits less cleanly, but the cheap end of the market does worse. Frontier ran late 28.74 percent of the time and cancelled 2.32 percent of its flights, the worst delay rate and the worst cancellation rate among the large carriers. Spirit ran late 23.93 percent and cancelled 1.91 percent. Allegiant did better than its cheap peers at 21.67 percent late and 1.72 percent cancelled.

At the other end, Delta was the most reliable of the big four: 17.26 percent late and 0.91 percent cancelled, across 1,009,174 flights. United ran late 19.86 percent and cancelled 1.64 percent. Southwest ran late 20.60 percent and cancelled 0.83 percent, the lowest cancellation rate of any large carrier, across the most flights in the data at 1,419,419. American was the weakest of the big four: 26.13 percent late and 1.55 percent cancelled, with an average arrival delay of 15.31 minutes, far above Delta's 3.66 minutes.

Two cautions belong here. First, average arrival delay is pulled around by extreme delays, so a carrier with a few very bad days can look worse on that one number than on the delay rate. Second, carriers fly different route mixes, and a carrier heavy on storm exposed or congested airports will look worse through no fault of its own scheduling. The carrier table describes what happened. It does not by itself prove why.

![Carrier delays](charts/carrier-delays.png)

### Aspen cancellations are a class of their own

The most cancelled routes in the country are Aspen routes, and it is not close. Aspen to Houston cancelled 7.72 percent of its flights. Aspen to Los Angeles cancelled 6.84 percent. Aspen to Chicago O'Hare cancelled 6.53 percent. Aspen to Dallas Fort Worth cancelled 6.28 percent. Aspen to Denver cancelled 6.14 percent. The national rate is 1.36 percent.

Aspen appears on both sides of each pair, which rules out a single carrier or a single direction as the explanation. The route list alone does not say why Aspen cancels so often, and this project does not test a cause. The On-Time data does carry a cancellation reason code for each cancelled flight, and breaking Aspen cancellations down by reason and by month is the obvious next cut. What the current data does establish is the size of the gap: a traveler booking Aspen faces roughly five times the cancellation risk of the average domestic route.

### Dallas Fort Worth shows up again and again on the delay list

The most delayed route in the country is Key West to Dallas Fort Worth, at 45.75 percent of flights arriving 15 or more minutes late. Dallas Fort Worth also appears in six more of the fifteen most delayed routes: Dallas Fort Worth to Spokane at 40.21 percent, Dallas Fort Worth to Hartford at 39.83 percent, Dallas Fort Worth to Madison at 38.91 percent, Dallas Fort Worth to Columbia at 38.61 percent, Dallas Fort Worth to West Palm Beach at 37.64 percent, and Dallas Fort Worth to San Francisco at 37.52 percent.

San Francisco arrivals show up too: Charlotte to San Francisco at 39.67 percent, San Diego to San Francisco at 39.25 percent, Miami to San Francisco at 38.89 percent. Two hubs account for most of the worst delay list. That pattern points at hub congestion and arrival airport strain rather than at any single route's bad luck, though proving that would need airport level delay data the route table does not carry.

### Chicago: Hawaii costs the most, Huntsville and Seattle run latest

Chicago's priciest routes are Hawaii flying. Honolulu to O'Hare averaged 660.00 dollars, Maui to O'Hare 657.43 dollars, O'Hare to Maui 655.14 dollars, and O'Hare to Honolulu 654.81 dollars. Those four routes are also among the most reliable Hawaii routes in the data, with delay rates from 6.45 percent to 12.96 percent, far below the national rate of 20.82 percent. On Chicago to Hawaii, the high fare at least comes with a flight that usually arrives on time.

Chicago's worst delay routes are short and mid length domestic flying. O'Hare to Huntsville ran late 34.99 percent of the time. Midway to Seattle ran late 33.56 percent. Midway to Houston ran late 32.26 percent. O'Hare to Aspen ran late 32.02 percent, and Aspen to O'Hare cancelled 6.53 percent of the time, the worst cancellation rate of any Chicago route with real volume.

![Chicago delays](charts/chicago-delays.png)

### The busiest routes are not the priciest routes

The busiest route by passengers was Los Angeles to New York JFK, with 113,281 sampled passengers and an average fare of 493.59 dollars, across 9,915 flights. The busiest route by flights was the short hop between Maui's Kahului airport and Honolulu: 11,642 flights in the year, about 32 a day, at an average fare of 87.83 dollars.

The cheapest routes in the data are small leisure markets flown by ultra low cost carriers: Columbus Rickenbacker to Myrtle Beach at 73.41 dollars, Orlando Sanford to Concord-Paducah at 74.62 dollars, and Myrtle Beach to Columbus Rickenbacker at 74.78 dollars. Cheap, in this data, means short, leisure heavy, and thinly served, not unreliable by default: Portland to Provo at 76.76 dollars ran late only 13.89 percent of the time.

## Recommendations

### 1. Judge a route on fare and reliability together, never on fare alone

The core finding of this project is that price carries no information about reliability. A traveler choosing between two flights on the same route should check the route's delay rate and cancellation rate before paying extra for a higher fare. The route table in this project is built for exactly that check, and it is the table a traveler facing a real choice should open first.

### 2. Treat Aspen and Dallas Fort Worth connections with extra care

Aspen bookings carry roughly five times the average cancellation risk. Dallas Fort Worth connections sit on the most delayed routes in the country. Neither fact means avoiding those airports. It means building in slack: an earlier flight, a longer connection, or a backup plan, on routes where the data says trouble is normal rather than rare.

### 3. Do not read a low fare as a warning, or a high fare as a promise

The cheapest routes in the data include some of the most reliable ones, and the most expensive routes include some of the least. Frontier's low fares come with the worst delay rate among large carriers, but Allegiant's low fares do not. Judge the carrier and the route, not the price tag.

### 4. For analysts: add capacity and cancellation reasons next

Two gaps limit what this project can say. First, it has no seat capacity data, so it cannot say how full flights were or whether full flights run later than empty ones. The BTS T100 capacity files would fill that gap, and they are the first data set to add. Second, it does not break cancellations down by reason code, which the On-Time data does carry. That cut would test whether Aspen cancellations are weather, carrier, or airspace driven, instead of leaving the question open as this report does.

### 5. Rebuild the dashboard in Tableau for presentation

The charts in this project are static images. The cleaned route table is shaped for a Tableau dashboard: one row per route, with fare, delay rate, cancellation rate, flights, and passengers as measures, and origin, destination, carrier, and month as filters. A Tableau version would let a reader filter to their own airport and see their own routes, which a static report cannot do.

## Tools Used

- Python and pandas for cleaning and aggregation
- Matplotlib for charts and the dashboard preview image
- BTS TranStats prezipped CSV files as the raw data source
- Git for version control of the project files

## Skills Demonstrated

- Joining two large public data sets on a shared key (airport pair) at route level
- Passenger weighted averages, so high volume routes count in proportion to their passengers
- Working with data too large to hold in memory at once, by reading files in chunks and adding up partial totals
- Correlation analysis with plain language interpretation: what a correlation of 0.01 and a correlation of 0.53 each mean in words
- Honest limits: saying which carriers lack reliability data, which questions the data cannot answer, and what the next cut should be
- Writing findings so a non analyst can follow every number back to what it counts

## Limitations and Next Steps

- DB1B is a 10 percent sample. Passenger counts are sampled counts. Fares are averages over the sample and are the best available estimate of market fares, not a census of every ticket sold.
- Fares under 50 dollars were dropped per BTS guidance. If some of those records were real low fares rather than tax only records, average fares on the cheapest routes are slightly overstated.
- On-Time data covers reporting carriers only. Small carriers in the fare data have no reliability numbers here. Their blank cells are missing data, not zero delays.
- The DB1B fare class field was not used, because the Department of Transportation warns that carriers code fare classes differently, so the field does not mean the same thing across carriers.
- Distance in DB1B is market distance, which can include ground transport legs. It is close to flight distance on most routes but not identical to it.
- This project describes 2024. Fares, schedules, and carrier networks change every year, and nothing here should be read as a forecast for 2025 or 2026.
- Next steps, in order: add T100 seat capacity for load factor analysis, break cancellations down by reason code and month, and rebuild the dashboard in Tableau with airport filters.

## How to Reproduce

1. Download the raw files from BTS TranStats: DB1B Market files named Origin_and_Destination_Survey_DB1BMarket_2024_1.zip through _4.zip, and On-Time files named On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2024_1.zip through _12.zip. Put them in data/raw.
2. Run build_routes.py. It reads each file in chunks, builds the route level, carrier level, monthly, and Chicago tables, and writes them plus findings.txt into data.
3. Run make_charts.py. It reads the tables in data and writes the charts and the dashboard preview image into charts.
4. The numbers in this README come from data/findings.txt and from the tables in data. Every figure in the Key Insights section can be traced back to a row in one of those tables.

## Author

Matthew Karan, independent media researcher. GitHub: github.com/matthewkaran33.
