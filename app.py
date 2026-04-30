import streamlit as st
import pandas as pd
import sqlite3
import urllib.parse
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="Smart Class Pro", page_icon="🎓", layout="centered")

# --- CUSTOM CSS FOR UI ENHANCEMENT ---
st.markdown("""
    <style>
    /* Main Background */
    .stApp {
        background-color: #f8f9fa;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #1e293b !important;
    }
    section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] label {
        color: white !important;
    }

    /* Titles and Headers */
    h1 {
        color: #1e293b;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 700;
    }

    /* Card-like containers for Dashboard */
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
        border-left: 5px solid #25d366;
    }

    /* Buttons Styling */
    .stButton>button {
        border-radius: 12px;
        height: 3em;
        background-color: #25d366;
        color: white;
        font-weight: bold;
        transition: 0.3s;
        border: none;
    }
    .stButton>button:hover {
        background-color: #128c7e;
        transform: scale(1.02);
    }

    /* Inputs */
    .stTextInput>div>div>input, .stNumberInput>div>div>input {
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- DATABASE LOGIC ---
def get_connection():
    return sqlite3.connect("smart_management_v9.db", check_same_thread=False)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS students 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, school TEXT, grade TEXT, whatsapp TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS payments 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, student_name TEXT, grade TEXT, month TEXT, amount REAL, date TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- LOGIN SYSTEM ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.markdown("<h1 style='text-align: center;'>🎓 Smart Class Pro</h1>", unsafe_allow_html=True)
    with st.container():
        st.markdown("<div style='background-color: white; padding: 30px; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.1);'>", unsafe_allow_html=True)
        user = st.text_input("Username", placeholder="Enter username")
        pw = st.text_input("Password", type="password", placeholder="Enter password")
        if st.button("Login to Dashboard"):
            if user == "admin" and pw == "1234":
                st.session_state['logged_in'] = True
                st.rerun()
            else:
                st.error("Access Denied: Incorrect credentials")
        st.markdown("</div>", unsafe_allow_html=True)
else:
    # --- SIDEBAR ---
    st.sidebar.markdown("<h2 style='color: white; text-align: center;'>💎 Control Panel</h2>", unsafe_allow_html=True)
    st.sidebar.markdown("---")
    choice = st.sidebar.radio("Navigation", ["🚀 Dashboard", "📝 Student Registration", "💰 Payment Gateway", "📊 View Records"])
    
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

    # --- DASHBOARD ---
    if choice == "🚀 Dashboard":
        st.title("Welcome to Smart Class")
        conn = get_connection()
        total_students = pd.read_sql("SELECT COUNT(*) FROM students", conn).iloc[0,0]
        total_income = pd.read_sql("SELECT SUM(amount) FROM payments", conn).iloc[0,0] or 0
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"<div class='metric-card'><h3>Students</h3><h2>{total_students}</h2></div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div class='metric-card' style='border-left: 5px solid #007bff;'><h3>Total Earnings</h3><h2>Rs. {total_income:,.2f}</h2></div>", unsafe_allow_html=True)
        
        st.markdown("---")
        st.image("https://img.freepik.com/free-vector/education-learning-concept-banner-poster-flyer-template-design_1017-31015.jpg", use_column_width=True)

    # --- REGISTRATION ---
    elif choice == "📝 Student Registration":
        st.title("Register New Student")
        with st.form("reg_form", clear_on_submit=True):
            name = st.text_input("Full Name")
            school = st.text_input("School Name")
            grade = st.text_input("Grade / Batch")
            wa = st.text_input("WhatsApp Number (e.g., 94771234567)")
            if st.form_submit_button("Submit Registration"):
                if name and wa:
                    conn = get_connection()
                    conn.execute("INSERT INTO students (name, school, grade, whatsapp) VALUES (?,?,?,?)", (name, school, grade, wa))
                    conn.commit()
                    st.success(f"Successfully registered {name}!")
                else:
                    st.warning("Please fill in the required fields.")

    # --- PAYMENT ---
    elif choice == "💰 Payment Gateway":
        st.title("Collect Fees")
        conn = get_connection()
        typed_name = st.text_input("Search Student by Name")
        student_data = pd.read_sql(f"SELECT * FROM students WHERE name LIKE '%{typed_name}%'", conn) if typed_name else pd.DataFrame()
        
        if not student_data.empty and len(student_data) == 1:
            row = student_data.iloc[0]
            st.info(f"Student: {row['name']} | Grade: {row['grade']}")
            months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
            selected_month = st.selectbox("Select Month", months)
            amt = st.number_input("Amount (Rs.)", min_value=0.0, step=100.0)
            
            if st.button("Generate Receipt"):
                today = datetime.now().strftime("%Y-%m-%d")
                conn.execute("INSERT INTO payments (student_name, grade, month, amount, date) VALUES (?,?,?,?,?)", 
                             (row['name'], row['grade'], selected_month, amt, today))
                conn.commit()
                
                receipt_msg = (f"🎓 *SMART CLASS - Official Receipt* 🎓\n-----------------------------------\n👤 *Student:* {row['name']}\n📚 *Grade:* {row['grade']}\n🗓️ *Month:* {selected_month}\n💰 *Amount:* Rs. {amt:,.2f}\n📅 *Date:* {today}\n✅ *Status:* Received\n-----------------------------------\n*Thank you!*")
                encoded_msg = urllib.parse.quote(receipt_msg)
                wa_url = f"https://wa.me/{row['whatsapp']}?text={encoded_msg}"
                
                st.success("Payment Recorded!")
                st.markdown(f'<a href="{wa_url}" target="_blank"><button style="background-color: #25D366; color: white; border: none; padding: 10px 20px; border-radius: 12px; cursor: pointer; width: 100%;">📲 Send WhatsApp Receipt</button></a>', unsafe_allow_html=True)
        elif typed_name:
            st.warning("Please type the exact name as registered.")

    # --- VIEW RECORDS ---
    elif choice == "📊 View Records":
        st.title("Data Management")
        tab1, tab2 = st.tabs(["Students List", "Payments History"])
        conn = get_connection()
        
        with tab1:
            df_s = pd.read_sql("SELECT * FROM students", conn)
            st.dataframe(df_s, use_container_width=True)
            
        with tab2:
            df_p = pd.read_sql("SELECT * FROM payments", conn)
            st.dataframe(df_p, use_container_width=True)
            if not df_p.empty:
                st.metric("Total Collected", f"Rs. {df_p['amount'].sum():,.2f}")
