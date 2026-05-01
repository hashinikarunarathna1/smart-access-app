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
    .receipt-title {
        color: #1a73e8; font-size: 28px; font-weight: bold; text-align: center;
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
    
    try:
        cursor.execute("SELECT target_month FROM expenses LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute('ALTER TABLE expenses ADD COLUMN target_month TEXT')
        conn.commit()
    conn.close()

init_db()

# Global variables for grades
GRADES = ["Grade 6", "Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Revision", "Theory", "Online", "Edexcel"]

# --- 3. APP LOGIC ---
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
    st.sidebar.title("💎 Smart Class Pro")
    choice = st.sidebar.radio("Main Menu", ["🚀 Dashboard", "📝 Registration", "💰 Payments", "💸 Cash Out", "📊 Reports"])
    
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

    conn = get_connection()
    months_list = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

    # --- 🚀 DASHBOARD ---
    if choice == "🚀 Dashboard":
        st.title("System Overview")
        total_students = pd.read_sql("SELECT COUNT(*) FROM students", conn).iloc[0,0]
        all_pay = pd.read_sql("SELECT amount FROM payments", conn)
        all_exp = pd.read_sql("SELECT amount FROM expenses", conn)
        
        income = all_pay['amount'].sum() if not all_pay.empty else 0
        expense = all_exp['amount'].sum() if not all_exp.empty else 0
        net = income - expense
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Registered Students", total_students)
        m2.metric("Total Cash Out", f"Rs. {expense:,.2f}")
        m3.metric("Net Balance", f"Rs. {net:,.2f}")
        
        st.divider()
        st.subheader("📅 Monthly Revenue (Student Payments)")
        if not all_pay.empty:
            st.table(pd.read_sql("SELECT month, SUM(amount) as Total FROM payments GROUP BY month", conn))
        else:
            st.info("තවමත් ගෙවීම් දත්ත නැත.")

    # --- 📝 REGISTRATION ---
    elif choice == "📝 Registration":
        st.title("New Student Registration")
        with st.form("reg_form", clear_on_submit=True):
            name = st.text_input("Student Name")
            school = st.text_input("School")
            grade = st.selectbox("Grade", GRADES) # යාවත්කාලීන කළ ලැයිස්තුව
            wa = st.text_input("WhatsApp Number")
            if st.form_submit_button("Register"):
                if name and wa:
                    conn.execute("INSERT INTO students (name, school, grade, whatsapp) VALUES (?,?,?,?)", (name, school, grade, wa))
                    conn.commit()
                    st.success(f"{name} ලියාපදිංචි කිරීම සාර්ථකයි!")

    # --- 💰 PAYMENTS ---
    elif choice == "💰 Payments":
        st.title("Payment Gateway")
        search = st.text_input("Search Student Name")
        if search:
            res = pd.read_sql(f"SELECT * FROM students WHERE name LIKE '%{search}%'", conn)
            if not res.empty:
                st.dataframe(res)
                s_name = st.selectbox("Confirm Student Name", res['name'].tolist())
                s_info = res[res['name'] == s_name].iloc[0]
                month = st.selectbox("Payment Month", months_list)
                amt = st.number_input("Amount", min_value=0.0, value=1500.0)
                if st.button("Submit Payment"):
                    date_str = datetime.now().strftime("%Y-%m-%d")
                    conn.execute("INSERT INTO payments (student_name, grade, month, amount, date) VALUES (?,?,?,?,?)", (s_name, s_info['grade'], month, amt, date_str))
                    conn.commit()
                    
                    st.markdown(f'<div class="receipt-container"><div class="receipt-title">🎓 SMART CLASS</div><p style="text-align:center;">Date: {date_str}<br>Name: {s_name}<br>Month: {month}<br>Amount: Rs.{amt:,.2f}</p></div>', unsafe_allow_html=True)
                    
                    wa_msg = f"🎓 *SMART CLASS RECEIPT*\n\n👤 Name: {s_name}\n🗓️ Month: {month}\n💰 Amount: Rs. {amt:,.2f}\n✅ Recorded."
                    st.markdown(f'<a href="https://wa.me/{s_info["whatsapp"]}?text={urllib.parse.quote(wa_msg)}" target="_blank"><button style="background-color:#25d366; color:white; width:100%; border-radius:10px; padding:10px; border:none; cursor:pointer;">📲 Send WhatsApp Receipt</button></a>', unsafe_allow_html=True)

    # --- 💸 CASH OUT ---
    elif choice == "💸 Cash Out":
        st.title("💸 Targeted Cash Out")
        col1, col2 = st.columns(2)
        with col1:
            t_month = st.selectbox("Select Month to Withdraw from", months_list)
            m_income = pd.read_sql(f"SELECT SUM(amount) as total FROM payments WHERE month='{t_month}'", conn).iloc[0,0] or 0.0
            m_expenses = pd.read_sql(f"SELECT SUM(amount) as total FROM expenses WHERE target_month='{t_month}'", conn).iloc[0,0] or 0.0
            remaining_balance = m_income - m_expenses
            
            st.info(f"Available for {t_month}: **Rs. {remaining_balance:,.2f}**")
            st.caption(f"(Total Income: Rs. {m_income:,.2f} | Already Cashed Out: Rs. {m_expenses:,.2f})")
        
        with col2:
            with st.form("co_form", clear_on_submit=True):
                desc = st.text_input("Reason")
                amt = st.number_input("Amount", min_value=0.0)
                if st.form_submit_button("Confirm Cash Out"):
                    if amt > remaining_balance:
                        st.error(f"වැඩියෙන් මුදල් ගන්න බැහැ!")
                    elif desc and amt > 0:
                        conn.execute("INSERT INTO expenses (description, amount, date, target_month) VALUES (?,?,?,?)", 
                                     (desc, amt, datetime.now().strftime("%Y-%m-%d %H:%M"), t_month))
                        conn.commit()
                        st.success("Cash Out Success!")
                        st.rerun()
        
        st.subheader("📜 History")
        st.dataframe(pd.read_sql("SELECT * FROM expenses ORDER BY id DESC", conn), use_container_width=True)

    # --- 📊 REPORTS ---
    elif choice == "📊 Reports":
        st.title("Reports & Management")
        tab1, tab2, tab3, tab4 = st.tabs(["👥 Students", "📄 Payments", "🔴 Arrears", "🗑️ Delete"])
        
        with tab1:
            df_std = pd.read_sql("SELECT * FROM students", conn)
            if not df_std.empty:
                for g in GRADES: # යාවත්කාලීන කළ ලැයිස්තුව
                    g_data = df_std[df_std['grade'] == g]
                    if not g_data.empty:
                        with st.expander(f"📂 {g} - ({len(g_data)})"):
                            st.dataframe(g_data, use_container_width=True)
        with tab2:
            st.dataframe(pd.read_sql("SELECT * FROM payments", conn), use_container_width=True)
        with tab3:
            cm = st.selectbox("Month", months_list)
            cg = st.selectbox("Grade", GRADES) # යාවත්කාලීන කළ ලැයිස්තුව
            if st.button("Check Arrears"):
                all_s = pd.read_sql(f"SELECT name FROM students WHERE grade='{cg}'", conn)
                paid_s = pd.read_sql(f"SELECT student_name FROM payments WHERE month='{cm}' AND grade='{cg}'", conn)
                arrears = all_s[~all_s['name'].isin(paid_s['student_name'].tolist())]
                
                if not arrears.empty:
                    st.table(arrears)
                else:
                    st.success("All Paid!")
                    
        with tab4:
            st.subheader("Remove Records")
            dt = st.radio("Type", ["Payments", "Students", "Expenses"])
            di = st.number_input("ID", min_value=1)
            if st.button("Delete"):
                conn.execute(f"DELETE FROM {dt.lower()} WHERE id={di}")
                conn.commit()
                st.rerun()
