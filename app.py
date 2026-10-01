from flask import Flask, render_template, request, redirect, url_for, session
import csv
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "super_secret_key"

USER_FILE = "users.csv"
DATA_FILE = "expenses.csv"

if not os.path.exists(USER_FILE):
    with open(USER_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["username", "password"])

@app.route("/")
def index():
    if "username" not in session:
        return redirect(url_for("login"))

    search_date = request.args.get("search_date", "").strip()

    formatted_search_date = None
    if search_date:
        try:
            formatted_search_date = datetime.strptime(search_date, "%Y-%m-%d").date()
        except ValueError:
            pass

    user_transactions = []
    total_income = 0.0
    total_expense = 0.0

    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, mode='r', encoding='utf-8') as file:
            reader = list(csv.DictReader(file))
            for idx, row in enumerate(reader):
                if row.get("username") == session["username"]:
                    row["amount"] = float(row["amount"])
                    row["original_index"] = idx
                    
                    if row["type"] == "income":
                        total_income += row["amount"]
                    else:
                        total_expense += row["amount"]

                    if formatted_search_date:
                        raw_date_str = row.get("date", "").strip()
                        row_date_obj = None

                        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"):
                            try:
                                row_date_obj = datetime.strptime(raw_date_str, fmt).date()
                                break
                            except ValueError:
                                continue

                        if row_date_obj and row_date_obj == formatted_search_date:
                            user_transactions.append(row)
                    else:
                        user_transactions.append(row)

    balance = total_income - total_expense

    return render_template(
        "index.html",
        username=session["username"],
        transactions=user_transactions,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        search_date=search_date
    )

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        action = request.form.get("action")
        username = request.form.get("username").strip()
        password = request.form.get("password").strip()

        if action == "register":
            with open(USER_FILE, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow([username, password])
            return render_template("login.html", msg="Register success! Please login.")

        elif action == "login":
            with open(USER_FILE, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row["username"] == username and row["password"] == password:
                        session["username"] = username
                        return redirect(url_for("index"))
            return render_template("login.html", msg="Wrong Username or Password!")

    return render_template("login.html")

@app.route("/add", methods=["POST"])
def add_transaction():
    if "username" not in session:
        return redirect(url_for("login"))

    item_name = request.form.get("name")
    category = request.form.get("category")
    amount = float(request.form.get("amount"))
    item_date = request.form.get("date")

    t_type = "income" if category == "1" else "expense"

    data = {
        "username": session["username"],
        "name": item_name,
        "type": t_type,
        "amount": amount,
        "date": item_date
    }

    return redirect(url_for("index"))
    if 0 <= index < len(rows) and rows[index].get("username") == session["username"]:
            rows.pop(index)

            with open(DATA_FILE, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=["username", "name", "type", "amount", "date"])
                writer.writeheader()
                writer.writerows(rows)

    return render_template("delete.html")

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
