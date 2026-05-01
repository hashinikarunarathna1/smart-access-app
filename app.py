import streamlit as st
import pandas as pd
import sqlite3
import urllib.parse
from datetime import datetime

# --- CONFIG & STYLING ---
st.set_page_config(page_title="Smart Class Management", page_icon="🎓", layout="wide")

# CSS Styling (ඔයාගේ Screenshot එකේ තිබුණු විදිහට)
st.markdown("""
    <style>
    .stButton>button {
        width: 100%; border-radius: 8px; height: 3.5em;
        background-color: #1a73e8; color: white; font-weight: bold; border: none;
    }
    .receipt-container {
        background-color: #f8faff; border: 2px solid #1a73e8; border-radius: 20px;
        padding: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('payments.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS payments 
                 (student_name TEXT, month TEXT, amount REAL, date TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- APP UI ---
st.title("Smart Class - Payment Gateway")

student_name = st.text_input("Search Student Name")
if student_name:
    st.info(f"ශිෂ්‍යයා: {student_name} (Grade 6)")

month = st.selectbox("Month", ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"])
amount = st.number_input("Amount (Rs.)", min_value=0.0, step=100.0)

if st.button("Generate & Save Payment"):
    if student_name and amount > 0:
        # Database එකට සේව් කිරීම
        conn = sqlite3.connect('payments.db')
        c = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO payments VALUES (?, ?, ?, ?)", (student_name, month, amount, now))
        conn.commit()
        conn.close()
        
        st.success("ගෙවීම් සාර්ථකව සටහන් කළා!")

        # --- WHATSAPP RECEIPT LOGIC ---
        message = f"🎓 *Smart Class - Payment Receipt*\n\n👤 *Student:* {student_name}\n📅 *Month:* {month}\n💰 *Amount:* Rs.{amount}\n✅ *Status:* Paid\n⏰ *Date:* {now}"
        encoded_message = urllib.parse.quote(message)
        whatsapp_url = f"https://wa.me/?text={encoded_message}"

        # WhatsApp Button එක පෙන්වීම
        st.markdown(f'''
            <div class="receipt-container">
                <p style="text-align: center; font-weight: bold;">දැන් ඔබට රිසිට් පත WhatsApp කළ හැක:</p>
                <a href="{whatsapp_url}" target="_blank" style="text-decoration: none;">
                    <button style="background-color: #25D366; color: white; border: none; padding: 15px 20px; border-radius: 10px; cursor: pointer; width: 100%; font-size: 16px;">
                         WhatsApp Receipt එක යවන්න ✅
                    </button>
                </a>
            </div>
        ''', unsafe_allow_html=True)
    else:
        st.error("කරුණාකර ශිෂ්‍යයාගේ නම සහ මුදල නිවැරදිව ඇතුළත් කරන්න.")

# Logo එක පෙන්වීම
st.image("https://raw.githubusercontent.com/Sajan-S/Smart-Class/main/logo.png", width=250)
