st.markdown("""
    <style>
    /* මුළු ඇප් එකේම අකුරු වල පාට පාලනය කිරීම */
    html, body, [class*="View"] {
        color: inherit; /* System theme එකේ අකුරු පාට ගන්නවා */
    }

    /* Metric Boxes (Dashboard එකේ කොටු) */
    [data-testid="stMetric"] {
        background-color: rgba(255, 255, 255, 0.05) !important; /* පොඩි විනිවිද පෙනෙන ස්වභාවයක් */
        padding: 20px !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
        border: 1px solid rgba(128, 128, 128, 0.2);
    }

    /* බොත්තම් වල පාට */
    .stButton>button {
        width: 100%; border-radius: 8px; height: 3.5em;
        background-color: #1a73e8; color: white !important; /* මෙතන අකුරු සුදුම වෙනවා */
        font-weight: bold; border: none;
    }

    /* රිසිට් එකේ විස්තර */
    .receipt-container {
        background-color: rgba(26, 115, 232, 0.05); /* සැහැල්ලු නිල් පාටක් */
        border: 2px solid #1a73e8; border-radius: 20px;
        padding: 40px; margin: 20px auto; max-width: 800px;
        font-family: 'Courier New', Courier, monospace;
    }
    
    .receipt-title { 
        color: #1a73e8; font-size: 32px; font-weight: bold; text-align: center; 
    }

    /* Table වල අකුරු පෙනීම වැඩි කිරීමට */
    .stDataFrame, .stTable {
        background-color: transparent !important;
    }
    </style>
    """, unsafe_allow_html=True)
