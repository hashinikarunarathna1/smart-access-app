import streamlit as st
import pandas as pd
import sqlite3
import urllib.parse

# Page Setup
st.set_page_config(page_title="Smart Access Pro", layout="centered")

# Custom CSS for UI Design
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        background-color: #007bff;
        color: white;
        font-weight: bold;
    }
    .stTextInput>div>div>input { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# Database logic
def get_connection():
    return sqlite3.connect("management.db", check_same_thread=False)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS students (name TEXT, school TEXT, grade TEXT, whatsapp TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS payments (student_name TEXT, amount TEXT, date TEXT)')
    conn.commit()
    conn.close()

init_db()

# Login
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
        st.info("සාදරයෙන් පිළිගන්නවා!")
        
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
        students_df = pd.read_sql("SELECT name, whatsapp FROM students", conn)
        if not students_df.empty:
            s_name = st.selectbox("Select Student", students_df['name'])
            amt = st.text_input("Amount (Rs.)")
            if st.button("Save & Send WhatsApp"):
                conn.execute("INSERT INTO payments VALUES (?,?,?)", (s_name, amt, "Today"))
                conn.commit()
                
                student_wa = students_df[students_df['name'] == s_name]['whatsapp'].values[0]
                msg = f"ස්තූතියි {s_name}, රු. {amt} මුදල අපට ලැබුණා."
                encoded_msg = urllib.parse.quote(msg)
                wa_url = f"https://wa.me/{student_wa}?text={encoded_msg}"
                st.markdown(f'[👉 මෙතනින් WhatsApp Message එක යවන්න]({wa_url})', unsafe_allow_html=True)
        else:
            st.warning("මුලින්ම ශිෂ්‍යයෙකු ලියාපදිංචි කරන්න.")

    elif choice == "View Data":
        st.title("📊 Records")
        conn = get_connection()
        st.write("Registered Students")
        st.dataframe(pd.read_sql("SELECT * FROM students", conn))

    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()
