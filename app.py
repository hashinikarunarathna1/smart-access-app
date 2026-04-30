import streamlit as st
import pandas as pd
import sqlite3
import urllib.parse
from datetime import datetime

# --- CONFIG & STYLING ---
# පේජ් එකේ සැකසුම් (මෙය සැමවිටම මුලින්ම තිබිය යුතුය)
st.set_page_config(page_title="Smart Class Management", page_icon="🎓", layout="wide")

st.markdown("""
    <style>
    /* Dark Mode සහ Light Mode දෙකටම ගැලපෙන ලෙස Overview කොටු සැකසීම */
    [data-testid="stMetric"] {
        background-color: #ffffff !important;
        padding: 20px !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
    }
    
    /* Label (අකුරු) කළු පාට කිරීම */
    [data-testid="stMetricLabel"] {
        color: #1e293b !important;
        font-weight: bold !important;
    }
    
    /* Value (සංඛ්‍යා) තද නිල් පාට කිරීම */
    [data-testid="stMetricValue"] {
        color: #1a73e8 !important;
    }

    /* බොත්තම් වල පෙනුම */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3.5em;
        background-color: #1a73e8;
        color: white;
        font-weight: bold;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #1557b0;
        transform: translateY(-2px);
    }
    </style>
    """, unsafe_allow_html=True)

# --- DATABASE ENGINE ---
def get_connection():
    return sqlite3.connect("smart_class_v10.db", check_same_thread=False)

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
                st.error("වැරදි පරිශීලක නාමයක් හෝ මුරපදයක්!")
else:
    # --- SIDEBAR ---
    st.sidebar.title("💎 Smart Class Pro")
    choice = st.sidebar.radio("Main Menu", ["🚀 Dashboard", "📝 Registration", "💰 Payments", "📊 Reports"])
    
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

    conn = get_connection()

    # --- DASHBOARD ---
    if choice == "🚀 Dashboard":
        st.markdown("<h1 style='color: #1a73e8;'>Overview</h1>", unsafe_allow_html=True)
        
        total_students = pd.read_sql("SELECT COUNT(*) FROM students", conn).iloc[0,0]
        total_revenue = pd.read_sql("SELECT SUM(amount) FROM payments", conn).iloc[0,0] or 0
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Students", total_students)
        m2.metric("Total Revenue", f"Rs. {total_revenue:,.2f}")
        m3.metric("Status", "Active")
        
        st.markdown("---")
        st.subheader("Quick Actions")
        q1, q2 = st.columns(2)
        if q1.button("Register New Student"):
            st.info("Side Menu එකෙන් Registration තෝරන්න.")
        if q2.button("Record a Payment"):
            st.info("Side Menu එකෙන් Payments තෝරන්න.")

    # --- REGISTRATION ---
    elif choice == "📝 Registration":
        st.title("Student Enrollment")
        with st.expander("Add New Student", expanded=True):
            name = st.text_input("Student Full Name")
            school = st.text_input("School")
            grade = st.text_input("Grade")
            wa = st.text_input("WhatsApp Number (94...)")
            
            if st.button("Confirm Enrollment"):
                if name and wa:
                    conn.execute("INSERT INTO students (name, school, grade, whatsapp) VALUES (?,?,?,?)", (name, school, grade, wa))
                    conn.commit()
                    st.success(f"{name} සාර්ථකව ලියාපදිංචි කළා!")

    # --- PAYMENTS ---
    elif choice == "💰 Payments":
        st.title("Payment Gateway")
        search_name = st.text_input("Search Student Name").strip()
        
        if search_name:
            results = pd.read_sql(f"SELECT * FROM students WHERE name LIKE '%{search_name}%'", conn)
            if not results.empty:
                student = results.iloc[0]
                st.success(f"Selected: {student['name']}")
                month = st.selectbox("Select Month", ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"])
                amount = st.number_input("Amount (Rs.)", min_value=0.0)
                
                if st.button("Process Payment & Send Receipt"):
                    today = datetime.now().strftime("%Y-%m-%d")
                    conn.execute("INSERT INTO payments (student_name, grade, month, amount, date) VALUES (?,?,?,?,?)", (student['name'], student['grade'], month, amount, today))
                    conn.commit()
                    msg = f"🎓 *SMART CLASS RECEIPT*\n\nName: {student['name']}\nMonth: {month}\nAmount: Rs.{amount:,.2f}\nDate: {today}"
                    url = f"https://wa.me/{student['whatsapp']}?text={urllib.parse.quote(msg)}"
                    st.markdown(f'<a href="{url}" target="_blank" style="text-decoration:none;"><div style="background-color:#25d366;color:white;padding:10px;text-align:center;border-radius:5px;">Send WhatsApp Receipt</div></a>', unsafe_allow_html=True)

    # --- REPORTS ---
    elif choice == "📊 Reports":
        st.title("Records")
        t1, t2 = st.tabs(["Students", "Payments"])
        with t1:
            st.dataframe(pd.read_sql("SELECT name, school, grade, whatsapp FROM students", conn), use_container_width=True)
        with t2:
            st.dataframe(pd.read_sql("SELECT * FROM payments", conn), use_container_width=True)
