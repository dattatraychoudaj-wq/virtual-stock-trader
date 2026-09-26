import csv
import sqlite3
from pathlib import Path

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

DATA_FILE = Path(__file__).parent / "data" / "stock_prices.csv"
STARTING_BALANCE = 100000

db = sqlite3.connect(":memory:", check_same_thread=False)
db.row_factory = sqlite3.Row


def init_db():
	if not DATA_FILE.exists():
		raise FileNotFoundError(
			f"Stock data not found at {DATA_FILE}. Run generate_data.py first."
		)

	with DATA_FILE.open(newline="", encoding="utf-8") as csv_file:
		reader = csv.DictReader(csv_file)
		if reader.fieldnames != ["symbol", "datetime", "price"]:
			raise ValueError("Stock CSV must have symbol, datetime, and price columns.")
		db.execute(
			"CREATE TABLE prices (symbol TEXT NOT NULL, datetime TEXT NOT NULL, price REAL NOT NULL)"
		)
		db.executemany(
			"INSERT INTO prices (symbol, datetime, price) VALUES (?, ?, ?)",
			((row["symbol"], row["datetime"], float(row["price"])) for row in reader),
		)

	db.execute(
		"""
		CREATE TABLE portfolio (
			symbol TEXT PRIMARY KEY,
			quantity INTEGER NOT NULL,
			avg_price REAL NOT NULL
		)
		"""
	)
	db.execute(
		"""
		CREATE TABLE transactions (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			symbol TEXT NOT NULL,
			action TEXT NOT NULL,
			quantity INTEGER NOT NULL,
			price REAL NOT NULL,
			trade_time TEXT NOT NULL,
			created_at TEXT DEFAULT CURRENT_TIMESTAMP
		)
		"""
	)
	db.execute("CREATE TABLE account (id INTEGER PRIMARY KEY, balance REAL NOT NULL)")
	db.execute("INSERT INTO account (id, balance) VALUES (1, ?)", (STARTING_BALANCE,))
	db.commit()


init_db()


@app.route("/")
def home():
	return render_template("index.html")


@app.route("/stocks")
def stocks():
	rows = db.execute("SELECT DISTINCT symbol FROM prices ORDER BY symbol").fetchall()
	return jsonify([row["symbol"] for row in rows])


@app.route("/price")
def get_price():
	symbol = request.args.get("symbol")
	dt = request.args.get("datetime")

	if not symbol or not dt:
		return jsonify({"error": "symbol and datetime are required"}), 400

	row = db.execute(
		"""
		SELECT symbol, datetime, price
		FROM prices
		WHERE symbol = ? AND datetime <= ?
		ORDER BY datetime DESC
		LIMIT 1
		""",
		(symbol, dt),
	).fetchone()

	if not row:
		return jsonify({"error": "No price found for that symbol/time"}), 404

	return jsonify(
		{
			"symbol": row["symbol"],
			"datetime": row["datetime"],
			"price": row["price"],
		}
	)


@app.route("/buy", methods=["POST"])
def buy():
	data = request.get_json(silent=True)
	if not isinstance(data, dict):
		return jsonify({"error": "symbol, quantity and datetime are required"}), 400

	symbol = data.get("symbol")
	quantity = data.get("quantity")
	dt = data.get("datetime")
	if not isinstance(symbol, str) or not symbol.strip() or not dt:
		return jsonify({"error": "symbol, quantity and datetime are required"}), 400

	if isinstance(quantity, bool):
		return jsonify({"error": "quantity must be a positive whole number"}), 400
	try:
		parsed_quantity = int(quantity)
	except (TypeError, ValueError):
		return jsonify({"error": "quantity must be a positive whole number"}), 400
	if parsed_quantity <= 0 or (isinstance(quantity, float) and quantity != parsed_quantity):
		return jsonify({"error": "quantity must be a positive whole number"}), 400

	price_row = db.execute(
		"""
		SELECT price FROM prices
		WHERE symbol = ? AND datetime <= ?
		ORDER BY datetime DESC
		LIMIT 1
		""",
		(symbol, dt),
	).fetchone()
	if not price_row:
		return jsonify({"error": "No price found for that symbol/time"}), 404

	price = price_row["price"]
	cost = price * parsed_quantity
	account = db.execute("SELECT balance FROM account WHERE id = 1").fetchone()
	if account["balance"] < cost:
		return jsonify({"error": "Insufficient balance"}), 400

	db.execute("UPDATE account SET balance = balance - ? WHERE id = 1", (cost,))
	existing = db.execute(
		"SELECT quantity, avg_price FROM portfolio WHERE symbol = ?", (symbol,)
	).fetchone()
	if existing:
		new_quantity = existing["quantity"] + parsed_quantity
		new_average = (
			existing["avg_price"] * existing["quantity"] + cost
		) / new_quantity
		db.execute(
			"UPDATE portfolio SET quantity = ?, avg_price = ? WHERE symbol = ?",
			(new_quantity, new_average, symbol),
		)
	else:
		db.execute(
			"INSERT INTO portfolio (symbol, quantity, avg_price) VALUES (?, ?, ?)",
			(symbol, parsed_quantity, price),
		)

	db.execute(
		"""
		INSERT INTO transactions (symbol, action, quantity, price, trade_time)
		VALUES (?, 'BUY', ?, ?, ?)
		""",
		(symbol, parsed_quantity, price, dt),
	)
	db.commit()

	return jsonify(
		{
			"message": "Buy successful",
			"symbol": symbol,
			"quantity": parsed_quantity,
			"price": price,
			"cost": cost,
		}
	)


@app.route("/sell", methods=["POST"])
def sell():
	data = request.get_json(silent=True)
	if not isinstance(data, dict):
		return jsonify({"error": "symbol, quantity and datetime are required"}), 400

	symbol = data.get("symbol")
	quantity = data.get("quantity")
	dt = data.get("datetime")
	if not isinstance(symbol, str) or not symbol.strip() or not isinstance(dt, str) or not dt:
		return jsonify({"error": "symbol, quantity and datetime are required"}), 400

	if isinstance(quantity, bool):
		return jsonify({"error": "quantity must be a positive whole number"}), 400
	try:
		parsed_quantity = int(quantity)
	except (TypeError, ValueError):
		return jsonify({"error": "quantity must be a positive whole number"}), 400
	if parsed_quantity <= 0 or (isinstance(quantity, float) and quantity != parsed_quantity):
		return jsonify({"error": "quantity must be a positive whole number"}), 400

	holding = db.execute(
		"SELECT quantity, avg_price FROM portfolio WHERE symbol = ?", (symbol,)
	).fetchone()
	if not holding or holding["quantity"] < parsed_quantity:
		return jsonify({"error": "Not enough shares to sell"}), 400

	price_row = db.execute(
		"""
		SELECT price FROM prices
		WHERE symbol = ? AND datetime <= ?
		ORDER BY datetime DESC
		LIMIT 1
		""",
		(symbol, dt),
	).fetchone()
	if not price_row:
		return jsonify({"error": "No price found for that symbol/time"}), 404

	price = price_row["price"]
	proceeds = price * parsed_quantity
	db.execute("UPDATE account SET balance = balance + ? WHERE id = 1", (proceeds,))

	remaining_quantity = holding["quantity"] - parsed_quantity
	if remaining_quantity == 0:
		db.execute("DELETE FROM portfolio WHERE symbol = ?", (symbol,))
	else:
		db.execute(
			"UPDATE portfolio SET quantity = ? WHERE symbol = ?",
			(remaining_quantity, symbol),
		)

	db.execute(
		"""
		INSERT INTO transactions (symbol, action, quantity, price, trade_time)
		VALUES (?, 'SELL', ?, ?, ?)
		""",
		(symbol, parsed_quantity, price, dt),
	)
	db.commit()

	realized_pnl = (price - holding["avg_price"]) * parsed_quantity
	return jsonify(
		{
			"message": "Sell successful",
			"symbol": symbol,
			"quantity": parsed_quantity,
			"price": price,
			"proceeds": proceeds,
			"realized_pnl": round(realized_pnl, 2),
		}
	)


@app.route("/portfolio")
def portfolio():
	holdings = db.execute(
		"SELECT symbol, quantity, avg_price FROM portfolio ORDER BY symbol"
	).fetchall()
	account = db.execute("SELECT balance FROM account WHERE id = 1").fetchone()

	result = []
	total_current_value = 0
	total_invested = 0
	for holding in holdings:
		latest = db.execute(
			"""
			SELECT price FROM prices
			WHERE symbol = ?
			ORDER BY datetime DESC
			LIMIT 1
			""",
			(holding["symbol"],),
		).fetchone()

		current_price = latest["price"] if latest else holding["avg_price"]
		current_value = current_price * holding["quantity"]
		invested_value = holding["avg_price"] * holding["quantity"]
		unrealized_pnl = current_value - invested_value
		total_current_value += current_value
		total_invested += invested_value
		result.append(
			{
				"symbol": holding["symbol"],
				"quantity": holding["quantity"],
				"avg_price": round(holding["avg_price"], 2),
				"current_price": round(current_price, 2),
				"invested_value": round(invested_value, 2),
				"current_value": round(current_value, 2),
				"unrealized_pnl": round(unrealized_pnl, 2),
			}
		)

	return jsonify(
		{
			"balance": round(account["balance"], 2),
			"holdings": result,
			"total_invested": round(total_invested, 2),
			"total_current_value": round(total_current_value, 2),
			"total_unrealized_pnl": round(total_current_value - total_invested, 2),
		}
	)


@app.route("/transactions")
def transactions():
	rows = db.execute(
		"""
		SELECT id, symbol, action, quantity, price, trade_time, created_at
		FROM transactions
		ORDER BY created_at DESC, id DESC
		"""
	).fetchall()

	return jsonify(
		[
			{
				"symbol": row["symbol"],
				"action": row["action"],
				"quantity": row["quantity"],
				"price": row["price"],
				"trade_time": row["trade_time"],
				"created_at": row["created_at"],
			}
			for row in rows
		]
	)


if __name__ == "__main__":
	app.run(debug=True)
