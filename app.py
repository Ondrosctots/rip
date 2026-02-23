import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
import re

# --- Configuration ---
REVERB_API_BASE = "https://api.reverb.com/api"

def parse_ids_from_html(html_content):
    """
    Highly aggressive extraction of Reverb Listing IDs from HTML source.
    Looks for data attributes, URL paths, and JSON blobs.
    """
    listing_ids = set()
    
    # 1. Standard Reverb data attribute
    # Example: data-listing-id="12345678"
    found_data_attrs = re.findall(r'data-listing-id=["\'](\d+)["\']', html_content)
    listing_ids.update(found_data_attrs)
    
    # 2. Standard URL pattern in links
    # Example: /item/12345678-gibson-les-paul
    found_urls = re.findall(r'/item/(\d+)-', html_content)
    listing_ids.update(found_urls)

    # 3. JSON Object patterns (Found in script tags)
    # Example: "id":12345678,"title"
    found_json = re.findall(r'["\']id["\']\s*:\s*(\d{7,10})', html_content)
    listing_ids.update(found_json)

    # 4. Canonical link tags
    # Example: <link rel="canonical" href=".../item/12345678">
    found_canon = re.findall(r'reverb\.com/item/(\d+)', html_content)
    listing_ids.update(found_canon)
            
    return sorted(list(listing_ids))

# --- UI Setup ---
st.set_page_config(page_title="Reverb Guardian", page_icon="🛡️")
st.title("🛡️ Reverb Guardian: Deep Bypass")

with st.sidebar:
    st.header("1. Authentication")
    api_token = st.text_input("Reverb API Token", type="password")
    
    st.header("2. Settings")
    report_reason = "scam" 
    dry_run = st.checkbox("Dry Run (Safe Mode)", value=True)
    delay = st.slider("Request Delay (Seconds)", 1, 10, 2)

st.subheader("Bypass Method: Manual Paste")
st.info("If Method A failed (403), open the shop in your browser, right-click -> 'View Page Source', and paste it below.")
manual_html = st.text_area("Paste Page Source Here", height=300)

if st.button("🚀 Process Listings"):
    if not api_token:
        st.error("Please enter your Reverb API Token in the sidebar.")
    elif not manual_html.strip():
        st.error("Please paste the page source code first.")
    else:
        st.info("Scanning code for listing patterns...")
        found_ids = parse_ids_from_html(manual_html)
            
        if not found_ids:
            st.error("❌ Still no listing IDs detected in the code.")
            st.warning("Ensure you copied the *Source Code* (Ctrl+U) and not just the text on the screen.")
        else:
            st.success(f"🎯 Target Acquired: {len(found_ids)} listings found.")
            
            api_headers = {
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/hal+json",
                "Accept": "application/hal+json",
                "Accept-Version": "3.0"
            }
            
            progress = st.progress(0)
            for idx, l_id in enumerate(found_ids):
                if dry_run:
                    st.info(f"🔍 [DRY RUN] Found Listing: **{l_id}**")
                else:
                    flag_url = f"{REVERB_API_BASE}/listings/{l_id}/flags"
                    payload = {
                        "reason": report_reason, 
                        "description": "Reporting shop-wide fraudulent patterns identified via deep scan."
                    }
                    f_resp = requests.post(flag_url, json=payload, headers=api_headers)
                    if f_resp.status_code in [200, 201, 204]:
                        st.write(f"🚩 Reported ID: {l_id}")
                    else:
                        st.error(f"Failed {l_id}: {f_resp.status_code}")
                
                progress.progress((idx + 1) / len(found_ids))
                time.sleep(delay)
            
            st.balloons()
