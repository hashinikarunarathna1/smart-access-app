import streamlit as st
import pandas as pd
import sqlite3
import urllib.parse
from datetime import datetime

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="Smart Class Pro", page_icon="🎓", layout="wide")

# Dashboard UI එක සහ Metrics Cards වඩාත් ආකර්ෂණීය කිරීමට CSS ඇතුළත් කිරීම
st.markdown("""
    <style>
    /* Metric Cards Styling */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #ffffff 0%, #f0f4f8 100%);
        padding: 24px !important; 
        border-radius: 16px !important;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        transition: transform 0.2s;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
    }
    /* Metric Labels & Values */
    div[data-testid="stMetricLabel"] {
        color: #4a5568 !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    div[data-testid="stMetricValue"] {
        color: #1a73e8 !important;
        font-size: 28px !important;
        font-weight: 700 !important;
    }
    /* Common Button Styling */
    .stButton>button {
        width: 100%; border-radius: 10px; height: 3.5em;
        background: linear-gradient(90deg, #1a73e8 0%, #34a853 100%); 
        color: white !important;
        font-weight: bold; border: none;
        box-shadow: 0 4px 6px rgba(26, 115, 232, 0.2);
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #1557b0 0%, #2b843f 100%);
    }
    /* Receipt Styling */
    .receipt-container {
        border: 2px dashed #1a73e8; border-radius: 16px;
        padding: 25px; margin: 20px auto; max-width: 500px;
        font-family: 'Courier New', Courier, monospace;
        background-color: #f8f9fa;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    .receipt-title {
        color: #1a73e8; font-size: 26px; font-weight: bold; text-align: center;
        border-bottom: 2px dashed #ddd; padding-bottom: 10px; margin-bottom: 15px;
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

GRADES = ["Grade 6", "Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Revision", "Theory", "Online", "Edexcel", "Office Package"]

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

    # --- 🚀 DASHBOARD (UPDATED DESIGN) ---
    if choice == "🚀 Dashboard":
        st.markdown("<h1 style='color: #1a73e8;'>🚀 System Overview & Analytics</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color: #718096;'>ආයතනයේ වත්මන් තත්ත්වය සහ මූල්‍ය විශ්ලේෂණය මෙතැනින් බලන්න.</p>", unsafe_allow_html=True)
        st.write("")

        # දත්ත ලබා ගැනීම
        total_students = pd.read_sql("SELECT COUNT(*) FROM students", conn).iloc[0,0]
        all_pay = pd.read_sql("SELECT amount FROM payments", conn)
        all_exp = pd.read_sql("SELECT amount FROM expenses", conn)
        
        income = all_pay['amount'].sum() if not all_pay.empty else 0
        expense = all_exp['amount'].sum() if not all_exp.empty else 0
        net = income - expense
        
        # 3-Column Metrics Card Layout
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric(label="👥 TOTAL REGISTERED STUDENTS", value=f"{total_students} Students")
        with m2:
            st.metric(label="💸 TOTAL CASH OUT (EXPENSES)", value=f"Rs. {expense:,.2f}")
        with m3:
            # ශේෂය ධන හෝ සෘණ ද යන්න මත වර්ණය වෙනස් කිරීමට (UI එකට ගැළපෙන සේ)
            st.metric(label="📈 NET BALANCE (PROFIT)", value=f"Rs. {net:,.2f}")
        
        st.write("")
        st.divider()
        st.write("")
        
        # මාසික ආදායම් වගුව ලස්සනට පෙන්වීම
        st.markdown("<h3 style='color: #2d3748;'>📅 Monthly Revenue Summary</h3>", unsafe_allow_html=True)
        
        if not all_pay.empty:
            df_monthly = pd.read_sql("SELECT month as 'Month', SUM(amount) as 'Total Income (Rs.)' FROM payments GROUP BY month", conn)
            # වගුවේ පෙනුම සකස් කිරීම
            st.dataframe(
                df_monthly.style.format({'Total Income (Rs.)': 'Rs. {:,.2f}'}),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("තවමත් ගෙවීම් දත්ත ඇතුළත් කර නැත.")

    # --- 📝 REGISTRATION ---
    elif choice == "📝 Registration":
        st.title("New Student Registration")
        with st.form("reg_form", clear_on_submit=True):
            name = st.text_input("Student Name")
            school = st.text_input("School")
            grade = st.selectbox("Grade", GRADES)
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
                        conn.execute("INSERT INTO expenses (description, amount, date, target_month) VALUES (?,?,?,?)", (desc, amt, datetime.now().strftime("%Y-%m-%d %H:%M"), t_month))
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
                for g in GRADES:
                    g_data = df_std[df_std['grade'] == g]
                    if not g_data.empty:
                        with st.expander(f"📂 {g} - ({len(g_data)})"):
                            st.dataframe(g_data, use_container_width=True)
        with tab2:
            st.dataframe(pd.read_sql("SELECT * FROM payments", conn), use_container_width=True)
        with tab3:
            cm = st.selectbox("Month", months_list)
            cg = st.selectbox("Grade", GRADES)
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
