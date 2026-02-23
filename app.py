import streamlit as st
import requests
import time
import re

# --- Configuration ---
REVERB_API_BASE = "https://api.reverb.com/api"

def deep_extract_ids(html_content):
    """
    Scans for 7-9 digit numbers associated with Reverb listing patterns.
    This is designed to find IDs even in compressed or minified HTML.
    """
    # Pattern 1: URL path /item/12345678
    p1 = re.findall(r'/item/(\d{7,9})', html_content)
    # Pattern 2: JSON key "id":12345678
    p2 = re.findall(r'["\']id["\']\s*:\s*(\d{7,9})', html_content)
    # Pattern 3: Data attribute data-listing-id="12345678"
    p3 = re.findall(r'listing[-_]id["\']?\s*[:=]\s*["\']?(\d{7,9})', html_content)
    # Pattern 4: Ending listing param ?ended_listing=12345678
    p4 = re.findall(r'listing=(\d{7,9})', html_content)

    all_found = set(p1 + p2 + p3 + p4)
    return sorted(list(all_found))

# --- UI Setup ---
st.set_page_config(page_title="Reverb Guardian", page_icon="🛡️")
st.title("🛡️ Reverb Guardian: Forensic Mode")

with st.sidebar:
    st.header("1. Authentication")
    api_token = st.text_input("Reverb API Token", type="password")
    
    st.header("2. Settings")
    report_reason = "scam" 
    dry_run = st.checkbox("Dry Run (Safe Mode)", value=True)
    delay = st.slider("Request Delay (Seconds)", 1, 10, 2)

st.info("💡 **Instructions:** Go to the shop, press **Ctrl+U**, copy EVERYTHING, and paste it below.")
manual_html = st.text_area("Paste 'View Source' Code Here", height=400)

if st.button("🚀 Run Forensic Scan"):
    if not api_token:
        st.error("Missing API Token in sidebar!")
    elif not manual_html.strip():
        st.error("Please paste the source code first.")
    else:
        found_ids = deep_extract_ids(manual_html)
            
        if not found_ids:
            st.error("❌ Forensic scan found 0 IDs. Try scrolling down the shop page first to ensure all items are loaded, then 'View Source' again.")
        else:
            st.success(f"🎯 Forensic match! Found {len(found_ids)} unique Listing IDs.")
            
            headers = {
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/hal+json",
                "Accept": "application/hal+json",
                "Accept-Version": "3.0"
            }
            
            progress = st.progress(0)
            for idx, l_id in enumerate(found_ids):
                if dry_run:
                    st.info(f"🔍 [DRY RUN] ID Identified: **{l_id}**")
                else:
                    flag_url = f"{REVERB_API_BASE}/listings/{l_id}/flags"
                    payload = {"reason": report_reason, "description": "Bulk scam listing reported via forensic scan."}
                    f_resp = requests.post(flag_url, json=payload, headers=headers)
                    if f_resp.status_code in [200, 201, 204]:
                        st.write(f"🚩 Reported ID: {l_id}")
                    else:
                        st.error(f"Failed {l_id}: {f_resp.status_code}")
                
                progress.progress((idx + 1) / len(found_ids))
                time.sleep(delay)
            
            st.balloons()
