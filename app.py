import streamlit as st
import requests
import time
import re

# --- UI Setup ---
st.set_page_config(page_title="Reverb Guardian", page_icon="🛡️")
st.title("🛡️ Reverb Guardian: Session Emulation")

st.markdown("""
### 🛠️ How to get your Session Keys:
1. Open the scam listing in **Chrome/Edge**.
2. Press **F12** and go to the **Network** tab.
3. Refresh the page. Click on the first request (the listing name).
4. Look at **Request Headers**:
    * Copy the entire text after `cookie:`
    * Copy the text after `x-csrf-token:` (if present).
""")

with st.sidebar:
    st.header("1. Session Credentials")
    user_cookie = st.text_area("Paste Cookie String:")
    csrf_token = st.text_input("Paste X-CSRF-Token:")
    
    st.header("2. Settings")
    delay = st.slider("Request Delay (Seconds)", 1, 10, 3)

# --- Input Area ---
listing_url = st.text_input("Scam Listing URL:", placeholder="https://reverb.com/item/94627157...")

if st.button("🚩 Report via Session"):
    if not user_cookie:
        st.error("You must provide a Cookie string to emulate a session.")
    elif not listing_url:
        st.error("Please provide a listing URL.")
    else:
        # Extract ID from URL
        match = re.search(r'/item/(\d+)', listing_url)
        if not match:
            st.error("Invalid URL format.")
        else:
            l_id = match.group(1)
            st.info(f"Attempting to report ID: {l_id} using your browser session...")

            # These headers make your script look like your actual browser
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": listing_url,
                "Cookie": user_cookie,
                "X-CSRF-Token": csrf_token,
                "X-Requested-With": "XMLHttpRequest"
            }

            # Reverb's internal flagging endpoint (different from the API)
            report_url = f"https://reverb.com/listings/{l_id}/flags"
            
            payload = {
                "flag": {
                    "reason": "scam",
                    "description": "Suspected fraudulent listing identified during manual review."
                }
            }

            try:
                # We use a standard POST request just like the 'Report' button does
                response = requests.post(report_url, json=payload, headers=headers)
                
                if response.status_code in [200, 201, 204]:
                    st.success(f"✅ Successfully reported {l_id} via session emulation!")
                elif response.status_code == 422:
                    st.error("❌ CSRF Error: Your CSRF token is missing or expired. Refresh the page and copy it again.")
                elif response.status_code == 403:
                    st.error("❌ Forbidden: Reverb's security (Cloudflare) blocked the request. Try a longer delay.")
                else:
                    st.error(f"❌ Failed with Status {response.status_code}")
                    st.write(response.text[:500]) # Show snippet of error
            except Exception as e:
                st.error(f"Connection Error: {e}")

            time.sleep(delay)
