from flask import Flask, render_template, request, redirect, url_for, session
import csv
import os

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

    username = session["username"]
    user_transactions = []
    total_income = 0.0
    total_expense = 0.0

    # 1. อ่านข้อมูลทั้งหมดเฉพาะของผู้ใช้ปัจจุบัน
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row.get("username") == username:
                    row["amount"] = float(row["amount"])
                    user_transactions.append(row)
                    if row["type"] == "income":
                        total_income += row["amount"]
                    else:
                        total_expense += row["amount"]

    balance = total_income - total_expense

    # 2. รับค่าค้นหาตามวันที่ (GET Parameter)
    search_date = request.args.get("search_date", "").strip()

    # 3. กรองรายการตามวันที่ที่จะส่งไปแสดงผล
    display_transactions = []
    for t in user_transactions:
        if not search_date or t["date"] == search_date:
            display_transactions.append(t)

    return render_template(
        "index.html",
        username=username,
        transactions=display_transactions,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        current_date=search_date
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
            if os.path.exists(USER_FILE):
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

    file_exists = os.path.exists(DATA_FILE)
    with open(DATA_FILE, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["username", "name", "type", "amount", "date"])
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)

    return redirect(url_for("index"))

@app.route("/delete/<int:index>", methods=["POST"])
def delete_transaction(index):
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]
    all_rows = []

    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            all_rows = list(reader)

    user_rows = [row for row in all_rows if row.get("username") == username]

    if 0 <= index < len(user_rows):
        target_item = user_rows[index]
        all_rows.remove(target_item)
        
        with open(DATA_FILE, mode='w', newline='', encoding='utf-8') as file:
            fieldnames = ["username", "name", "type", "amount", "date"]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_rows)

    return redirect(url_for("index"))

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
