import csv
import random
from datetime import datetime, timedelta

stocks = {
	"TCS": 3800, "INFY": 1500, "RELIANCE": 2900, "HDFCBANK": 1600,
	"ICICIBANK": 1100, "WIPRO": 480, "ITC": 430, "SBIN": 780,
	"LT": 3500, "TATAMOTORS": 950,
}

# 12 trading days starting from a weekday
start_day = datetime(2026, 9, 1)
days = []
d = start_day
while len(days) < 12:
	if d.weekday() < 5:  # Mon-Fri only
		days.append(d)
	d += timedelta(days=1)

rows = []
for symbol, price in stocks.items():
	current = price
	for day in days:
		t = day.replace(hour=9, minute=30)
		end = day.replace(hour=15, minute=30)
		while t <= end:
			current = round(current * (1 + random.uniform(-0.01, 0.01)), 2)
			rows.append([symbol, t.strftime("%Y-%m-%d %H:%M:%S"), current])
			t += timedelta(minutes=30)

with open("data/stock_prices.csv", "w", newline="") as f:
	writer = csv.writer(f)
	writer.writerow(["symbol", "datetime", "price"])
	writer.writerows(rows)

print(f"Done! {len(rows)} rows written.")
