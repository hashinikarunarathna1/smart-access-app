import streamlit as st
import pandas as pd
import sqlite3
import urllib.parse
from datetime import datetime

# --- 1. පරණ දත්ත මතක තබා ගැනීම (Performance Optimization) ---
@st.cache_resource
def get_connection():
    return sqlite3.connect("smart_management_v9.db", check_same_thread=False)

# --- PAGE CONFIG ---
st.set_page_config(page_title="Smart Class Pro", page_icon="🎓", layout="centered")

# --- CSS (සරල කර ඇත) ---
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .metric-card {
        background-color: white;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        text-align: center;
        border-left: 5px solid #25d366;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS students 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, school TEXT, grade TEXT, whatsapp TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS payments 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, student_name TEXT, grade TEXT, month TEXT, amount REAL, date TEXT)''')
    conn.commit()

init_db()

# --- LOGIN ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("🎓 Smart Class Pro")
    user = st.text_input("Username")
    pw = st.text_input("Password", type="password")
    if st.button("Login"):
        if user == "admin" and pw == "1234":
            st.session_state['logged_in'] = True
            st.rerun()
else:
    # --- NAVIGATION ---
    choice = st.sidebar.radio("Menu", ["🚀 Dashboard", "📝 Registration", "💰 Payment", "📊 Records"])
    
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

    conn = get_connection()

    if choice == "🚀 Dashboard":
        st.title("Smart Class Dashboard")
        
        # දත්ත ඉක්මනින් ලබා ගැනීම
        cur = conn.cursor()
        total_std = cur.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        total_inc = cur.execute("SELECT SUM(amount) FROM payments").fetchone()[0] or 0
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"<div class='metric-card'><h4>Students</h4><h2>{total_std}</h2></div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<div class='metric-card' style='border-left-color: #007bff;'><h4>Total (Rs)</h4><h2>{total_inc:,.0f}</h2></div>", unsafe_allow_html=True)

    elif choice == "📝 Registration":
        st.subheader("New Student")
        with st.form("reg", clear_on_submit=True):
            n = st.text_input("Name")
            g = st.text_input("Grade")
            w = st.text_input("WhatsApp (94...)")
            if st.form_submit_button("Save"):
                conn.execute("INSERT INTO students (name, grade, whatsapp) VALUES (?,?,?)", (n, g, w))
                conn.commit()
                st.success("Saved!")

    elif choice == "💰 Payment":
        st.subheader("Add Payment")
        t_name = st.text_input("Type Name").strip()
        if t_name:
            # නම හරියටම ගැලපෙනවාදැයි පරීක්ෂාව
            std = pd.read_sql(f"SELECT * FROM students WHERE name LIKE '%{t_name}%' LIMIT 1", conn)
            if not std.empty:
                s = std.iloc[0]
                st.info(f"Student: {s['name']} ({s['grade']})")
                m = st.selectbox("Month", ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"])
                a = st.number_input("Amount", min_value=0)
                if st.button("Save & Send"):
                    dt = datetime.now().strftime("%Y-%m-%d")
                    conn.execute("INSERT INTO payments (student_name, grade, month, amount, date) VALUES (?,?,?,?,?)", (s['name'], s['grade'], m, a, dt))
                    conn.commit()
                    st.success("Done!")
                    msg = urllib.parse.quote(f"🎓 *SMART CLASS*\nReceipt for {s['name']}\nMonth: {m}\nAmount: Rs.{a}\nStatus: Received")
                    st.markdown(f"[📲 Send WhatsApp](https://wa.me/{s['whatsapp']}?text={msg})")

    elif choice == "📊 Records":
        st.subheader("Records Management")
        tab1, tab2 = st.tabs(["Students", "Payments"])
        with tab1:
            st.dataframe(pd.read_sql("SELECT * FROM students", conn), use_container_width=True)
        with tab2:
            st.dataframe(pd.read_sql("SELECT * FROM payments", conn), use_container_width=True)
