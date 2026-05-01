import streamlit as st
import pandas as pd
import sqlite3
import urllib.parse
from datetime import datetime

# --- CONFIG & STYLING ---
st.set_page_config(page_title="Smart Class Management", page_icon="🎓", layout="wide")

st.markdown("""
    <style>
    [data-testid="stMetric"] {
        background-color: #ffffff !important;
        padding: 20px !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
    }
    .stButton>button {
        width: 100%; border-radius: 8px; height: 3.5em;
        background-color: #1a73e8; color: white; font-weight: bold; border: none;
    }
    .receipt-container {
        background-color: #f8faff; border: 2px solid #1a73e8; border-radius: 20px;
        padding: 40px; margin: 20px auto; max-width: 800px;
        font-family: 'Courier New', Courier, monospace;
    }
    .receipt-title { color: #1a73e8; font-size: 32px; font-weight: bold; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- DATABASE ---
def get_connection():
    return sqlite3.connect("smart_class_v10.db", check_same_thread=False)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, school TEXT, grade TEXT, whatsapp TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY AUTOINCREMENT, student_name TEXT, grade TEXT, month TEXT, amount REAL, date TEXT)')
    conn.commit()

init_db()

# --- LOGIN ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.markdown("<h2 style='text-align: center; color: #1a73e8;'>🔐 Smart Class Admin Login</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        user = st.text_input("Username")
        pw = st.text_input("Password", type="password")
        if st.button("Login"):
            if user == "admin" and pw == "1234":
                st.session_state['logged_in'] = True
                st.rerun()
else:
    st.sidebar.title("💎 Smart Class Pro")
    choice = st.sidebar.radio("Main Menu", ["🚀 Dashboard", "📝 Registration", "💰 Payments", "📊 Reports"])
    
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

    conn = get_connection()

    if choice == "🚀 Dashboard":
        st.title("Overview")
        total_students = pd.read_sql("SELECT COUNT(*) FROM students", conn).iloc[0,0]
        all_payments_df = pd.read_sql("SELECT * FROM payments", conn)
        current_month_name = datetime.now().strftime("%B")
        overall_total = all_payments_df['amount'].sum() if not all_payments_df.empty else 0
        current_month_total = all_payments_df[all_payments_df['month'] == current_month_name]['amount'].sum() if not all_payments_df.empty else 0
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Students", total_students)
        m2.metric(f"Revenue ({current_month_name})", f"Rs. {current_month_total:,.2f}")
        m3.metric("Total Revenue (All)", f"Rs. {overall_total:,.2f}")
        m4.metric("Status", "Active")

    elif choice == "📝 Registration":
        st.title("Student Enrollment")
        with st.form("reg_form", clear_on_submit=True):
            name = st.text_input("Full Name")
            school = st.text_input("School")
            grade = st.selectbox("Grade / Group", ["Grade 6", "Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Revision", "Theory"])
            wa = st.text_input("WhatsApp (94...)")
            if st.form_submit_button("Confirm Enrollment"):
                if name and wa:
                    conn.execute("INSERT INTO students (name, school, grade, whatsapp) VALUES (?,?,?,?)", (name, school, grade, wa))
                    conn.commit()
                    st.success("Registered Successfully!")

    elif choice == "💰 Payments":
        st.title("Payment Gateway")
        search_name = st.text_input("Search Student Name")
        if search_name:
            results = pd.read_sql(f"SELECT * FROM students WHERE name LIKE '%{search_name}%'", conn)
            if not results.empty:
                student = results.iloc[0]
                st.info(f"Selected: {student['name']} ({student['grade']})")
                month = st.selectbox("Month", ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"])
                amount = st.number_input("Amount (Rs.)", min_value=0.0)
                if st.button("Generate & Save Payment"):
                    today = datetime.now().strftime("%Y-%m-%d")
                    conn.execute("INSERT INTO payments (student_name, grade, month, amount, date) VALUES (?,?,?,?,?)", (student['name'], student['grade'], month, amount, today))
                    conn.commit()
                    st.markdown(f'<div class="receipt-container"><div class="receipt-title">🎓 SMART CLASS</div><p style="text-align:center;">Official Receipt<br>Date: {today}<br>Student: {student["name"]}<br>Month: {month}<br>Amount: Rs.{amount:,.2f}</p></div>', unsafe_allow_html=True)
                    whatsapp_msg = f"🎓 *SMART CLASS OFFICIAL RECEIPT*\n\n📅 *Date:* {today}\n👤 *Student:* {student['name']}\n📚 *Grade:* {student['grade']}\n🗓️ *Month:* {month}\n💰 *Paid Amount:* Rs. {amount:,.2f}\n\n✅ Payment Successful."
                    encoded_msg = urllib.parse.quote(whatsapp_msg)
                    st.markdown(f'<a href="https://wa.me/{student["whatsapp"]}?text={encoded_msg}" target="_blank" style="text-decoration:none;"><div style="background-color:#25d366;color:white;padding:15px;text-align:center;border-radius:10px;font-weight:bold;">📲 Send WhatsApp Receipt</div></a>', unsafe_allow_html=True)

    elif choice == "📊 Reports":
        st.title("Reports Management")
        t1, t2, t3, t4 = st.tabs(["Student List", "Payment Records", "🔴 Arrears List", "🗑️ Delete Records"])
        
        with t1:
            df_std = pd.read_sql("SELECT * FROM students", conn)
            if not df_std.empty:
                st.dataframe(df_std)
        
        with t2:
            df_pay = pd.read_sql("SELECT * FROM payments", conn)
            if not df_pay.empty:
                st.dataframe(df_pay)

        with t3:
            st.subheader("Check Unpaid Students")
            c_month = st.selectbox("Select Month", ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"])
            c_grade = st.selectbox("Select Grade", ["Grade 6", "Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Revision", "Theory"])
            if st.button("Show Arrears List"):
                all_st = pd.read_sql(f"SELECT name, whatsapp FROM students WHERE grade='{c_grade}'", conn)
                paid_st = pd.read_sql(f"SELECT student_name FROM payments WHERE month='{c_month}' AND grade='{c_grade}'", conn)
                paid_list = paid_st['student_name'].tolist()
                arrears = all_st[~all_st['name'].isin(paid_list)]
                if not arrears.empty:
                    st.warning(f"{c_month} මාසයේ ගෙවීම් නොකළ සිසුන් {len(arrears)} දෙනෙකි.")
                    st.table(arrears)
                else:
                    st.success("සියලුම සිසුන් ගෙවීම් කර ඇත!")

        with t4:
            st.subheader("Delete Record")
            pid = st.number_input("Record ID", min_value=1, step=1)
            if st.button("Delete Now", type="primary"):
                conn.execute(f"DELETE FROM payments WHERE id={pid}")
                conn.commit()
                st.success("Deleted!")
