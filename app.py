import streamlit as st
import pandas as pd
import sqlite3
import urllib.parse
from datetime import datetime
import plotly.express as px

# --- CONFIG & STYLING ---
st.set_page_config(page_title="Smart Class Management", page_icon="🎓", layout="wide")

# CSS Styling
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stButton>button {
        width: 100%; border-radius: 8px; height: 3.5em;
        background-color: #1a73e8; color: white; font-weight: bold; border: none;
    }
    .receipt-container {
        background-color: #1e293b; border: 2px solid #1a73e8; border-radius: 20px;
        padding: 20px; margin-top: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('smart_class.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS payments 
                 (student_name TEXT, month TEXT, amount REAL, date TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("Smart Class Menu")
page = st.sidebar.radio("Go to", ["Payment Gateway", "Dashboard & Analytics", "View History"])

# --- PAGE 1: PAYMENT GATEWAY ---
if page == "Payment Gateway":
    st.title("💳 Payment Gateway")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        student_name = st.text_input("Search Student Name")
        month = st.selectbox("Month", ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"])
        amount = st.number_input("Amount (Rs.)", min_value=0.0, step=100.0)

        if st.button("Generate & Save Payment"):
            if student_name and amount > 0:
                # Save to Database
                conn = sqlite3.connect('smart_class.db')
                c = conn.cursor()
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                c.execute("INSERT INTO payments VALUES (?, ?, ?, ?)", (student_name, month, amount, now))
                conn.commit()
                conn.close()
                
                st.success(f"{student_name} ගේ {month} මාසයේ ගෙවීම් සටහන් කළා!")

                # WhatsApp Logic
                message = f"🎓 *Smart Class - Payment Receipt*\n\n👤 *Student:* {student_name}\n📅 *Month:* {month}\n💰 *Amount:* Rs.{amount}\n✅ *Status:* Paid\n⏰ *Date:* {now}"
                encoded_message = urllib.parse.quote(message)
                whatsapp_url = f"https://wa.me/?text={encoded_message}"

                st.markdown(f'''
                    <div class="receipt-container">
                        <p style="text-align: center; color: white;">ගෙවීම් සටහන් සාර්ථකයි! පහත බටන් එකෙන් රිසිට් එක යවන්න.</p>
                        <a href="{whatsapp_url}" target="_blank" style="text-decoration: none;">
                            <button style="background-color: #25D366; color: white; border: none; padding: 15px 20px; border-radius: 10px; cursor: pointer; width: 100%; font-size: 16px;">
                                 WhatsApp Receipt එක යවන්න ✅
                            </button>
                        </a>
                    </div>
                ''', unsafe_allow_html=True)
            else:
                st.error("කරුණාකර විස්තර නිවැරදිව ඇතුළත් කරන්න.")

    with col2:
        st.image("https://raw.githubusercontent.com/Sajan-S/Smart-Class/main/logo.png", use_column_width=True)

# --- PAGE 2: DASHBOARD & ANALYTICS ---
elif page == "Dashboard & Analytics":
    st.title("📊 Class Analytics")
    
    conn = sqlite3.connect('smart_class.db')
    df = pd.read_sql_query("SELECT * FROM payments", conn)
    conn.close()

    if not df.empty:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Payments", len(df))
        col2.metric("Total Income", f"Rs. {df['amount'].sum()}")
        col3.metric("This Month", df[df['month'] == datetime.now().strftime("%B")]['amount'].sum())

        # Chart
        fig = px.bar(df, x='month', y='amount', title="Income by Month", color_discrete_sequence=['#1a73e8'])
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("තවමත් දත්ත ඇතුළත් කර නැත.")

# --- PAGE 3: VIEW HISTORY ---
elif page == "View History":
    st.title("📜 Payment History")
    
    conn = sqlite3.connect('smart_class.db')
    df = pd.read_sql_query("SELECT * FROM payments ORDER BY date DESC", conn)
    conn.close()

    if not df.empty:
        st.dataframe(df, use_container_width=True)
        
        # CSV Download
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download History as CSV", data=csv, file_name="payment_history.csv", mime="text/csv")
    else:
        st.info("ඉතිහාසය බැලීමට දත්ත කිසිවක් නැත.")
