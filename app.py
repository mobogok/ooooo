import os
import json
import gspread
from flask import Flask, render_template, request, redirect, url_for, session
from google.oauth2.service_account import Credentials

app = Flask(__name__)
app.secret_key = 'income_tracker_super_secret_key_123'

SHEET_NAME = "Income_Expense_Tracker"

def get_sheets():
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    creds_json = os.environ.get('GOOGLE_CREDENTIALS')
    
    if creds_json:
        info = json.loads(creds_json)
        creds = Credentials.from_service_account_info(info, scopes=scopes)
    else:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        CREDENTIALS_PATH = os.path.join(BASE_DIR, 'credentials.json')
        creds = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=scopes)
        
    gc = gspread.authorize(creds)
    sh = gc.open(SHEET_NAME)
    
    # ดึง Sheet1 สำหรับเก็บ Transactions
    tx_sheet = sh.sheet1
    
    # ตรวจสอบว่ามี Sheet2 สำหรับเก็บ Users หรือยัง ถ้ายังไม่มีให้สร้างขึ้นมา
    try:
        user_sheet = sh.worksheet("Users")
    except Exception:
        user_sheet = sh.add_worksheet(title="Users", rows="100", cols="2")
        user_sheet.append_row(["Username", "Password"])
        
    return tx_sheet, user_sheet


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        try:
            _, user_sheet = get_sheets()
            users_data = user_sheet.get_all_values()
            
            # ตรวจสอบ Username และ Password จาก Google Sheet
            user_found = False
            if len(users_data) > 1:
                for row in users_data[1:]:
                    if len(row) >= 2 and row[0] == username and row[1] == password:
                        user_found = True
                        break
            
            if user_found:
                session['user'] = username
                return redirect(url_for('index'))
            else:
                error = "Invalid Username or Password!"
        except Exception as e:
            error = f"Database error: {e}"

    return render_template('login.html', error=error)


@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            error = "Please fill out all fields!"
        else:
            try:
                _, user_sheet = get_sheets()
                users_data = user_sheet.get_all_values()
                
                # เช็กว่ามีชื่อผู้ใช้นี้อยู่แล้วหรือยัง
                existing_users = [row[0] for row in users_data[1:] if len(row) > 0]
                
                if username in existing_users:
                    error = "Username already exists! Please choose another."
                else:
                    # บันทึก User ใหม่ลง Google Sheet
                    user_sheet.append_row([username, password])
                    session['user'] = username
                    return redirect(url_for('index'))
            except Exception as e:
                error = f"Registration error: {e}"

    return render_template('register.html', error=error)


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))


@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))

    current_user = session['user']

    try:
        tx_sheet, _ = get_sheets()
        data = tx_sheet.get_all_values()
        
        if data and len(data) > 0:
            headers = data[0]
            all_transactions = data[1:]
            user_transactions = [tx for tx in all_transactions if len(tx) >= 5 and tx[4] == current_user]
        else:
            headers = ['Date', 'Type', 'Category', 'Amount', 'User']
            user_transactions = []
            
    except Exception as e:
        print(f"Error fetching data: {e}")
        headers = ['Date', 'Type', 'Category', 'Amount', 'User']
        user_transactions = []
        
    return render_template('index.html', headers=headers, transactions=user_transactions, current_user=current_user)


@app.route('/add', methods=['POST'])
def add_transaction():
    if 'user' not in session:
        return redirect(url_for('login'))

    date = request.form.get('date', '')
    tx_type = request.form.get('type', '')
    category = request.form.get('category', '')
    amount = request.form.get('amount', '')
    user = session['user']

    try:
        tx_sheet, _ = get_sheets()
        tx_sheet.append_row([date, tx_type, category, amount, user])
    except Exception as e:
        print(f"Error saving data: {e}")

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
