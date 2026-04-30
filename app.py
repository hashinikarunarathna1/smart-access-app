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
    .delete-confirm>button {
        background-color: #ff4b4b !important;
        color: white !important;
    }
    .cancel-btn>button {
        background-color: #f0f2f6 !important;
        color: black !important;
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

# Session State for Delete Confirmation
if 'confirm_delete_id' not in st.session_state:
    st.session_state.confirm_delete_id = None
if 'delete_type' not in st.session_state:
    st.session_state.delete_type = None

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
        students_df = pd.read_sql("SELECT name, grade, whatsapp FROM students", conn)
        
        if not students_df.empty:
            s_name = st.selectbox("Select Student Name", students_df['name'])
            selected_student_info = students_df[students_df['name'] == s_name]
            s_grade = selected_student_info['grade'].values[0]
            student_wa = selected_student_info['whatsapp'].values[0]

            st.text_input("Grade", value=s_grade, disabled=True)
            months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
            selected_month = st.selectbox("Select Month", months)
            amt = st.number_input("Amount (Rs.)", min_value=0.0, step=100.0)
            
            if st.button("Save & Send Official Receipt"):
                if amt > 0:
                    today = datetime.now().strftime("%Y-%m-%d")
                    conn.execute("INSERT INTO payments (student_name, grade, month, amount, date) VALUES (?,?,?,?,?)", 
                                 (s_name, s_grade, selected_month, amt, today))
                    conn.commit()
                    
                    receipt_msg = (f"🎓 *SMART CLASS - Official Receipt* 🎓\n-----------------------------------\n👤 *Student:* {s_name}\n📚 *Grade:* {s_grade}\n🗓️ *Month:* {selected_month}\n💰 *Amount:* Rs. {amt:,.2f}\n📅 *Date:* {today}\n✅ *Status:* Payment Received\n-----------------------------------\n*Thank you for your payment!*")
                    encoded_msg = urllib.parse.quote(receipt_msg)
                    wa_url = f"https://wa.me/{student_wa}?text={encoded_msg}"
                    
                    st.success("Payment Saved Successfully!")
                    st.markdown(f'<a href="{wa_url}" target="_blank"><button style="background-color: #25D366; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; width: 100%;">📲 Send Official WhatsApp Receipt</button></a>', unsafe_allow_html=True)
        else:
            st.warning("Register a student first.")

    elif choice == "View Data":
        st.title("📊 Records")
        conn = get_connection()
        tab1, tab2 = st.tabs(["Registered Students", "Payment History"])
        
        with tab1:
            st.subheader("Manage Students")
            students_data = pd.read_sql("SELECT * FROM students", conn)
            for index, row in students_data.iterrows():
                cols = st.columns([3, 2, 2, 1])
                cols[0].write(row['name'])
                cols[1].write(row['grade'])
                cols[2].write(row['whatsapp'])
                
                # Delete Confirmation Logic
                if st.session_state.confirm_delete_id == row['id'] and st.session_state.delete_type == 'student':
                    st.warning(f"Delete {row['name']}?")
                    c1, c2 = st.columns(2)
                    if c1.button("✅ Yes", key=f"yes_std_{row['id']}"):
                        conn.execute(f"DELETE FROM students WHERE id = {row['id']}")
                        conn.commit()
                        st.session_state.confirm_delete_id = None
                        st.rerun()
                    if c2.button("❌ No", key=f"no_std_{row['id']}"):
                        st.session_state.confirm_delete_id = None
                        st.rerun()
                else:
                    if cols[3].button("🗑️", key=f"del_std_{row['id']}"):
                        st.session_state.confirm_delete_id = row['id']
                        st.session_state.delete_type = 'student'
                        st.rerun()
            
        with tab2:
            st.subheader("Manage Payments")
            payments_data = pd.read_sql("SELECT * FROM payments", conn)
            for index, row in payments_data.iterrows():
                cols = st.columns([2, 1, 1, 1, 1])
                cols[0].write(row['student_name'])
                cols[1].write(row['month'])
                cols[2].write(f"Rs.{row['amount']}")
                cols[3].write(row['date'])
                
                # Delete Confirmation Logic
                if st.session_state.confirm_delete_id == row['id'] and st.session_state.delete_type == 'payment':
                    st.error("Delete this record?")
                    c1, c2 = st.columns(2)
                    if c1.button("Confirm", key=f"yes_pay_{row['id']}"):
                        conn.execute(f"DELETE FROM payments WHERE id = {row['id']}")
                        conn.commit()
                        st.session_state.confirm_delete_id = None
                        st.rerun()
                    if c2.button("Cancel", key=f"no_pay_{row['id']}"):
                        st.session_state.confirm_delete_id = None
                        st.rerun()
                else:
                    if cols[4].button("🗑️", key=f"del_pay_{row['id']}"):
                        st.session_state.confirm_delete_id = row['id']
                        st.session_state.delete_type = 'payment'
                        st.rerun()
            
            if not payments_data.empty:
                st.markdown("---")
                total_all = payments_data['amount'].sum()
                st.subheader(f"💰 Total: Rs. {total_all:,.2f}")
                
                st.markdown("### 🗓️ Monthly Summary")
                monthly_summary = payments_data.groupby('month')['amount'].sum().reset_index()
                st.table(monthly_summary)

    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()
