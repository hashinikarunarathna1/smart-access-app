import streamlit as st
import pandas as pd
import sqlite3
import urllib.parse
from datetime import datetime

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="Smart Class Pro", page_icon="🎓", layout="wide")

st.markdown("""
    <style>
    [data-testid="stMetric"] {
        background-color: rgba(28, 131, 225, 0.1) !important;
        padding: 20px !important; border-radius: 12px !important;
        border: 1px solid rgba(28, 131, 225, 0.2);
    }
    .stButton>button {
        width: 100%; border-radius: 8px; height: 3.5em;
        background-color: #1a73e8; color: white !important;
        font-weight: bold; border: none;
    }
    .receipt-container {
        border: 2px solid #1a73e8; border-radius: 20px;
        padding: 30px; margin: 20px auto; max-width: 600px;
        font-family: 'Courier New', Courier, monospace;
        background-color: rgba(0, 0, 0, 0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE SETUP ---
def get_connection():
    return sqlite3.connect("smart_class_v10.db", check_same_thread=False)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, school TEXT, grade TEXT, whatsapp TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY AUTOINCREMENT, student_name TEXT, grade TEXT, month TEXT, amount REAL, date TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, description TEXT, amount REAL, date TEXT, target_month TEXT)')
    
    # පරණ ඩේටාබේස් එකට target_month එකතු වී නැත්නම් එය එකතු කිරීම (Migration)
    try:
        cursor.execute("SELECT target_month FROM expenses LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute('ALTER TABLE expenses ADD COLUMN target_month TEXT')
        conn.commit()
    conn.close()

init_db()

# --- 3. APP LOGIC ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.markdown("<h2 style='text-align: center; color: #1a73e8;'>🔐 Admin Login</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        user = st.text_input("Username")
        pw = st.text_input("Password", type="password")
        if st.button("Login"):
            if user == "admin" and pw == "1234":
                st.session_state['logged_in'] = True
                st.rerun()
            else:
                st.error("Invalid Credentials")
else:
    st.sidebar.title("💎 Smart Class Pro")
    choice = st.sidebar.radio("Main Menu", ["🚀 Dashboard", "📝 Registration", "💰 Payments", "💸 Cash Out", "📊 Reports"])
    
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

    conn = get_connection()
    months_list = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

    # --- DASHBOARD ---
    if choice == "🚀 Dashboard":
        st.title("System Overview")
        all_pay = pd.read_sql("SELECT amount FROM payments", conn)
        all_exp = pd.read_sql("SELECT amount FROM expenses", conn)
        
        income = all_pay['amount'].sum() if not all_pay.empty else 0
        expense = all_exp['amount'].sum() if not all_exp.empty else 0
        net = income - expense
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Income", f"Rs. {income:,.2f}")
        m2.metric("Total Cash Out", f"Rs. {expense:,.2f}")
        m3.metric("Net Balance", f"Rs. {max(0, net):,.2f}")
        
        st.divider()
        st.subheader("Monthly Revenue (Student Payments)")
        if not all_pay.empty:
            st.table(pd.read_sql("SELECT month, SUM(amount) as Total FROM payments GROUP BY month", conn))

    # --- CASH OUT (Targeted) ---
    elif choice == "💸 Cash Out":
        st.title("💸 Targeted Cash Out")
        col1, col2 = st.columns(2)
        with col1:
            t_month = st.selectbox("Select Month to Withdraw from", months_list)
            m_income = pd.read_sql(f"SELECT SUM(amount) as total FROM payments WHERE month='{t_month}'", conn).iloc[0,0] or 0.0
            st.info(f"Available for {t_month}: **Rs. {m_income:,.2f}**")
        
        with col2:
            with st.form("co_form", clear_on_submit=True):
                desc = st.text_input("Reason")
                amt = st.number_input("Amount", min_value=0.0)
                if st.form_submit_button("Confirm"):
                    if amt > m_income:
                        st.error("වැඩියෙන් මුදල් ගන්න බැහැ!")
                    elif desc and amt > 0:
                        conn.execute("INSERT INTO expenses (description, amount, date, target_month) VALUES (?,?,?,?)", 
                                     (desc, amt, datetime.now().strftime("%Y-%m-%d %H:%M"), t_month))
                        conn.commit()
                        st.success("Cash Out Success!")
                        st.rerun()
        
        st.subheader("History")
        st.dataframe(pd.read_sql("SELECT * FROM expenses ORDER BY id DESC", conn), use_container_width=True)

    # (Registration, Payments, Reports කොටස් ද මේ ආකාරයටම පවතී)
    elif choice == "📝 Registration":
        with st.form("reg"):
            n = st.text_input("Name"); s = st.text_input("School")
            g = st.selectbox("Grade", ["Grade 6", "Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Revision", "Theory"])
            w = st.text_input("WhatsApp")
            if st.form_submit_button("Save"):
                conn.execute("INSERT INTO students (name, school, grade, whatsapp) VALUES (?,?,?,?)", (n,s,g,w))
                conn.commit(); st.success("Saved!")

    elif choice == "💰 Payments":
        search = st.text_input("Search Name")
        if search:
            res = pd.read_sql(f"SELECT * FROM students WHERE name LIKE '%{search}%'", conn)
            if not res.empty:
                s_name = st.selectbox("Confirm Student", res['name'].tolist())
                month = st.selectbox("Month", months_list)
                amt = st.number_input("Amount", value=1500.0)
                if st.button("Pay"):
                    conn.execute("INSERT INTO payments (student_name, grade, month, amount, date) VALUES (?,?,?,?,?)", 
                                 (s_name, res[res['name']==s_name]['grade'].values[0], month, amt, datetime.now().strftime("%Y-%m-%d")))
                    conn.commit(); st.success("Paid!")

    elif choice == "📊 Reports":
        t1, t2, t3, t4 = st.tabs(["Students", "Payments", "Arrears", "Delete"])
        with t1: st.dataframe(pd.read_sql("SELECT * FROM students", conn), use_container_width=True)
        with t2: st.dataframe(pd.read_sql("SELECT * FROM payments", conn), use_container_width=True)
        with t3:
            cm = st.selectbox("Month", months_list); cg = st.selectbox("Grade", ["Grade 6", "Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Revision", "Theory"])
            if st.button("Check"):
                all_s = pd.read_sql(f"SELECT name FROM students WHERE grade='{cg}'", conn)
                paid_s = pd.read_sql(f"SELECT student_name FROM payments WHERE month='{cm}' AND grade='{cg}'", conn)
                st.table(all_s[~all_s['name'].isin(paid_s['student_name'].tolist())])
        with t4:
            dt = st.radio("Type", ["Payments", "Students", "Expenses"])
            di = st.number_input("ID", min_value=1)
            if st.button("Delete"):
                conn.execute(f"DELETE FROM {dt.lower()} WHERE id={di}"); conn.commit(); st.rerun()
