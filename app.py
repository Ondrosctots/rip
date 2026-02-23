import streamlit as st
import requests
import time
import re

# --- UI Setup ---
st.set_page_config(page_title="Reverb Guardian", page_icon="🛡️")
st.title("🛡️ Reverb Guardian: Session Emulation")

with st.sidebar:
    st.header("🔑 Session Credentials")
    user_cookie = st.text_area("1. Paste Cookie String:")
    csrf_token = st.text_input("2. Paste X-CSRF-Token:")
    
    st.divider()
    st.info("💡 Get the CSRF token by typing `reverb.csrf_token` in the browser console.")

# --- Input Area ---
listing_url = st.text_input("Listing URL to Report:", placeholder="https://reverb.com/item/...")

if st.button("🚀 Submit Session Report"):
    if not user_cookie or not csrf_token:
        st.error("Missing Session Credentials.")
    else:
        match = re.search(r'/item/(\d+)', listing_url)
        if match:
            l_id = match.group(1)
            
            # --- HIGH STEALTH HEADERS ---
            # These are designed to bypass Cloudflare 403 filters
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Accept-Language": "en-US,en;q=0.9",
                "Content-Type": "application/json",
                "X-CSRF-Token": csrf_token,
                "X-Requested-With": "XMLHttpRequest",
                "Cookie": user_cookie,
                "Origin": "https://reverb.com",
                "Referer": listing_url,
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin"
            }

            report_url = f"https://reverb.com/listings/{l_id}/flags"
            payload = {
                "flag": {
                    "reason": "scam", 
                    "description": "Coordinated scam listing - regional block detected."
                }
            }

            try:
                # We use a Session object to handle cookie persistence
                session = requests.Session()
                response = session.post(report_url, json=payload, headers=headers)
                
                if response.status_code in [200, 201, 204]:
                    st.success(f"✅ Report successful for {l_id}!")
                elif response.status_code == 403:
                    st.error("❌ 403 Forbidden: Cloudflare is still blocking the script.")
                    st.warning("Try this: Open the listing, click 'Report' manually once, then try the script again.")
                else:
                    st.error(f"❌ Failed ({response.status_code})")
                    st.write(response.text[:300])
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.error("Invalid URL format.")

st.divider()
st.caption("2026 Reverb Community Defense Tool")
