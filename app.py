import streamlit as st
import pandas as pd
import sqlite3
import urllib.parse
from datetime import datetime

# --- CONFIG & STYLING ---
st.set_page_config(page_title="Smart Class Management", page_icon="🎓", layout="wide")

st.markdown("""
    <style>
    /* පද්ධතියේ පසුබිම සහ Metrics */
    [data-testid="stMetric"] {
        background-color: #ffffff !important;
        padding: 20px !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
    }
    [data-testid="stMetricLabel"] { color: #1e293b !important; font-weight: bold !important; }
    [data-testid="stMetricValue"] { color: #1a73e8 !important; }

    /* බොත්තම් වල පෙනුම */
    .stButton>button {
        width: 100%; border-radius: 8px; height: 3.5em;
        background-color: #1a73e8; color: white; font-weight: bold; border: none;
    }

    /* Official Receipt Box (පින්තූරයේ ඇති ආකාරයට) */
    .receipt-container {
        background-color: #f8faff;
        border: 2px solid #1a73e8;
        border-radius: 20px;
        padding: 40px;
        margin: 20px 0;
        max-width: 800px;
        margin-left: auto;
        margin-right: auto;
        font-family: 'Courier New', Courier, monospace;
        position: relative;
    }
    .receipt-header {
        text-align: center;
        margin-bottom: 30px;
    }
    .receipt-title {
        color: #1a73e8;
        font-size: 32px;
        font-weight: bold;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
    }
    .receipt-subtitle {
        color: #555;
        font-size: 18px;
    }
    .receipt-detail {
        font-size: 18px;
        margin-bottom: 15px;
        color: #333;
    }
    .receipt-label {
        font-weight: bold;
        min-width: 150px;
        display: inline-block;
    }
    .receipt-footer {
        text-align: center;
        margin-top: 40px;
        font-size: 14px;
        color: #777;
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
        
        st.markdown("---")
        st.subheader("📅 Monthly Revenue Breakdown")
        if not all_payments_df.empty:
            monthly_summary = all_payments_df.groupby('month')['amount'].sum().reset_index()
            st.table(monthly_summary)

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

    # --- PAYMENTS (OFFICIAL RECEIPT UPDATED) ---
    elif choice == "💰 Payments":
        st.title("Payment Gateway")
        search_name = st.text_input("Search Student Name")
        if search_name:
            results = pd.read_sql(f"SELECT * FROM students WHERE name LIKE '%{search_name}%'", conn)
            if not results.empty:
                student = results.iloc[0]
                st.info(f"Selected: {student['name']} ({student['grade']})")
                
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    month = st.selectbox("Month", ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"])
                    amount = st.number_input("Amount (Rs.)", min_value=0.0)
                    process = st.button("Generate & Save Payment")
                
                if process:
                    today = datetime.now().strftime("%Y-%m-%d")
                    conn.execute("INSERT INTO payments (student_name, grade, month, amount, date) VALUES (?,?,?,?,?)", (student['name'], student['grade'], month, amount, today))
                    conn.commit()
                    
                    # පින්තූරයේ පෙනෙන ආකාරයටම CSS මගින් රිසිට් එක නිර්මාණය කිරීම
                    st.markdown(f"""
                        <div class="receipt-container">
                            <div class="receipt-header">
                                <div class="receipt-title">🎓 SMART CLASS</div>
                                <div class="receipt-subtitle">Official Payment Receipt</div>
                            </div>
                            <div class="receipt-detail"><span class="receipt-label">Date:</span> {today}</div>
                            <div class="receipt-detail"><span class="receipt-label">Student:</span> {student['name']}</div>
                            <div class="receipt-detail"><span class="receipt-label">Grade:</span> {student['grade']}</div>
                            <div class="receipt-detail"><span class="receipt-label">Month:</span> {month}</div>
                            <div class="receipt-detail"><span class="receipt-label">Paid Amount:</span> Rs. {amount:,.2f}</div>
                            <div class="receipt-footer">
                                <hr style='border: 0.5px solid #eee;'>
                                Thank you for your payment!
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # WhatsApp පණිවිඩය පිළිවෙළට සැකසීම
                    whatsapp_msg = (
                        f"🎓 *SMART CLASS OFFICIAL RECEIPT*\n\n"
                        f"📅 *Date:* {today}\n"
                        f"👤 *Student:* {student['name']}\n"
                        f"📚 *Grade:* {student['grade']}\n"
                        f"🗓️ *Month:* {month}\n"
                        f"💰 *Paid Amount:* Rs. {amount:,.2f}\n\n"
                        f"✅ Payment Successful. Thank you for your payment!"
                    )
                    encoded_msg = urllib.parse.quote(whatsapp_msg)
                    st.markdown(f'<a href="https://wa.me/{student['whatsapp']}?text={encoded_msg}" target="_blank" style="text-decoration:none;"><div style="background-color:#25d366;color:white;padding:15px;text-align:center;border-radius:10px;font-weight:bold;font-size:18px;">📲 Send WhatsApp Receipt</div></a>', unsafe_allow_html=True)

    # --- REPORTS ---
    elif choice == "📊 Reports":
        st.title("Reports Management")
        t1, t2, t3 = st.tabs(["Student List", "Payment Records", "🗑️ Delete Records"])
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
                st.subheader("Delete Payment Record")
                pid = st.number_input("Payment ID", min_value=1, step=1, key="del_pay")
                if st.button("Delete Record", type="primary"):
                    conn.execute(f"DELETE FROM payments WHERE id={pid}")
                    conn.commit()
                    st.rerun()
