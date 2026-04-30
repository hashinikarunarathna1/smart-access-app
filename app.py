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
        width: 100%; border-radius: 8px; height: 3.5em;
        background-color: #1a73e8; color: white; font-weight: bold; border: none;
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
    st.sidebar.title("💎 Smart Class Pro")
    choice = st.sidebar.radio("Main Menu", ["🚀 Dashboard", "📝 Registration", "💰 Payments", "📊 Reports"])
    
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

    conn = get_connection()

    # --- DASHBOARD (NEW REVENUE UPDATES) ---
    if choice == "🚀 Dashboard":
        st.markdown("<h1 style='color: #1a73e8;'>Overview</h1>", unsafe_allow_html=True)
        
        # දත්ත ලබා ගැනීම
        total_students = pd.read_sql("SELECT COUNT(*) FROM students", conn).iloc[0,0]
        all_payments_df = pd.read_sql("SELECT * FROM payments", conn)
        
        # වත්මන් මාසය ලබා ගැනීම (උදා: April)
        current_month_name = datetime.now().strftime("%B")
        
        # ගණනය කිරීම්
        overall_total = all_payments_df['amount'].sum() if not all_payments_df.empty else 0
        current_month_total = all_payments_df[all_payments_df['month'] == current_month_name]['amount'].sum() if not all_payments_df.empty else 0
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Students", total_students)
        m2.metric(f"Revenue ({current_month_name})", f"Rs. {current_month_total:,.2f}")
        m3.metric("Total Revenue (All)", f"Rs. {overall_total:,.2f}")
        m4.metric("Status", "Active")
        
        st.markdown("---")
        
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            st.subheader("📅 Monthly Revenue Breakdown")
            if not all_payments_df.empty:
                # මාසය අනුව Group කිරීම
                monthly_summary = all_payments_df.groupby('month')['amount'].sum().reset_index()
                st.table(monthly_summary)
            else:
                st.info("No payment data available yet.")
        
        with col_right:
            st.subheader("Quick Actions")
            if st.button("New Registration"):
                st.info("Use Sidebar -> Registration")
            if st.button("Add Payment"):
                st.info("Use Sidebar -> Payments")

    # --- REGISTRATION ---
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

    # --- PAYMENTS ---
    elif choice == "💰 Payments":
        st.title("Payment Gateway")
        search_name = st.text_input("Search Student Name")
        if search_name:
            results = pd.read_sql(f"SELECT * FROM students WHERE name LIKE '%{search_name}%'", conn)
            if not results.empty:
                student = results.iloc[0]
                st.info(f"Student: {student['name']} | Grade: {student['grade']}")
                month = st.selectbox("Month", ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"])
                amount = st.number_input("Amount", min_value=0.0)
                if st.button("Save & Send Receipt"):
                    today = datetime.now().strftime("%Y-%m-%d")
                    conn.execute("INSERT INTO payments (student_name, grade, month, amount, date) VALUES (?,?,?,?,?)", (student['name'], student['grade'], month, amount, today))
                    conn.commit()
                    st.success("Payment Saved!")
                    msg = urllib.parse.quote(f"🎓 *SMART CLASS*\nReceipt for {student['name']}\nGrade: {student['grade']}\nMonth: {month}\nAmount: Rs.{amount}")
                    st.markdown(f'<a href="https://wa.me/{student['whatsapp']}?text={msg}" target="_blank" style="text-decoration:none;"><div style="background-color:#25d366;color:white;padding:10px;text-align:center;border-radius:5px;">Send WhatsApp Receipt</div></a>', unsafe_allow_html=True)

    # --- REPORTS ---
    elif choice == "📊 Reports":
        st.title("Reports Management")
        t1, t2, t3 = st.tabs(["Student List", "Payment Records", "🗑️ Delete Records"])
        
        with t1:
            df_std = pd.read_sql("SELECT * FROM students", conn)
            if not df_std.empty:
                unique_grades = df_std['grade'].unique()
                for g in unique_grades:
                    with st.expander(f"📂 {g} - Students", expanded=False):
                        st.table(df_std[df_std['grade'] == g][['id', 'name', 'school', 'whatsapp']])
                
        with t2:
            df_pay = pd.read_sql("SELECT * FROM payments", conn)
            if not df_pay.empty:
                unique_grades_pay = df_pay['grade'].unique()
                for g in unique_grades_pay:
                    with st.expander(f"💰 {g} - Payment Records", expanded=False):
                        st.table(df_pay[df_pay['grade'] == g][['id', 'student_name', 'month', 'amount', 'date']])

        with t3:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Delete Student")
                sid = st.number_input("Student ID", min_value=1, step=1, key="del_std")
                if st.button("Delete Student", type="primary"):
                    conn.execute(f"DELETE FROM students WHERE id={sid}")
                    conn.commit()
                    st.rerun()
            with col2:
                st.subheader("Delete Payment")
                pid = st.number_input("Payment ID", min_value=1, step=1, key="del_pay")
                if st.button("Delete Record", type="primary"):
                    conn.execute(f"DELETE FROM payments WHERE id={pid}")
                    conn.commit()
                    st.rerun()
