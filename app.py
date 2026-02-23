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
st.title("🛡️ Reverb Guardian: Priority Flag Mode")

with st.sidebar:
    st.header("1. Authentication")
    api_token = st.text_input("Reverb API Token", type="password", help="Check ALL boxes during generation!")
    
    st.header("2. Settings")
    report_reason = "scam" 
    dry_run = st.checkbox("Dry Run (Safe Mode)", value=False)
    delay = st.slider("Request Delay (Seconds)", 1, 10, 2)

st.info("💡 **Tip:** If you still get a 404, try creating a **new** API token specifically while using a **VPN** set to the seller's country.")

raw_input = st.text_area("Paste Listing IDs or URLs:", height=150)

if st.button("🚩 Execute Priority Report"):
    if not api_token:
        st.error("Missing API Token!")
    elif not raw_input.strip():
        st.error("Please paste at least one ID.")
    else:
        found_ids = list(set(clean_id_list(raw_input)))
        
        if not found_ids:
            st.error("❌ No valid IDs found.")
        else:
            st.success(f"🎯 IDs Detected: {len(found_ids)}")
            
            # Using v3.0 headers for maximum compatibility
            headers = {
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/hal+json",
                "Accept": "application/hal+json",
                "Accept-Version": "3.0"
            }
            
            progress = st.progress(0)
            for idx, l_id in enumerate(found_ids):
                if dry_run:
                    st.info(f"🔍 [DRY RUN] Target: {l_id}")
                else:
                    # Alternative Flagging Endpoint Logic
                    flag_url = f"{REVERB_API_BASE}/listings/{l_id}/flags"
                    payload = {
                        "reason": report_reason, 
                        "description": "Fraudulent listing detected. Coordinated scam shop pattern."
                    }
                    
                    try:
                        res = requests.post(flag_url, json=payload, headers=headers)
                        
                        if res.status_code in [200, 201, 204]:
                            st.write(f"✅ **Reported:** {l_id}")
                        elif res.status_code == 404:
                            st.error(f"❌ **404 Blocked:** Reverb API is hiding {l_id} from your account's region.")
                        elif res.status_code == 403:
                            st.error(f"❌ **403 Forbidden:** Your token lacks 'Write' permissions.")
                        else:
                            st.error(f"❌ **Error {res.status_code}:** Listing {l_id}")
                    except Exception as e:
                        st.error(f"Request failed: {e}")
                
                progress.progress((idx + 1) / len(found_ids))
                time.sleep(delay)
            
            st.balloons()
