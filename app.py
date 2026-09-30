from flask import Flask, render_template, request, redirect, url_for, session
import gspread
import os

app = Flask(__name__)
app.secret_key = "super_secret_key"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_PATH = os.path.join(BASE_DIR, 'credentials.json')

gc = gspread.service_account(filename=CREDENTIALS_PATH)
# เปิดสเปรดชีตชื่อ Income_Expense_Tracker
spreadsheet = gc.open("Income_Expense_Tracker")

# เลือกแผ่นงาน (Worksheet) สำหรับ users และ expenses
user_sheet = spreadsheet.worksheet("users")
expense_sheet = spreadsheet.worksheet("expenses")


@app.route("/")
def index():
    if "username" not in session:
        return redirect(url_for("login"))

    user_transactions = []
    total_income = 0.0
    total_expense = 0.0

    rows = expense_sheet.get_all_records()
    for row in rows:
        if str(row.get("username")) == session["username"]:
            row["amount"] = float(row["amount"])
            user_transactions.append(row)
            if row["type"] == "income":
                total_income += row["amount"]
            else:
                total_expense += row["amount"]

    balance = total_income - total_expense

    return render_template(
        "index.html",
        username=session["username"],
        transactions=user_transactions,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        action = request.form.get("action")
        username = request.form.get("username").strip()
        password = request.form.get("password").strip()

        if action == "register":
            user_sheet.append_row([username, password])
            return render_template("login.html", msg="Register success! Please login.")

        elif action == "login":
            users = user_sheet.get_all_records()
            for row in users:
                if str(row.get("username")) == username and str(row.get("password")) == password:
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

    expense_sheet.append_row([session["username"], item_name, t_type, amount, item_date])

    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
