import streamlit as st
import sqlite3
import pandas as pd

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect("management.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS students 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, school TEXT, grade TEXT, class_name TEXT, whatsapp TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS payments 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, student_name TEXT, grade TEXT, amount TEXT)''')
    conn.commit()
    return conn

conn = init_db()

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("Smart Access Menu")
page = st.sidebar.radio("Go to", ["Login", "Dashboard", "New Registration", "Student Payment", "Registration Details", "Payment History"])

# --- LOGIN SCREEN ---
if page == "Login":
    st.title("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == "admin" and password == "1234":
            st.success("Logged In Successfully!")
            st.session_state["logged_in"] = True
        else:
            st.error("Invalid Credentials")

# --- DASHBOARD ---
elif page == "Dashboard":
    st.title("📊 Management Dashboard")
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"Total Students: {pd.read_sql('SELECT COUNT(*) FROM students', conn).iloc[0,0]}")
    with col2:
        st.success(f"Total Payments: {pd.read_sql('SELECT COUNT(*) FROM payments', conn).iloc[0,0]}")

# --- NEW REGISTRATION ---
elif page == "New Registration":
    st.title("📝 Student Registration")
    with st.form("reg_form"):
        name = st.text_input("Student Full Name")
        school = st.text_input("School")
        grade = st.text_input("Grade")
        class_name = st.text_input("Class Name")
        whatsapp = st.text_input("WhatsApp Number")
        if st.form_submit_button("Save Student"):
            cursor = conn.cursor()
            cursor.execute("INSERT INTO students (name, school, grade, class_name, whatsapp) VALUES (?,?,?,?,?)", 
                           (name, school, grade, class_name, whatsapp))
            conn.commit()
            st.success("Student Registered!")

# --- STUDENT PAYMENT ---
elif page == "Student Payment":
    st.title("💰 Add Payment")
    p_name = st.text_input("Student Name")
    p_grade = st.text_input("Grade")
    p_amount = st.text_input("Amount (Rs.)")
    
    if st.button("Confirm Payment"):
        student = conn.execute("SELECT * FROM students WHERE name=? AND grade=?", (p_name, p_grade)).fetchone()
        if student:
            conn.execute("INSERT INTO payments (student_name, grade, amount) VALUES (?,?,?)", (p_name, p_grade, p_amount))
            conn.commit()
            st.success("Payment Added!")
        else:
            st.error("Student Not Found!")

# --- REGISTRATION DETAILS ---
elif page == "Registration Details":
    st.title("📋 Registered Students")
    df = pd.read_sql("SELECT name, school, grade, whatsapp, class_name FROM students", conn)
    st.dataframe(df, use_container_width=True)

# --- PAYMENT HISTORY ---
elif page == "Payment History":
    st.title("📜 Payment History")
    df_pay = pd.read_sql("SELECT student_name, grade, amount FROM payments ORDER BY id DESC", conn)
    st.table(df_pay)
