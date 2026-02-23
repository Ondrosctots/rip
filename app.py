import streamlit as st
import requests
import time
import re

# --- Configuration ---
REVERB_API_BASE = "https://api.reverb.com/api"

def clean_id_list(input_text):
    """
    Extracts all 7-10 digit numbers from a block of text.
    Allows the user to paste URLs, a list, or even raw notes.
    """
    return re.findall(r'(\d{7,10})', input_text)

# --- UI Setup ---
st.set_page_config(page_title="Reverb Guardian", page_icon="🛡️")
st.title("🛡️ Reverb Guardian: Failsafe Mode")
st.markdown("""
### 🎯 How to use this:
1. Open the scammer's shop.
2. Click on a few listings and copy the numbers from the URL (e.g., `reverb.com/item/**84756321**`).
3. Paste all those numbers (or the full URLs) into the box below.
""")

with st.sidebar:
    st.header("1. Authentication")
    api_token = st.text_input("Reverb API Token", type="password")
    
    st.header("2. Settings")
    report_reason = "scam" 
    dry_run = st.checkbox("Dry Run (Safe Mode)", value=True)
    delay = st.slider("Request Delay (Seconds)", 1, 10, 2)

# --- Input Area ---
raw_input = st.text_area("Paste Listing IDs or URLs here:", height=200, placeholder="87654321, 87654322, https://reverb.com/item/87654323...")

if st.button("🚩 Start Bulk Reporting"):
    if not api_token:
        st.error("Please provide your API token in the sidebar.")
    elif not raw_input.strip():
        st.error("Please paste at least one Listing ID or URL.")
    else:
        # Extract and de-duplicate IDs
        found_ids = list(set(clean_id_list(raw_input)))
        
        if not found_ids:
            st.error("❌ No valid 7-10 digit IDs found in your text.")
        else:
            st.success(f"✅ Found {len(found_ids)} unique IDs. Starting process...")
            
            headers = {
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/hal+json",
                "Accept": "application/hal+json",
                "Accept-Version": "3.0"
            }
            
            progress = st.progress(0)
            status_text = st.empty()
            
            for idx, l_id in enumerate(found_ids):
                status_text.text(f"Processing {idx+1}/{len(found_ids)}: ID {l_id}")
                
                if dry_run:
                    st.info(f"🔍 [DRY RUN] Ready to report Listing: **{l_id}**")
                else:
                    flag_url = f"{REVERB_API_BASE}/listings/{l_id}/flags"
                    payload = {
                        "reason": report_reason, 
                        "description": "Part of a coordinated scam shop. Reporting for immediate review."
                    }
                    
                    try:
                        f_resp = requests.post(flag_url, json=payload, headers=headers)
                        if f_resp.status_code in [200, 201, 204]:
                            st.write(f"🚩 **Success:** Reported {l_id}")
                        elif f_resp.status_code == 404:
                            st.warning(f"⚠️ **Notice:** {l_id} was not found (might already be deleted).")
                        else:
                            st.error(f"❌ **Error {f_resp.status_code}** for {l_id}")
                    except Exception as e:
                        st.error(f"Connection error for {l_id}: {e}")
                
                # Update progress
                progress.progress((idx + 1) / len(found_ids))
                time.sleep(delay)
            
            st.balloons()
            st.success("Finished processing all IDs.")
