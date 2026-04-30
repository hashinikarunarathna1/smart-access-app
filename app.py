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
    [data-testid="stMetricLabel"] { color: #1e293b !important; font-weight: bold !important; }
    [data-testid="stMetricValue"] { color: #1a73e8 !important; }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3.5em;
        background-color: #1a73e8;
        color: white;
        font-weight: bold;
        border: none;
    }
    </style>
    """, unsafe_allow_html=True)

# --- DATABASE ENGINE ---
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
                st.error("Invalid Login")
else:
    st.sidebar.title("💎 Smart Class Pro")
    choice = st.sidebar.radio("Main Menu", ["🚀 Dashboard", "📝 Registration", "💰 Payments", "📊 Reports"])
    
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

    conn = get_connection()

    # --- DASHBOARD ---
    if choice == "🚀 Dashboard":
        st.markdown("<h1 style='color: #1a73e8;'>Overview</h1>", unsafe_allow_html=True)
        total_students = pd.read_sql("SELECT COUNT(*) FROM students", conn).iloc[0,0]
        total_revenue = pd.read_sql("SELECT SUM(amount) FROM payments", conn).iloc[0,0] or 0
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Students", total_students)
        m2.metric("Total Revenue", f"Rs. {total_revenue:,.2f}")
        m3.metric("Status", "Active")

    # --- REGISTRATION ---
    elif choice == "📝 Registration":
        st.title("Student Enrollment")
        with st.form("reg_form", clear_on_submit=True):
            name = st.text_input("Full Name")
            school = st.text_input("School")
            grade = st.text_input("Grade")
            wa = st.text_input("WhatsApp (94...)")
            if st.form_submit_button("Confirm Enrollment"):
                if name and wa:
                    conn.execute("INSERT INTO students (name, school, grade, whatsapp) VALUES (?,?,?,?)", (name, school, grade, wa))
                    conn.commit()
                    st.success("Registered!")

    # --- PAYMENTS ---
    elif choice == "💰 Payments":
        st.title("Payment Gateway")
        search_name = st.text_input("Search Student Name")
        if search_name:
            results = pd.read_sql(f"SELECT * FROM students WHERE name LIKE '%{search_name}%'", conn)
            if not results.empty:
                student = results.iloc[0]
                st.success(f"Selected: {student['name']}")
                month = st.selectbox("Month", ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"])
                amount = st.number_input("Amount", min_value=0.0)
                if st.button("Save & Send Receipt"):
                    today = datetime.now().strftime("%Y-%m-%d")
                    conn.execute("INSERT INTO payments (student_name, grade, month, amount, date) VALUES (?,?,?,?,?)", (student['name'], student['grade'], month, amount, today))
                    conn.commit()
                    msg = urllib.parse.quote(f"🎓 *SMART CLASS*\nReceipt: {student['name']}\nMonth: {month}\nAmount: Rs.{amount}")
                    st.markdown(f'<a href="https://wa.me/{student['whatsapp']}?text={msg}" target="_blank" style="text-decoration:none;"><div style="background-color:#25d366;color:white;padding:10px;text-align:center;border-radius:5px;">Send WhatsApp Receipt</div></a>', unsafe_allow_html=True)

    # --- REPORTS & DELETE OPTION ---
    elif choice == "📊 Reports":
        st.title("Data Management")
        t1, t2 = st.tabs(["Student List", "Payment Records"])
        
        with t1:
            df_std = pd.read_sql("SELECT * FROM students", conn)
            st.dataframe(df_std, use_container_width=True)
            st.divider()
            st.subheader("🗑️ Delete Student")
            delete_std_id = st.number_input("Enter Student ID to delete", min_value=1, step=1)
            if st.button("Delete Student", type="secondary"):
                conn.execute(f"DELETE FROM students WHERE id={delete_std_id}")
                conn.commit()
                st.warning(f"Student ID {delete_std_id} deleted!")
                st.rerun()
                
        with t2:
            df_pay = pd.read_sql("SELECT * FROM payments", conn)
            st.dataframe(df_pay, use_container_width=True)
            st.divider()
            st.subheader("🗑️ Delete Payment Record")
            delete_pay_id = st.number_input("Enter Payment ID to delete", min_value=1, step=1)
            if st.button("Delete Record", type="secondary"):
                conn.execute(f"DELETE FROM payments WHERE id={delete_pay_id}")
                conn.commit()
                st.warning(f"Payment ID {delete_pay_id} deleted!")
                st.rerun()
