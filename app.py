import streamlit as st
import pandas as pd
import sqlite3
import urllib.parse
from datetime import datetime

# --- 1. CONFIG & THEME-FRIENDLY STYLING ---
st.set_page_config(page_title="Smart Class Pro", page_icon="🎓", layout="wide")

st.markdown("""
    <style>
    /* Dashboard Metrics - Adaptive colors */
    [data-testid="stMetric"] {
        background-color: rgba(28, 131, 225, 0.1) !important;
        padding: 20px !important;
        border-radius: 12px !important;
        border: 1px solid rgba(28, 131, 225, 0.2);
    }
    
    /* Buttons */
    .stButton>button {
        width: 100%; border-radius: 8px; height: 3.5em;
        background-color: #1a73e8; color: white !important;
        font-weight: bold; border: none;
    }

    /* Receipt - Adaptive text and background */
    .receipt-container {
        border: 2px solid #1a73e8;
        border-radius: 20px;
        padding: 30px;
        margin: 20px auto;
        max-width: 600px;
        font-family: 'Courier New', Courier, monospace;
        background-color: rgba(0, 0, 0, 0.05);
    }
    
    .receipt-title {
        color: #1a73e8;
        font-size: 28px;
        font-weight: bold;
        text-align: center;
        margin-bottom: 20px;
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
    conn.commit()

init_db()

# --- 3. LOGIN SYSTEM ---
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
                st.error("වැරදි දත්ත ඇතුළත් කළා!")
else:
    # --- 4. NAVIGATION ---
    st.sidebar.title("💎 Smart Class Pro")
    choice = st.sidebar.radio("Main Menu", ["🚀 Dashboard", "📝 Registration", "💰 Payments", "📊 Reports"])
    
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

    conn = get_connection()

    # --- DASHBOARD ---
    if choice == "🚀 Dashboard":
        st.title("System Overview")
        total_students = pd.read_sql("SELECT COUNT(*) FROM students", conn).iloc[0,0]
        all_payments_df = pd.read_sql("SELECT * FROM payments", conn)
        current_month = datetime.now().strftime("%B")
        
        rev_total = all_payments_df['amount'].sum() if not all_payments_df.empty else 0
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Students", total_students)
        m2.metric("Overall Revenue", f"Rs. {rev_total:,.2f}")
        m3.metric("Current Month", current_month)

    # --- REGISTRATION ---
    elif choice == "📝 Registration":
        st.title("New Student Registration")
        with st.form("reg_form", clear_on_submit=True):
            name = st.text_input("Student Name")
            school = st.text_input("School")
            grade = st.selectbox("Grade", ["Grade 6", "Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Revision", "Theory"])
            wa = st.text_input("WhatsApp Number (e.g. 94771234567)")
            if st.form_submit_button("Register"):
                if name and wa:
                    conn.execute("INSERT INTO students (name, school, grade, whatsapp) VALUES (?,?,?,?)", (name, school, grade, wa))
                    conn.commit()
                    st.success(f"{name} ලියාපදිංචි කිරීම සාර්ථකයි!")

    # --- PAYMENTS ---
    elif choice == "💰 Payments":
        st.title("Payment Gateway")
        search = st.text_input("Search Student Name")
        if search:
            res = pd.read_sql(f"SELECT * FROM students WHERE name LIKE '%{search}%'", conn)
            if not res.empty:
                st.dataframe(res)
                s_name = st.selectbox("Confirm Student Name", res['name'].tolist())
                s_info = res[res['name'] == s_name].iloc[0]
                
                month = st.selectbox("Payment Month", ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"])
                amt = st.number_input("Amount", min_value=0.0, value=1500.0)
                
                if st.button("Submit Payment"):
                    date_str = datetime.now().strftime("%Y-%m-%d")
                    conn.execute("INSERT INTO payments (student_name, grade, month, amount, date) VALUES (?,?,?,?,?)", (s_name, s_info['grade'], month, amt, date_str))
                    conn.commit()
                    
                    # Receipt Display
                    st.markdown(f"""
                        <div class="receipt-container">
                            <div class="receipt-title">🎓 SMART CLASS</div>
                            <p style='text-align:center;'><b>Official Payment Receipt</b></p>
                            <hr>
                            <p><b>Name:</b> {s_name}</p>
                            <p><b>Grade:</b> {s_info['grade']}</p>
                            <p><b>Month:</b> {month}</p>
                            <p><b>Amount:</b> Rs. {amt:,.2f}</p>
                            <p><b>Date:</b> {date_str}</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # WhatsApp Link
                    wa_msg = f"🎓 *SMART CLASS RECEIPT*\n\n👤 Name: {s_name}\n🗓️ Month: {month}\n💰 Amount: Rs. {amt:,.2f}\n✅ Payment Recorded."
                    st.markdown(f'<a href="https://wa.me/{s_info["whatsapp"]}?text={urllib.parse.quote(wa_msg)}" target="_blank"><button style="background-color:#25d366; color:white; width:100%; border-radius:10px; padding:10px; border:none; cursor:pointer;">📲 Send WhatsApp Receipt</button></a>', unsafe_allow_html=True)

    # --- REPORTS & ARREARS ---
    elif choice == "📊 Reports":
        st.title("Reports & Arrears")
        tab1, tab2, tab3 = st.tabs(["Student List", "Payment Logs", "🔴 Arrears List"])
        
        with tab1:
            st.dataframe(pd.read_sql("SELECT * FROM students", conn), use_container_width=True)
        
        with tab2:
            st.dataframe(pd.read_sql("SELECT * FROM payments", conn), use_container_width=True)
            
        with tab3:
            st.subheader("Check Unpaid Students")
            c_month = st.selectbox("Target Month", ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"], key="arr_m")
            c_grade = st.selectbox("Target Grade", ["Grade 6", "Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Revision", "Theory"], key="arr_g")
            
            if st.button("Generate Arrears List"):
                all_s = pd.read_sql(f"SELECT name, whatsapp FROM students WHERE grade='{c_grade}'", conn)
                paid_s = pd.read_sql(f"SELECT student_name FROM payments WHERE month='{c_month}' AND grade='{c_grade}'", conn)
                
                paid_names = paid_s['student_name'].tolist()
                arrears_df = all_s[~all_s['name'].isin(paid_names)]
                
                if not arrears_df.empty:
                    st.warning(f"⚠️ {c_month} සඳහා {c_grade} පන්තියේ {len(arrears_df)} දෙනෙකු ගෙවා නැත.")
                    st.table(arrears_df)
                else:
                    st.success("සියලුම සිසුන් ගෙවීම් කර ඇත!")
