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
    .receipt-container {
        background-color: #f8faff; border: 2px solid #1a73e8; border-radius: 20px;
        padding: 40px; margin: 20px 0; max-width: 800px; margin-left: auto; margin-right: auto;
        font-family: 'Courier New', Courier, monospace;
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

    # --- DASHBOARD ---
    if choice == "🚀 Dashboard":
        st.markdown("<h1 style='color: #1a73e8;'>Overview</h1>", unsafe_allow_html=True)
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
                st.info(f"Selected: {student['name']} ({student['grade']})")
                month = st.selectbox("Month", ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"])
                amount = st.number_input("Amount (Rs.)", min_value=0.0)
                if st.button("Generate & Save Payment"):
                    today = datetime.now().strftime("%Y-%m-%d")
                    conn.execute("INSERT INTO payments (student_name, grade, month, amount, date) VALUES (?,?,?,?,?)", (student['name'], student['grade'], month, amount, today))
                    conn.commit()
                    st.success("Payment Saved!")

    # --- REPORTS & ARREARS LIST ---
    elif choice == "📊 Reports":
        st.title("Reports Management")
        t1, t2, t3, t4 = st.tabs(["Student List", "Payment Records", "🚨 Pending Payments", "🗑️ Delete Records"])
        
        with t1:
            df_std = pd.read_sql("SELECT * FROM students", conn)
            if not df_std.empty:
                for g in df_std['grade'].unique():
                    with st.expander(f"📂 {g} - Students", expanded=False):
                        st.table(df_std[df_std['grade'] == g][['id', 'name', 'school', 'whatsapp']])
        
        with t2:
            df_pay = pd.read_sql("SELECT * FROM payments", conn)
            if not df_pay.empty:
                for g in df_pay['grade'].unique():
                    with st.expander(f"💰 {g} - Payment Records", expanded=False):
                        st.table(df_pay[df_pay['grade'] == g][['id', 'student_name', 'month', 'amount', 'date']])

        # --- ARREARS LOGIC ---
        with t3:
            st.subheader("Students who haven't paid for a specific month")
            target_month = st.selectbox("Select Month to check Arrears", ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"])
            
            df_all_std = pd.read_sql("SELECT name, grade, whatsapp FROM students", conn)
            df_paid_std = pd.read_sql(f"SELECT student_name FROM payments WHERE month = '{target_month}'", conn)
            
            if not df_all_std.empty:
                # ගෙවපු අයගේ නම් ලැයිස්තුවක් සාදා ගැනීම
                paid_list = df_paid_std['student_name'].tolist()
                # මුළු ශිෂ්‍ය ලැයිස්තුවෙන් ගෙවපු අය අයින් කිරීම
                arrears_df = df_all_std[~df_all_std['name'].isin(paid_list)]
                
                if not arrears_df.empty:
                    st.warning(f"Found {len(arrears_df)} students who haven't paid for {target_month}")
                    st.dataframe(arrears_df, use_container_width=True)
                    
                    # WhatsApp Reminder එකක් යැවීමට
                    st.info("ඔබට අවශ්‍ය නම් පහත ශිෂ්‍යයන්ට Reminder එකක් යැවිය හැක.")
                else:
                    st.success(f"Everyone has paid for {target_month}!")
            else:
                st.info("No students registered.")

        with t4:
            col1, col2 = st.columns(2)
            with col1:
                sid = st.number_input("Student ID", min_value=1, step=1, key="del_std")
                if st.button("Delete Student"):
                    conn.execute(f"DELETE FROM students WHERE id={sid}")
                    conn.commit()
                    st.rerun()
            with col2:
                pid = st.number_input("Payment ID", min_value=1, step=1, key="del_pay")
                if st.button("Delete Record"):
                    conn.execute(f"DELETE FROM payments WHERE id={pid}")
                    conn.commit()
                    st.rerun()
