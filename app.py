# --- CONFIG & STYLING ---
st.set_page_config(page_title="Smart Class Management", page_icon="🎓", layout="wide")

st.markdown("""
    <style>
    /* පසුබිම */
    .main { background-color: #f4f7f6; }
    
    /* Metrics කොටු සහ ඒ ඇතුළේ අකුරු වල පාට ස්ථාවර කිරීම */
    [data-testid="stMetric"] {
        background-color: #ffffff !important;
        padding: 20px !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
    }
    
    /* Label එක (උදා: Total Students) කළු පාට කිරීම */
    [data-testid="stMetricLabel"] {
        color: #1e293b !important;
        font-weight: bold !important;
    }
    
    /* Value එක (උදා: 1, 1300.00) තද නිල් පාට කිරීම */
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
