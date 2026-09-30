import os
import json
import gspread
from flask import Flask, render_template, request, redirect, url_for, session
from google.oauth2.service_account import Credentials

app = Flask(__name__)
app.secret_key = 'income_tracker_super_secret_key'  # สำหรับจัดการ Session การเข้าสู่ระบบ

SHEET_NAME = "Income_Expense_Tracker"

# ==========================================
# รายชื่อผู้ใช้งานและ รหัสผ่าน (สามารถเพิ่ม/แก้ไขได้ที่นี่)
# ==========================================
USERS = {
    "Alex": "alex123",
    "John": "john123",
    "Sarah": "sarah123"
}

def get_sheet():
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
    return gc.open(SHEET_NAME).sheet1


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if username in USERS and USERS[username] == password:
            session['user'] = username
            return redirect(url_for('index'))
        else:
            error = "Invalid Username or Password!"

    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))


@app.route('/')
def index():
    # ถ้ายังไม่ได้ Login ให้เด้งไปหน้า Login ก่อน
    if 'user' not in session:
        return redirect(url_for('login'))

    current_user = session['user']

    try:
        sheet = get_sheet()
        data = sheet.get_all_values()
        
        if data and len(data) > 0:
            headers = data[0]
            all_transactions = data[1:]
            # กรองแสดงเฉพาะรายการที่เป็นของ User ที่กำลัง Login อยู่เท่านั้น
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
    user = session['user']  # ดึงชื่อจาก Session อัตโนมัติ

    try:
        sheet = get_sheet()
        sheet.append_row([date, tx_type, category, amount, user])
    except Exception as e:
        print(f"Error saving data: {e}")

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
