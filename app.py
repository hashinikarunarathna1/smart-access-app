import streamlit as st
import pandas as pd
import sqlite3
import urllib.parse
from datetime import datetime

# Page Setup
st.set_page_config(page_title="Smart Access Pro", layout="centered")

# Custom CSS for UI
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        background-color: #28a745;
        color: white;
        font-weight: bold;
    }
    .stTextInput>div>div>input { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

def get_connection():
    return sqlite3.connect("smart_management_v4.db", check_same_thread=False)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS students 
                      (name TEXT, school TEXT, grade TEXT, whatsapp TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS payments 
                      (student_name TEXT, grade TEXT, month TEXT, amount TEXT, date TEXT)''')
    conn.commit()
    conn.close()

init_db()

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("🔐 Smart Access Login")
    user = st.text_input("Username")
    pw = st.text_input("Password", type="password")
    if st.button("Login"):
        if user == "admin" and pw == "1234":
            st.session_state['logged_in'] = True
            st.rerun()
        else:
            st.error("Invalid Credentials!")
else:
    st.sidebar.title("💎 Smart Access Menu")
    choice = st.sidebar.selectbox("Go to", ["Dashboard", "New Registration", "Student Payment", "View Data"])

    if choice == "Dashboard":
        st.title("🚀 Dashboard")
        st.info("Welcome to Smart Class") 
        
    elif choice == "New Registration":
        st.title("📝 Student Registration")
        name = st.text_input("Full Name")
        school = st.text_input("School")
        grade = st.text_input("Grade")
        wa = st.text_input("WhatsApp (e.g. 94771234567)")
        if st.button("Register Student"):
            conn = get_connection()
            conn.execute("INSERT INTO students VALUES (?,?,?,?)", (name, school, grade, wa))
            conn.commit()
            st.success("සාර්ථකව ලියාපදිංචි කළා!")

    elif choice == "Student Payment":
        st.title("💰 Payment Gateway")
        conn = get_connection()
        students_df = pd.read_sql("SELECT name, grade, whatsapp FROM students", conn)
        
        if not students_df.empty:
            s_name = st.selectbox("Select Student Name", students_df['name'])
            selected_student_info = students_df[students_df['name'] == s_name]
            s_grade = selected_student_info['grade'].values[0]
            student_wa = selected_student_info['whatsapp'].values[0]

            st.text_input("Grade", value=s_grade, disabled=True)
            months = ["January", "February", "March", "April", "May", "June", 
                      "July", "August", "September", "October", "November", "December"]
            selected_month = st.selectbox("Select Month", months)
            amt = st.text_input("Amount (Rs.)")
            
            if st.button("Save & Send Official Receipt"):
                if amt:
                    today = datetime.now().strftime("%Y-%m-%d")
                    conn.execute("INSERT INTO payments (student_name, grade, month, amount, date) VALUES (?,?,?,?,?)", 
                                 (s_name, s_grade, selected_month, amt, today))
                    conn.commit()
                    
                    # --- Official WhatsApp Message Design ---
                    receipt_msg = (
                        f"🎓 *SMART CLASS - Official Receipt* 🎓\n"
                        f"-----------------------------------\n"
                        f"👤 *Student:* {s_name}\n"
                        f"📚 *Grade:* {s_grade}\n"
                        f"🗓️ *Month:* {selected_month}\n"
                        f"💰 *Amount:* Rs. {amt}.00\n"
                        f"📅 *Date:* {today}\n"
                        f"✅ *Status:* Payment Received\n"
                        f"-----------------------------------\n"
                        f"*Thank you for your payment!*"
                    )
                    
                    encoded_msg = urllib.parse.quote(receipt_msg)
                    wa_url = f"https://wa.me/{student_wa}?text={encoded_msg}"
                    
                    st.success("Payment Saved Successfully!")
                    st.markdown(f'''
                        <a href="{wa_url}" target="_blank">
                            <button style="background-color: #25D366; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; width: 100%;">
                                📲 Send Official WhatsApp Receipt
                            </button>
                        </a>
                        ''', unsafe_allow_html=True)
                else:
                    st.warning("Please enter the amount.")
        else:
            st.warning("No students found. Register a student first.")

    elif choice == "View Data":
        st.title("📊 Records")
        conn = get_connection()
        tab1, tab2 = st.tabs(["Registered Students", "Payment History"])
        with tab1:
            st.dataframe(pd.read_sql("SELECT * FROM students", conn), use_container_width=True)
        with tab2:
            st.dataframe(pd.read_sql("SELECT * FROM payments", conn), use_container_width=True)

    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()
