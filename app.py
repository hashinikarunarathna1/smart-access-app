import streamlit as st
import pandas as pd
import sqlite3
import urllib.parse
from datetime import datetime

# --- 1. CONFIG & THEME-FRIENDLY STYLING ---
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
    cursor.execute('CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, description TEXT, amount REAL, date TEXT)')
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
            if user == "admin" and pw == "775512":
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

    # --- 🚀 DASHBOARD ---
    if choice == "🚀 Dashboard":
        st.title("System Overview")
        total_students = pd.read_sql("SELECT COUNT(*) FROM students", conn).iloc[0,0]
        all_payments_df = pd.read_sql("SELECT * FROM payments", conn)
        all_expenses_df = pd.read_sql("SELECT * FROM expenses", conn)
        
        rev_total = all_payments_df['amount'].sum() if not all_payments_df.empty else 0
        exp_total = all_expenses_df['amount'].sum() if not all_expenses_df.empty else 0
        net_balance = rev_total - exp_total # Cash out අඩුවූ පසු ඉතිරිය
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Students", total_students)
        m2.metric("Net Total (After Cash-out)", f"Rs. {net_balance:,.2f}") #
        m3.metric("Status", "Online")
        
        st.divider()
        st.subheader("📅 Monthly Revenue Breakdown (Student Payments)")
        if not all_payments_df.empty:
            # මෙතන පෙන්වන්නේ සිසුන් ගෙවූ මුළු මුදල පමණයි (Cash-out මෙයට බලපාන්නේ නැත)
            monthly_totals = all_payments_df.groupby('month')['amount'].sum().reset_index()
            monthly_totals.columns = ['Month', 'Student Payments (Rs.)']
            st.table(monthly_totals) #
        else:
            st.info("තවමත් ගෙවීම් දත්ත නැත.")

    # --- 💸 CASH OUT SECTION ---
    elif choice == "💸 Cash Out":
        st.title("💸 Cash Out & Payment Summary")
        
        # 1. පන්ති ගාස්තු මාස අනුව පෙන්වීම
        st.subheader("📊 Monthly Student Payment Summary")
        all_pay = pd.read_sql("SELECT month, amount FROM payments", conn)
        if not all_pay.empty:
            summary = all_pay.groupby('month')['amount'].sum().reset_index()
            summary.columns = ['Month', 'Total Collected (Rs.)']
            st.dataframe(summary, use_container_width=True) #
        else:
            st.info("ගෙවීම් වාර්තා නැත.")
            
        st.divider()

        # 2. Cash Out කිරීම
        st.subheader("📉 Record New Cash Out")
        with st.form("cash_out_form", clear_on_submit=True):
            desc = st.text_input("Reason / Description (e.g. Hall Fee)")
            amt = st.number_input("Amount to Cash Out (Rs.)", min_value=0.0)
            if st.form_submit_button("Confirm Cash Out"):
                if desc and amt > 0:
                    date_now = datetime.now().strftime("%Y-%m-%d %H:%M")
                    conn.execute("INSERT INTO expenses (description, amount, date) VALUES (?,?,?)", (desc, amt, date_now))
                    conn.commit()
                    st.success(f"රු. {amt} ක මුදලක් Cash Out කළා. මෙය Overall Balance එකෙන් අඩු වනු ඇත.") #
        
        # 3. පරණ Cash Out වාර්තා
        st.subheader("📜 Cash Out History")
        st.dataframe(pd.read_sql("SELECT * FROM expenses ORDER BY id DESC", conn), use_container_width=True)

    # --- අනිත් සියලුම කොටස් (Registration, Payments, Reports) කලින් තිබූ පරිදිම ---
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
                    st.markdown(f'<div class="receipt-container"><div class="receipt-title">🎓 SMART CLASS</div><p style="text-align:center;">Date: {date_str}<br>Name: {s_name}<br>Month: {month}<br>Amount: Rs.{amt:,.2f}</p></div>', unsafe_allow_html=True)
                    wa_msg = f"🎓 *SMART CLASS RECEIPT*\n\n👤 Name: {s_name}\n🗓️ Month: {month}\n💰 Amount: Rs. {amt:,.2f}\n✅ Recorded."
                    st.markdown(f'<a href="https://wa.me/{s_info["whatsapp"]}?text={urllib.parse.quote(wa_msg)}" target="_blank"><button style="background-color:#25d366; color:white; width:100%; border-radius:10px; padding:10px; border:none; cursor:pointer;">📲 Send WhatsApp Receipt</button></a>', unsafe_allow_html=True)

    elif choice == "📊 Reports":
        st.title("Reports & Management")
        tab1, tab2, tab3, tab4 = st.tabs(["👥 Student List", "📄 Payment Logs", "🔴 Arrears", "🗑️ Delete"])
        
        with tab1:
            df_std = pd.read_sql("SELECT * FROM students", conn)
            if not df_std.empty:
                grades = ["Grade 6", "Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Revision", "Theory"]
                for g in grades:
                    g_data = df_std[df_std['grade'] == g]
                    if not g_data.empty:
                        with st.expander(f"📂 {g} - ({len(g_data)} Students)"):
                            st.dataframe(g_data[['id', 'name', 'school', 'whatsapp']], use_container_width=True)
        
        with tab2:
            st.dataframe(pd.read_sql("SELECT * FROM payments", conn), use_container_width=True)
            
        with tab3:
            c_month = st.selectbox("Check Month", ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"])
            c_grade = st.selectbox("Check Grade", ["Grade 6", "Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Revision", "Theory"])
            if st.button("Generate Arrears List"):
                all_s = pd.read_sql(f"SELECT name FROM students WHERE grade='{c_grade}'", conn)
                paid_s = pd.read_sql(f"SELECT student_name FROM payments WHERE month='{c_month}' AND grade='{c_grade}'", conn)
                arr = all_s[~all_s['name'].isin(paid_s['student_name'].tolist())]
                if not arr.empty:
                    st.warning(f"Unpaid: {len(arr)}")
                    st.table(arr)
                else: st.success("All Paid!")

        with tab4:
            st.subheader("Remove Records")
            del_type = st.radio("Delete from:", ["Payments", "Students", "Expenses"])
            del_id = st.number_input("Enter ID", min_value=1, step=1)
            if st.button("Delete"):
                tbl = "payments" if del_type=="Payments" else "students" if del_type=="Students" else "expenses"
                conn.execute(f"DELETE FROM {tbl} WHERE id={del_id}")
                conn.commit()
                st.rerun()
