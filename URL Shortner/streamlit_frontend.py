import streamlit as st
import requests
from datetime import datetime
import base64
from PIL import Image
import io
import pytz

# Set timezone to IST
IST = pytz.timezone('Asia/Kolkata')

API_BASE = "http://localhost:8000"

# Initialize session state for authentication
if 'auth_token' not in st.session_state:
    st.session_state.auth_token = None
if 'username' not in st.session_state:
    st.session_state.username = None

st.title("🔗 URL Shortener")

# Authentication Section
def login_user(username, password):
    try:
        response = requests.post(
            f"{API_BASE}/token",
            data={"username": username, "password": password}
        )
        if response.status_code == 200:
            token_data = response.json()
            st.session_state.auth_token = token_data["access_token"]
            st.session_state.username = username
            return True
        return False
    except Exception as e:
        st.error(f"Login error: {str(e)}")
        return False

def register_user(username, password):
    try:
        response = requests.post(
            f"{API_BASE}/register",
            json={"username": username, "password": password}
        )
        if response.status_code == 200:
            st.success("Registration successful! Please login.")
            return True
        st.error(response.json().get("detail", "Registration failed"))
        return False
    except Exception as e:
        st.error(f"Registration error: {str(e)}")
        return False

# Authentication UI
if not st.session_state.auth_token:
    st.subheader("👤 Authentication")
    auth_tab1, auth_tab2 = st.tabs(["Login", "Register"])
    
    with auth_tab1:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Login")
            if submit_login:
                if login_user(username, password):
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Login failed. Please check your credentials.")

    with auth_tab2:
        with st.form("register_form"):
            new_username = st.text_input("Username")
            new_password = st.text_input("Password", type="password")
            submit_register = st.form_submit_button("Register")
            if submit_register:
                if register_user(new_username, new_password):
                    st.success("Registration successful! Please login.")
else:
    # Authenticated user interface
    st.sidebar.success(f"Logged in as {st.session_state.username}")
    if st.sidebar.button("Logout"):
        st.session_state.auth_token = None
        st.session_state.username = None
        st.rerun()

    # --- URL Shortening Form ---
    st.subheader("🔗 Shorten a URL")
    with st.form("shorten_form"):
        long_url = st.text_input("Enter the long URL")
        col1, col2 = st.columns(2)
        with col1:
            custom_code = st.text_input("Custom short code (optional)")
            expires_at = st.date_input("Expiry Date (optional)", value=None)
        with col2:
            expiry_minutes = st.number_input("Expiry in minutes (optional)", min_value=0, value=0)
            st.write("Leave both expiry fields empty for no expiration")

        submit_shorten = st.form_submit_button("Shorten URL")
        if submit_shorten:
            headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
            payload = {"long_url": long_url}
            
            if custom_code:
                payload["custom_code"] = custom_code
            if expires_at:
                # Combine date with minimum time and set IST timezone
                expires_at_datetime = IST.localize(datetime.combine(expires_at, datetime.min.time()))
                payload["expires_at"] = expires_at_datetime.isoformat()
            if expiry_minutes > 0:
                payload["expiry_minutes"] = str(expiry_minutes)  # Convert to string for JSON serialization

            try:
                response = requests.post(f"{API_BASE}/shorten", json=payload, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    st.success(f"Shortened URL: {data['short_url']}")
                    
                    # Display QR Code if available
                    if 'qr_code' in data:
                        qr_image = Image.open(io.BytesIO(base64.b64decode(data['qr_code'])))
                        st.image(qr_image, caption="Scan QR Code")
                    
                    st.markdown(f"Click to test: [{data['short_url']}]({data['short_url']})")
                else:
                    st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
            except Exception as e:
                st.error(f"Error creating short URL: {str(e)}")

    # --- Analytics Section ---
    st.subheader("� URL Analytics")
    
    tab1, tab2 = st.tabs(["Quick Analytics", "Detailed Analytics"])
    
    with tab1:
        short_code = st.text_input("Enter short code")
        if st.button("Get Analytics"):
            try:
                headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
                response = requests.get(f"{API_BASE}/analytics/{short_code}", headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Basic Info
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Total Clicks", data['analytics']['total_clicks'])
                        st.metric("Unique Visitors", data['analytics']['unique_visitors'])
                    with col2:
                        st.metric("Last 24h Clicks", data['analytics']['last_24h_clicks'])
                        st.metric("Last 7d Clicks", data['analytics']['last_7d_clicks'])
                    
                    # URL Details
                    st.write("### URL Details")
                    st.write(f"🔗 Long URL: {data['long_url']}")
                    # Convert datetime strings to IST
                    created_at = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00')).astimezone(IST)
                    st.write(f"📅 Created: {created_at.strftime('%Y-%m-%d %I:%M:%S %p %Z')}")
                    
                    if data['expires_at']:
                        expires_at = datetime.fromisoformat(data['expires_at'].replace('Z', '+00:00')).astimezone(IST)
                        st.write(f"⏳ Expires: {expires_at.strftime('%Y-%m-%d %I:%M:%S %p %Z')}")
                    
                    st.write(f"Status: {data['status']}")
                    
                    # Browser Stats
                    if data['analytics']['top_browsers']:
                        st.write("### Top Browsers")
                        for browser in data['analytics']['top_browsers']:
                            st.write(f"- {browser['browser']}: {browser['clicks']} clicks")
                else:
                    st.error(f"Error: {response.json().get('detail', 'Analytics not found')}")
            except Exception as e:
                st.error(f"Error fetching analytics: {str(e)}")
    
    with tab2:
        st.info("Coming soon: Advanced analytics with charts and geographic data")
