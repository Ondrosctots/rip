import streamlit as st
import requests
import time
import re

# --- Configuration ---
REVERB_API_BASE = "https://api.reverb.com/api"

def clean_id_list(input_text):
    """Extracts all 7-10 digit numbers from text."""
    return re.findall(r'(\d{7,10})', input_text)

# --- UI Setup ---
st.set_page_config(page_title="Reverb Guardian", page_icon="🛡️")
st.title("🛡️ Reverb Guardian: Failsafe Mode")

with st.sidebar:
    st.header("1. Authentication")
    api_token = st.text_input("Reverb API Token", type="password", help="Ensure all checkboxes were checked when generating this token!")
    
    st.header("2. Settings")
    report_reason = "scam" 
    dry_run = st.checkbox("Dry Run (Safe Mode)", value=False) # Default to False to allow action
    delay = st.slider("Request Delay (Seconds)", 1, 10, 2)

st.info("Paste the Listing IDs or URLs of the scam items below. We will attempt a high-priority API report.")

raw_input = st.text_area("Paste IDs or URLs:", height=200)

if st.button("🚩 Execute Priority Report"):
    if not api_token:
        st.error("Missing API Token! Check your sidebar.")
    elif not raw_input.strip():
        st.error("Please paste at least one ID.")
    else:
        found_ids = list(set(clean_id_list(raw_input)))
        
        if not found_ids:
            st.error("❌ No valid IDs found.")
        else:
            st.success(f"🎯 Target Acquired: {len(found_ids)} unique IDs.")
            
            # Use strict HAL+JSON headers as required by Reverb API v3.0
            headers = {
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/hal+json",
                "Accept": "application/hal+json",
                "Accept-Version": "3.0"
            }
            
            progress = st.progress(0)
            for idx, l_id in enumerate(found_ids):
                if dry_run:
                    st.info(f"🔍 [DRY RUN] Found: {l_id}")
                else:
                    # We hit the flags endpoint directly
                    flag_url = f"{REVERB_API_BASE}/listings/{l_id}/flags"
                    payload = {
                        "reason": report_reason, 
                        "description": "Reporting suspected fraudulent/scam listing for immediate review."
                    }
                    
                    try:
                        # Attempt to report
                        f_resp = requests.post(flag_url, json=payload, headers=headers)
                        
                        if f_resp.status_code in [200, 201, 204]:
                            st.write(f"✅ **Reported:** {l_id}")
                        elif f_resp.status_code == 404:
                            st.error(f"❌ **Error 404:** Reverb says ID {l_id} doesn't exist. This usually means your API Token doesn't have the 'public' or 'read' scopes enabled.")
                        elif f_resp.status_code == 401:
                            st.error(f"❌ **Error 401:** Unauthorized. Your token is invalid or has expired.")
                        else:
                            st.error(f"❌ **Error {f_resp.status_code}:** Could not report {l_id}.")
                    except Exception as e:
                        st.error(f"Network error for {l_id}: {e}")
                
                progress.progress((idx + 1) / len(found_ids))
                time.sleep(delay)
            
            st.balloons()
