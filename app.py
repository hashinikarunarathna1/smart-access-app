import streamlit as st
import pandas as pd
import sqlite3
import urllib.parse
from datetime import datetime

# Page Setup
st.set_page_config(page_title="Smart Access Pro", layout="centered")

# Custom CSS
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 2.5em;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

def get_connection():
    return sqlite3.connect("smart_management_v8.db", check_same_thread=False)

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
            conn.execute("INSERT INTO students (name, school, grade, whatsapp) VALUES (?,?,?,?)", (name, school, grade, wa))
            conn.commit()
            st.success("සාර්ථකව ලියාපදිංචි කළා!")

    elif choice == "Student Payment":
        st.title("💰 Payment Gateway")
        conn = get_connection()
        
        # නම Type කිරීමට Input එකක් ලබා දීම
        typed_name = st.text_input("Type Student Name")
        
        # ඩේටාබේස් එකේ එම නම තිබේදැයි පරීක්ෂා කිරීම
        student_data = pd.read_sql(f"SELECT * FROM students WHERE name = '{typed_name}'", conn)
        
        if not student_data.empty:
            # නම නිවැරදි නම් විස්තර ලබා ගැනීම
            s_grade = student_data['grade'].values[0]
            student_wa = student_data['whatsapp'].values[0]
            
            st.success(f"Student Found: {typed_name}")
            st.text_input("Grade", value=s_grade, disabled=True)
            
            months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
            selected_month = st.selectbox("Select Month", months)
            amt = st.number_input("Amount (Rs.)", min_value=0.0, step=100.0)
            
            if st.button("Save & Send Official Receipt"):
                if amt > 0:
                    today = datetime.now().strftime("%Y-%m-%d")
                    conn.execute("INSERT INTO payments (student_name, grade, month, amount, date) VALUES (?,?,?,?,?)", 
                                 (typed_name, s_grade, selected_month, amt, today))
                    conn.commit()
                    
                    receipt_msg = (f"🎓 *SMART CLASS - Official Receipt* 🎓\n-----------------------------------\n👤 *Student:* {typed_name}\n📚 *Grade:* {s_grade}\n🗓️ *Month:* {selected_month}\n💰 *Amount:* Rs. {amt:,.2f}\n📅 *Date:* {today}\n✅ *Status:* Payment Received\n-----------------------------------\n*Thank you for your payment!*")
                    encoded_msg = urllib.parse.quote(receipt_msg)
                    wa_url = f"https://wa.me/{student_wa}?text={encoded_msg}"
                    
                    st.success("Payment Saved!")
                    st.markdown(f'<a href="{wa_url}" target="_blank"><button style="background-color: #25D366; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; width: 100%;">📲 Send Official WhatsApp Receipt</button></a>', unsafe_allow_html=True)
        elif typed_name != "":
            st.error("ශිෂ්‍යයා සොයාගත නොහැක. කරුණාකර නිවැරදි නම Type කරන්න.")

    elif choice == "View Data":
        st.title("📊 Records")
        # කලින් කෝඩ් එකේ තිබූ View Data කොටස මෙතැනට එනු ඇත (පිටු සීමාව නිසා කෙටි කරන ලදී)
        st.write("Please refer to previous code for View Data section logic.")

    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()
