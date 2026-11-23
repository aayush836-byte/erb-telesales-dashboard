import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="ERB Pvt. Ltd. | Outbound Tele-Sales Dashboard",
    page_icon="📞",
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
    st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>📞 ERB Pvt. Ltd. (Policysafe Process)</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: #475569;'>Outbound Tele-Sales Analytics & Lead Qualification System</h4>", unsafe_allow_html=True)
    st.divider()
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.subheader("🔐 Floor Executive / TL Login")
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
        
        st.info("**Demo Credentials:**\n- Executive: `aayush` / `asb2024`\n- Team Leader: `fardeen` / `erb123`")

# --- MAIN APPLICATION ---
def main_app():
    # Sidebar Navigation
    with st.sidebar:
        st.markdown("### 🏢 ERB Pvt. Ltd. Noida")
        st.caption("Campaign: ABSLI Nishchit Aayush & Health")
        st.success(f"👤 **{st.session_state.user_info['name']}**\n\nRole: `{st.session_state.user_info['role']}`")
        st.divider()
        
        menu = st.radio(
            "Navigation Menu",
            [
                "📊 1. SIP Analytics Dashboard",
                "📝 2. Log Outbound Call (Input)",
                "📋 3. Lead & Callback Queue (Output)",
                "🛡️ 4. TRAI DND Scrubbing Tool"
            ]
        )
        st.divider()
        if st.button("🚪
