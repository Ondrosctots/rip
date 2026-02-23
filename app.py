import streamlit as st
import requests
import time
import re
import json

# --- Configuration ---
REVERB_API_BASE = "https://api.reverb.com/api"

def extract_from_json_blobs(html_content):
    """
    Looks for listing IDs inside script tags or JSON blocks 
    that Reverb uses to 'hydrate' the page.
    """
    # Find all 7-9 digit numbers that look like Reverb IDs
    # and are likely associated with a listing key
    patterns = [
        r'["\']listing_id["\']\s*:\s*(\d{7,9})',
        r'["\']id["\']\s*:\s*(\d{7,9})',
        r'/item/(\d{7,9})',
        r'listing_id=(\d{7,9})'
    ]
    
    found = set()
    for pattern in patterns:
        matches = re.findall(pattern, html_content)
        found.update(matches)
        
    return sorted(list(found))

# --- UI Setup ---
st.set_page_config(page_title="Reverb Guardian", page_icon="🛡️")
st.title("🛡️ Reverb Guardian: JSON Forensic Mode")

with st.sidebar:
    st.header("1. Authentication")
    api_token = st.text_input("Reverb API Token", type="password")
    
    st.header("2. Settings")
    report_reason = "scam" 
    dry_run = st.checkbox("Dry Run (Safe Mode)", value=True)
    delay = st.slider("Request Delay (Seconds)", 1, 10, 2)

st.warning("⚠️ **Important:** To get the full source, scroll to the bottom of the shop page first, THEN press **Ctrl+U**.")
manual_html = st.text_area("Paste 'View Source' Code Here", height=400)

if st.button("🚀 Execute JSON Extraction"):
    if not api_token:
        st.error("Missing API Token!")
    elif not manual_html.strip():
        st.error("Paste the source code first!")
    else:
        st.info("Parsing hidden data structures...")
        found_ids = extract_from_json_blobs(manual_html)
            
        if not found_ids:
            st.error("❌ No IDs found. Reverb might be hiding the data in a non-standard format.")
            st.info("Try this: Inspect one listing title in your browser, find the `id`, and paste it manually.")
        else:
            st.success(f"🎯 Success! Extracted {len(found_ids)} unique Listing IDs.")
            
            headers = {
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/hal+json",
                "Accept": "application/hal+json",
                "Accept-Version": "3.0"
            }
            
            progress = st.progress(0)
            for idx, l_id in enumerate(found_ids):
                if dry_run:
                    st.info(f"🔍 [DRY RUN] Found: **{l_id}**")
                else:
                    flag_url = f"{REVERB_API_BASE}/listings/{l_id}/flags"
                    payload = {"reason": report_reason, "description": "Coordinated fraudulent listings identified via shop source."}
                    f_resp = requests.post(flag_url, json=payload, headers=headers)
                    if f_resp.status_code in [200, 201, 204]:
                        st.write(f"🚩 Reported ID: {l_id}")
                    else:
                        st.error(f"Failed {l_id}: {f_resp.status_code}")
                
                progress.progress((idx + 1) / len(found_ids))
                time.sleep(delay)
            
            st.balloons()
