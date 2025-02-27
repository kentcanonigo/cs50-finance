import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, jsonify, url_for
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from enum import Enum

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


class TransactionType(Enum):
    BUY = "BUY"
    SELL = "SELL"


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    name = session["username"]
    try:
        rows = holdings = db.execute(
            "SELECT symbol, name, amount FROM holdings WHERE user_id=? AND amount > 0 ORDER BY symbol ASC", session["user_id"])
        if not rows:
            flash("You have no active holdings.")
    except:
        flash("Failed to get user holdings.")
    return render_template("index.html", name=name, holdings=holdings)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        # Checks for symbol
        symbol = request.form.get("symbol").strip()
        if not symbol:
            return apology("empty symbol", 400)

        result = lookup(symbol)
        if not result:
            return apology("invalid symbol", 400)

        # Checks for amount of shares
        shares = request.form.get("shares")
        try:
            shares = int(shares)
            if shares <= 0:
                return apology("must buy at least 1 share", 400)
        except:
            return apology("invalid share amount", 400)

        # Check if user has enough cash
        rows = db.execute("SELECT * FROM users WHERE id=?", session["user_id"])

        if len(rows) != 1:
            return apology("invalid session", 400)

        cash = rows[0]["cash"]
        quote_price = result["price"]

        if cash - (quote_price * shares) < 0:
            return apology("can't afford!", 400)
        else:
            new_cash = cash - (quote_price * shares)

            # Update user's cash
            db.execute("UPDATE users SET cash=? WHERE id=?", new_cash, session["user_id"])

            # Refresh cash for UI
            updated_cash = db.execute("SELECT cash FROM users WHERE id=?",
                                      session["user_id"])[0]["cash"]
            session["cash"] = updated_cash

            try:
                # Update transaction history table
                db.execute("BEGIN TRANSACTION")
                db.execute("INSERT INTO transactions (user_id, symbol, name, shares, price, type) VALUES (?, ?, ?, ?, ?, ?)",
                           session["user_id"], result["symbol"], result["name"], shares, quote_price, TransactionType.BUY.value)
                # Update holdings table (with on conflict in case user already owns some shares of that stock)
                db.execute("INSERT INTO holdings (user_id, symbol, name, amount) VALUES (?, ?, ?, ?) ON CONFLICT(user_id, symbol) DO UPDATE SET amount = amount + excluded.amount",
                           session["user_id"], result["symbol"], result["name"], shares)
                db.execute("COMMIT")
            except:
                # Revert users cash if failed
                db.execute("ROLLBACK")
                db.execute("UPDATE users SET cash=? WHERE id=?", cash, session["user_id"])
                return apology("could not complete transaction", 500)

            flash(f"Bought {shares} shares of {result['name']} for {usd(shares * quote_price)}")
            return redirect(url_for("index"))

    elif request.method == "GET":
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    try:
        transactions = db.execute(
            "SELECT symbol, name, shares, price, type, timestamp FROM transactions WHERE user_id=? ORDER BY id DESC", session["user_id"])
        return render_template("history.html", transactions=transactions)
    except:
        flash("Failed to get user holdings.")
    return render_template("history.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["username"] = rows[0]["username"]
        session["cash"] = rows[0]["cash"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "GET":
        return render_template("quote.html")
    elif request.method == "POST":
        # Look up the symbol using the helper function
        symbol = request.form.get("symbol")

        if not symbol:
            return jsonify({"error": "Please enter a stock symbol"}), 400  # Return JSON error

        result = lookup(symbol)
        # Send an error
        if not result:
            return jsonify({"error": "That company does not exist"}), 400

        # Return stock data as a JSON
        return jsonify({
            "name": result["name"],
            "symbol": result["symbol"],
            "price": usd(result["price"])
        })


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        # Verification in case client bypasses client-side verification
        username = request.form.get("username")
        try:
            username = username.strip()
            if not username:
                return apology("username can't be blank", 400)
        except:
            return apology("must provide valid username", 403)

        password = request.form.get("password")
        if not password:
            return apology("password can't be blank", 400)

        password_verify = request.form.get("confirmation")
        if not password_verify:
            return apology("verify your password", 400)

        if password != password_verify:
            return apology("passwords dont match", 400)

        # Hash the user's password
        hashed_password = generate_password_hash(password, method='scrypt', salt_length=16)

        # Insert into users table after hashing password
        try:
            db.execute("INSERT INTO users (username, hash) VALUES (?, ?)",
                       username, hashed_password)
            return redirect(url_for("login"))
        except Exception as e:
            print(f"Error: {e}")
            return apology("username already exists", 400)

    return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":
        # Checks for symbol
        symbol = request.form.get("symbol").strip()
        if not symbol:
            return apology("empty symbol", 403)

        result = lookup(symbol)
        if not result:
            return apology("invalid symbol", 403)

        # Checks for amount of shares
        shares_to_sell = request.form.get("shares")
        try:
            shares_to_sell = int(shares_to_sell)
            if shares_to_sell <= 0:
                return apology("must sell at least 1 share", 403)
            shares_user_has = db.execute(
                "SELECT amount FROM holdings WHERE user_id=? AND symbol=?", session["user_id"], result["symbol"])
            if not shares_user_has:
                return apology("you don't own that stock", 403)
            shares_user_has = shares_user_has[0]["amount"]
            if shares_to_sell > shares_user_has:
                return apology("insufficient shares to sell", 403)
        except:
            return apology("invalid share amount", 403)

        # Get user
        rows = db.execute("SELECT * FROM users WHERE id=?", session["user_id"])
        if len(rows) != 1:
            return apology("invalid session", 403)
        # Get user's cash
        cash = rows[0]["cash"]
        # Get current price of share to sell
        current_price = result["price"]

        # Resulting cash of user after selling
        new_cash = cash + (current_price * shares_to_sell)

        # Update user's cash
        db.execute("UPDATE users SET cash=? WHERE id=?", new_cash, session["user_id"])

        # Refresh cash for UI
        updated_cash = db.execute("SELECT cash FROM users WHERE id=?",
                                  session["user_id"])[0]["cash"]
        session["cash"] = updated_cash

        try:
            # Update transaction history table
            db.execute("BEGIN TRANSACTION")
            db.execute("INSERT INTO transactions (user_id, symbol, name, shares, price, type) VALUES (?, ?, ?, ?, ?, ?)",
                       session["user_id"], result["symbol"], result["name"], shares_to_sell, current_price, TransactionType.SELL.value)
            # Update holdings table (with on conflict in case user already owns some shares of that stock)
            db.execute("INSERT INTO holdings (user_id, symbol, name, amount) VALUES (?, ?, ?, ?) ON CONFLICT(user_id, symbol) DO UPDATE SET amount = amount - excluded.amount",
                       session["user_id"], result["symbol"], result["name"], shares_to_sell)
            db.execute("COMMIT")
        except Exception as e:
            # Revert users cash if failed
            db.execute("ROLLBACK")
            db.execute("UPDATE users SET cash=? WHERE id=?",
                       cash, session["user_id"])
            print(f"SQL ERROR: {e}")
            return apology("could not complete transaction", 500)

        flash(
            f"Sold {shares_to_sell} shares of {result['name']} for {usd(shares_to_sell * current_price)}.")
        return redirect(url_for("index"))

    elif request.method == "GET":
        return render_template("sell.html")


@app.route("/deposit", methods=["GET", "POST"])
def deposit():
    """Deposit cash"""
    if request.method == "POST":
        cash_to_deposit = request.form.get("cash")
        if not cash_to_deposit:
            return apology("invalid deposit amount", 403)
        try:
            cash_to_deposit = int(cash_to_deposit)
            if cash_to_deposit > 10000.00:
                return apology("over the limit", 403)
        except:
            return apology("deposit is not a number", 403)

        # Get user
        rows = db.execute("SELECT * FROM users WHERE id=?", session["user_id"])
        if len(rows) != 1:
            return apology("invalid session", 403)
        # Get user's cash
        cash = rows[0]["cash"]
        new_cash = cash + cash_to_deposit
        db.execute("UPDATE users SET cash=? WHERE id=?", new_cash, session["user_id"])

        # Refresh cash for UI
        updated_cash = db.execute("SELECT cash FROM users WHERE id=?",
                                  session["user_id"])[0]["cash"]
        session["cash"] = updated_cash
        return redirect(url_for("index"))
    elif request.method == "GET":
        return render_template("deposit.html")
