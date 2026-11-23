import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="ERB Pvt. Ltd. | Outbound Tele-Sales Dashboard",
    layout="wide"
)

# --- DATABASE SETUP (SQLite) ---
DB_FILE = "erb_telesales.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Table 1: Users (For Role-Based Login)
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password TEXT,
                    role TEXT,
                    full_name TEXT
                )''')
    
    # Table 2: Weekly Historical Data (From Aayush's 13-Week SIP Report)
    c.execute('''CREATE TABLE IF NOT EXISTS weekly_summary (
                    week_no TEXT PRIMARY KEY,
                    date_range TEXT,
                    work_days INTEGER,
                    total_dials INTEGER,
                    qualified_transfers INTEGER,
                    phase TEXT
                )''')
    
    # Table 3: Live Call & Lead Logs (Input/Output Operations)
    c.execute('''CREATE TABLE IF NOT EXISTS live_call_logs (
                    call_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_name TEXT,
                    phone_number TEXT,
                    age INTEGER,
                    occupation TEXT,
                    product_pitched TEXT,
                    disposition_code TEXT,
                    callback_slot TEXT,
                    logged_by TEXT,
                    timestamp TEXT
                )''')
    
    # Table 4: DND Suppression List (TRAI Compliance)
    c.execute('''CREATE TABLE IF NOT EXISTS dnd_registry (
                    phone_number TEXT PRIMARY KEY,
                    reason TEXT
                )''')

    # Seed Default Users
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        users_data = [
            ("aayush", "asb2024", "Tele-Sales Executive", "Aayush Mishra (ASB/BCA/24/057)"),
            ("fardeen", "erb123", "Team Leader", "Mr. Fardeen Arif (TL)")
        ]
        c.executemany("INSERT INTO users VALUES (?, ?, ?, ?)", users_data)

    # Seed 13-Week SIP Historical Data
    c.execute("SELECT COUNT(*) FROM weekly_summary")
    if c.fetchone()[0] == 0:
        sip_weeks = [
            ("W1", "25 May - 30 May", 6, 1158, 7, "Phase 1: Onboarding"),
            ("W2", "01 Jun - 06 Jun", 6, 1344, 7, "Phase 1: Onboarding"),
            ("W3", "08 Jun - 13 Jun", 5, 1117, 7, "Phase 1: Onboarding"),
            ("W4", "15 Jun - 20 Jun", 6, 1923, 6, "Phase 1: Onboarding"),
            ("W5", "22 Jun - 27 Jun", 6, 1680, 7, "Phase 1: Onboarding"),
            ("W6", "29 Jun - 30 Jun", 2, 612, 3, "Phase 2: Consolidation"),
            ("W7", "01 Jul - 04 Jul", 4, 1114, 4, "Phase 2: Consolidation"),
            ("W8", "06 Jul - 11 Jul", 6, 1517, 8, "Phase 2: Consolidation"),
            ("W9", "13 Jul - 18 Jul", 4, 1244, 4, "Phase 2: Consolidation"),
            ("W10", "20 Jul - 25 Jul", 6, 1658, 6, "Phase 2: Consolidation"),
            ("W11", "27 Jul - 01 Aug", 6, 1414, 5, "Phase 3: Optimization"),
            ("W12", "03 Aug - 08 Aug", 6, 1461, 11, "Phase 3: Optimization"),
            ("W13", "10 Aug - 15 Aug", 6, 1136, 7, "Phase 3: Optimization"),
        ]
        c.executemany("INSERT INTO weekly_summary VALUES (?, ?, ?, ?, ?, ?)", sip_weeks)

    # Seed Sample Live Call Logs & DND Numbers
    c.execute("SELECT COUNT(*) FROM live_call_logs")
    if c.fetchone()[0] == 0:
        sample_logs = [
            ("Rajesh Sharma", "9811223344", 36, "Salaried", "ABSLI Nishchit Aayush", "QUAL-TR (Qualified Transfer)", "Transferred Now", "Aayush Mishra", "2026-08-05 11:20:00"),
            ("Priya Verma", "9876543210", 31, "Self-Employed", "Retail Health Floater", "CB (Callback Requested)", "Saturday 11:00 AM", "Aayush Mishra", "2026-08-06 15:40:00"),
            ("Amitabh Tiwari", "9910011223", 42, "Salaried", "ABSLI Nishchit Aayush", "QUAL-TR (Qualified Transfer)", "Transferred Now", "Aayush Mishra", "2026-08-07 12:15:00"),
            ("Neha Kapoor", "9818877665", 29, "Salaried", "Retail Health Floater", "NI (Not Interested)", "None", "Aayush Mishra", "2026-08-08 16:10:00"),
            ("Suresh Gupta", "9711445566", 48, "Business", "ABSLI Nishchit Aayush", "CB (Callback Requested)", "Saturday 03:00 PM", "Aayush Mishra", "2026-08-08 16:45:00"),
        ]
        c.executemany("INSERT INTO live_call_logs (customer_name, phone_number, age, occupation, product_pitched, disposition_code, callback_slot, logged_by, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", sample_logs)
        
        c.executemany("INSERT INTO dnd_registry VALUES (?, ?)", [
            ("9999999999", "TRAI National DND Registry"),
            ("8888888888", "Customer Requested Opt-Out")
        ])

    conn.commit()
    conn.close()

init_db()

# --- AUTHENTICATION STATE ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_info = None

def login_screen():
    st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>ERB Pvt. Ltd. (Policysafe Process)</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: #475569;'>Outbound Tele-Sales Analytics & Lead Qualification System</h4>", unsafe_allow_html=True)
    st.divider()
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.subheader("Floor Executive / TL Login")
        username = st.text_input("Username", placeholder="Enter username (e.g., aayush)")
        password = st.text_input("Password", type="password", placeholder="Enter password")
        
        if st.button("Login to Floor Portal", use_container_width=True, type="primary"):
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT username, role, full_name FROM users WHERE username=? AND password=?", (username.strip(), password.strip()))
            user = c.fetchone()
            conn.close()
            
            if user:
                st.session_state.logged_in = True
                st.session_state.user_info = {"username": user[0], "role": user[1], "name": user[2]}
                st.rerun()
            else:
                st.error("Invalid Credentials! Try: aayush / asb2024 or fardeen / erb123")
        
        st.info("Demo Credentials:\n- Executive: aayush / asb2024\n- Team Leader: fardeen / erb123")

# --- MAIN APPLICATION ---
def main_app():
    with st.sidebar:
        st.markdown("### ERB Pvt. Ltd. Noida")
        st.caption("Campaign: ABSLI Nishchit Aayush & Health")
        st.success(f"User: **{st.session_state.user_info['name']}**\n\nRole: `{st.session_state.user_info['role']}`")
        st.divider()
        
        menu = st.radio(
            "Navigation Menu",
            [
                "1. SIP Analytics Dashboard",
                "2. Log Outbound Call (Input)",
                "3. Lead & Callback Queue (Output)",
                "4. TRAI DND Scrubbing Tool"
            ]
        )
        st.divider()
        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_info = None
            st.rerun()

    conn = sqlite3.connect(DB_FILE)
    df_weekly = pd.read_sql_query("SELECT * FROM weekly_summary", conn)
    df_live = pd.read_sql_query("SELECT * FROM live_call_logs ORDER BY call_id DESC", conn)
    conn.close()

    extra_dials = len(df_live) - 5
    extra_transfers = len(df_live[df_live["disposition_code"].str.contains("QUAL-TR")]) - 2
    
    total_dials = int(df_weekly["total_dials"].sum()) + max(0, extra_dials)
    total_transfers = int(df_weekly["qualified_transfers"].sum()) + max(0, extra_transfers)
    efficiency = (total_transfers / total_dials) * 100 if total_dials > 0 else 0

    # --- MODULE 1: ANALYTICS DASHBOARD ---
    if menu == "1. SIP Analytics Dashboard":
        st.title("Outbound Tele-Sales Performance Analytics")
        st.caption("Empirical Dataset: 13 Operational Weeks (24 May 2026 - 25 Aug 2026) | Shift: 10:00 AM - 6:00 PM")

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Outbound Dials", f"{total_dials:,}", "+251.9 Avg/Shift")
        k2.metric("Qualified Transfers (QUAL-TR)", f"{total_transfers}", "Peak: 11 in W12")
        k3.metric("Dial-to-Transfer Efficiency", f"{efficiency:.2f}%", "+0.57% in Phase 3")
        k4.metric("Confirmed Policies (NOP)", "2 Policies", "2.44% Closure Yield")

        st.divider()

        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Weekly Outbound Dialing Volume (W1-W13)")
            fig_dials = px.bar(
                df_weekly, x="week_no", y="total_dials", color="phase",
                text="total_dials", labels={"week_no": "Week", "total_dials": "Total Dials"},
                color_discrete_sequence=["#1E3A8A", "#2563EB", "#0D9488"]
            )
            fig_dials.update_traces(textposition="outside")
            st.plotly_chart(fig_dials, use_container_width=True)

        with c2:
            st.subheader("Weekly Qualified Lead Transfers (W1-W13)")
            fig_trans = px.line(
                df_weekly, x="week_no", y="qualified_transfers", markers=True,
                text="qualified_transfers", labels={"week_no": "Week", "qualified_transfers": "Transfers"}
            )
            fig_trans.update_traces(line_color="#D97706", line_width=3, textposition="top center")
            st.plotly_chart(fig_trans, use_container_width=True)

        c3, c4 = st.columns(2)
        with c3:
            st.subheader("Funnel Call Disposition Breakdown (17,378 Calls)")
            disp_data = pd.DataFrame({
                "Disposition": ["RNA (Ring No Answer)", "SWO (Switched Off)", "CUT (Immediate Hang-Up)", "NI (Not Interested)", "CB (Callback)", "QUAL-TR (Transfer)"],
                "Count": [8133, 3371, 2867, 1946, 979, 82]
            })
            fig_pie = px.pie(disp_data, names="Disposition", values="Count", hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)

        with c4:
            st.subheader("Product-Wise Qualified Transfers Split")
            prod_data = pd.DataFrame({
                "Product Campaign": ["ABSLI Nishchit Aayush (Guaranteed Income)", "Retail Health Insurance (Individual & Floater)"],
                "Transfers": [51, 31]
            })
            fig_prod = px.bar(
                prod_data, x="Product Campaign", y="Transfers", text="Transfers",
                color="Product Campaign", color_discrete_sequence=["#1E3A8A", "#B45309"]
            )
            fig_prod.update_traces(textposition="outside")
            st.plotly_chart(fig_prod, use_container_width=True)

    # --- MODULE 2: LIVE CALL ENTRY (INPUT) ---
    elif menu == "2. Log Outbound Call (Input)":
        st.title("Log New Outbound Call & Lead Qualification")
        st.write("Enter prospect details post-call. System automatically checks TRAI DND status and updates KPI metrics.")

        with st.form("call_entry_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                cust_name = st.text_input("Prospect Full Name *", placeholder="e.g., Vikram Malhotra")
                phone = st.text_input("10-Digit Mobile Number *", max_chars=10, placeholder="e.g., 9811002233")
                age = st.number_input("Prospect Age (Years) *", min_value=18, max_value=75, value=34)
            with col2:
                occupation = st.selectbox("Occupation Profile", ["Salaried", "Self-Employed / Business", "Professional", "Retired"])
                product = st.selectbox("Insurance Product Pitched", ["ABSLI Nishchit Aayush", "Retail Health Floater"])
                disposition = st.selectbox(
                    "Call Disposition Code *",
                    [
                        "QUAL-TR (Qualified Transfer)",
                        "CB (Callback Requested)",
                        "NI (Not Interested)",
                        "RNA (Ring No Answer)",
                        "SWO (Switched Off)",
                        "CUT (Immediate Hang-Up)"
                    ]
                )
            callback_slot = st.text_input("Preferred Callback Slot (If CB selected)", placeholder="e.g., Saturday 11:30 AM or None")
            submitted = st.form_submit_button("Save Call Record to Database", type="primary")

            if submitted:
                if not cust_name.strip():
                    st.error("Validation Error: Customer Name cannot be empty.")
                elif not (phone.isdigit() and len(phone) == 10):
                    st.error("Validation Error: Enter a valid 10-digit numeric mobile number.")
                elif "QUAL-TR" in disposition and not (23 <= age <= 60):
                    st.warning("Eligibility Alert: Qualified Transfer age bracket for ABSLI/Health campaign is 23-60 years.")
                else:
                    conn = sqlite3.connect(DB_FILE)
                    c = conn.cursor()
                    c.execute("SELECT reason FROM dnd_registry WHERE phone_number=?", (phone,))
                    dnd_hit = c.fetchone()

                    if dnd_hit:
                        st.error(f"TRAI COMPLIANCE BLOCK: Number {phone} is listed in DND Registry ({dnd_hit[0]}). Call suppressed!")
                    else:
                        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        c.execute(
                            "INSERT INTO live_call_logs (customer_name, phone_number, age, occupation, product_pitched, disposition_code, callback_slot, logged_by, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (cust_name.strip(), phone, age, occupation, product, disposition, callback_slot or "None", st.session_state.user_info["name"], ts)
                        )
                        conn.commit()
                        st.success(f"Call record for **{cust_name}** ({disposition}) saved successfully! Dashboard KPIs updated.")
                    conn.close()

    # --- MODULE 3: LEAD & CALLBACK QUEUE (OUTPUT) ---
    elif menu == "3. Lead & Callback Queue (Output)":
        st.title("Qualified Transfers & Saturday Callback Queue")
        
        filter_choice = st.selectbox(
            "Filter Records by Disposition:",
            ["All Logged Calls", "QUAL-TR (Qualified Transfer)", "CB (Callback Requested)", "NI (Not Interested)"]
        )

        if filter_choice != "All Logged Calls":
            filtered_df = df_live[df_live["disposition_code"] == filter_choice]
        else:
            filtered_df = df_live

        st.dataframe(filtered_df, use_container_width=True, hide_index=True)

        csv_data = filtered_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Filtered Report (CSV)",
            data=csv_data,
            file_name="ERB_TeleSales_Report.csv",
            mime="text/csv"
        )

    # --- MODULE 4: DND SCRUBBING TOOL ---
    elif menu == "4. TRAI DND Scrubbing Tool":
        st.title("TRAI DND Compliance & Number Scrubbing")
        st.write("Verify prospect phone numbers against the DND suppression table before dialing.")

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Check / Add DND Number")
            dnd_num = st.text_input("Enter 10-Digit Number to Suppress", max_chars=10)
            dnd_reason = st.selectbox("Suppression Reason", ["TRAI National DND Registry", "Customer Requested Opt-Out", "Invalid / Disconnected Number"])
            if st.button("Add to DND Blocklist"):
                if dnd_num.isdigit() and len(dnd_num) == 10:
                    conn = sqlite3.connect(DB_FILE)
                    c = conn.cursor()
                    c.execute("INSERT OR REPLACE INTO dnd_registry VALUES (?, ?)", (dnd_num, dnd_reason))
                    conn.commit()
                    conn.close()
                    st.success(f"Number {dnd_num} added to DND suppression list.")
                else:
                    st.error("Please enter a valid 10-digit number.")

        with col2:
            st.subheader("Current Suppressed Numbers")
            conn = sqlite3.connect(DB_FILE)
            df_dnd = pd.read_sql_query("SELECT * FROM dnd_registry", conn)
            conn.close()
            st.dataframe(df_dnd, use_container_width=True, hide_index=True)

# --- ROUTING ---
if st.session_state.logged_in:
    main_app()
else:
    login_screen()
