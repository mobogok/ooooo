import os
import json
import gspread
from flask import Flask, render_template, request, redirect, url_for
from google.oauth2.service_account import Credentials

app = Flask(__name__)

SHEET_NAME = "Income_Expense_Tracker"

def get_sheet():
    """ดึง credentials จาก Environment Variable หรือไฟล์ local"""
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    # 1. เช็กว่ามีรหัสใน Environment Variable บน Render ไหม
    creds_json = os.environ.get('GOOGLE_CREDENTIALS')
    
    if creds_json:
        # โหลดรหัสจาก Environment Variable
        info = json.loads(creds_json)
        creds = Credentials.from_service_account_info(info, scopes=scopes)
    else:
        # ถ้าไม่มี ให้ไปอ่านไฟล์ credentials.json ในเครื่อง (สำหรับรัน local)
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        CREDENTIALS_PATH = os.path.join(BASE_DIR, 'credentials.json')
        creds = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=scopes)
        
    gc = gspread.authorize(creds)
    return gc.open(SHEET_NAME).sheet1


@app.route('/')
def index():
    try:
        sheet = get_sheet()
        data = sheet.get_all_values()
        
        if data and len(data) > 0:
            headers = data[0]
            transactions = data[1:]
        else:
            headers = ['Date', 'Type', 'Category', 'Amount', 'User']
            transactions = []
            
    except Exception as e:
        print(f"Error fetching data: {e}")
        headers = ['Date', 'Type', 'Category', 'Amount', 'User']
        transactions = []
        
    return render_template('index.html', headers=headers, transactions=transactions)


@app.route('/add', methods=['POST'])
def add_transaction():
    date = request.form.get('date', '')
    tx_type = request.form.get('type', '')
    category = request.form.get('category', '')
    amount = request.form.get('amount', '')
    user = request.form.get('user', '')

    try:
        sheet = get_sheet()
        sheet.append_row([date, tx_type, category, amount, user])
    except Exception as e:
        print(f"Error saving data: {e}")

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
