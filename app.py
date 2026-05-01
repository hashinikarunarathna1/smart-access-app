# --- REPORTS ---
    elif choice == "📊 Reports":
        st.title("Reports Management")
        t1, t2, t3, t4 = st.tabs(["Student List", "Payment Records", "🔴 Arrears List", "🗑️ Delete Records"])
        
        with t1:
            # (පරණ කෝඩ් එක මෙතන තියෙනවා)
            df_std = pd.read_sql("SELECT * FROM students", conn)
            if not df_std.empty:
                for g in df_std['grade'].unique():
                    with st.expander(f"📂 {g} - Students", expanded=False):
                        st.table(df_std[df_std['grade'] == g][['id', 'name', 'school', 'whatsapp']])
        
        with t2:
            # (පරණ කෝඩ් එක මෙතන තියෙනවා)
            df_pay = pd.read_sql("SELECT * FROM payments", conn)
            if not df_pay.empty:
                for g in df_pay['grade'].unique():
                    with st.expander(f"💰 {g} - Payment Records", expanded=False):
                        st.table(df_pay[df_pay['grade'] == g][['id', 'student_name', 'month', 'amount', 'date']])

        # --- අලුතින් එකතු කළ ARREARS LIST කොටස ---
        with t3:
            st.subheader("Check Unpaid Students")
            check_month = st.selectbox("Select Month to Check", ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"], key="check_arrears")
            check_grade = st.selectbox("Select Grade", ["Grade 6", "Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Revision", "Theory"], key="check_grade_arr")
            
            if st.button("Show Arrears List"):
                # සියලුම ශිෂ්‍යයන් ලබා ගැනීම
                all_students = pd.read_sql(f"SELECT name, whatsapp FROM students WHERE grade='{check_grade}'", conn)
                # ගෙවීම් කළ ශිෂ්‍යයන් ලබා ගැනීම
                paid_students = pd.read_sql(f"SELECT student_name FROM payments WHERE month='{check_month}' AND grade='{check_grade}'", conn)
                
                if not all_students.empty:
                    # ගෙවීම් නොකළ අය වෙන් කර ගැනීම
                    paid_list = paid_students['student_name'].tolist()
                    arrears_df = all_students[~all_students['name'].isin(paid_list)]
                    
                    if not arrears_df.empty:
                        st.warning(f"⚠️ {check_month} මාසය සඳහා {check_grade} පන්තියේ ගෙවීම් නොකළ සිසුන් {len(arrears_df)} දෙනෙකු සිටී.")
                        st.table(arrears_df)
                        
                        # WhatsApp Reminder එකක් යැවීමට පහසුකම (විකල්ප)
                        for index, row in arrears_df.iterrows():
                            remind_msg = f"Hi {row['name']}, this is a reminder for your Smart Class {check_month} payment. Please settle it soon."
                            encoded_remind = urllib.parse.quote(remind_msg)
                            # මෙතනින් එක් එක් ශිෂ්‍යයාට වෙන වෙනම මැසේජ් යවන්න ලින්ක් එකක් දෙන්න පුළුවන්
                    else:
                        st.success(f"✅ {check_grade} පන්තියේ සියලුම සිසුන් {check_month} මාසය සඳහා ගෙවීම් කර ඇත.")
                else:
                    st.info("මෙම පන්තියේ ශිෂ්‍යයන් ලියාපදිංචි කර නැත.")

        with t4:
            # (Delete records කොටස මෙතන තියෙනවා)
            col1, col2 = st.columns(2)
            # ... (පරණ කෝඩ් එක)
