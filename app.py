import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
import re

# --- Configuration ---
REVERB_API_BASE = "https://api.reverb.com/api"

def parse_ids_from_html(html_content):
    """Extracts listing IDs from raw HTML string."""
    soup = BeautifulSoup(html_content, "html.parser")
    listing_ids = set()
    
    # Method A: Data attributes
    for tag in soup.find_all(attrs={"data-listing-id": True}):
        listing_ids.add(tag["data-listing-id"])
        
    # Method B: URL patterns
    links = soup.find_all("a", href=re.compile(r"/item/(\d+)"))
    for link in links:
        match = re.search(r"/item/(\d+)", link['href'])
        if match:
            listing_ids.add(match.group(1))
            
    return list(listing_ids)

# --- UI Setup ---
st.set_page_config(page_title="Reverb Guardian", page_icon="🛡️")
st.title("🛡️ Reverb Guardian: Bypass Mode")

with st.sidebar:
    st.header("1. Authentication")
    api_token = st.text_input("Reverb API Token", type="password")
    
    st.header("2. Settings")
    report_reason = "scam" 
    dry_run = st.checkbox("Dry Run (Safe Mode)", value=True)
    delay = st.slider("Request Delay (Seconds)", 1, 10, 2)

st.subheader("Method A: Automatic Scrape")
shop_link = st.text_input("Full Shop URL", placeholder="https://reverb.com/shop/gilmars-shop-5")

st.divider()

st.subheader("Method B: Manual Paste (Use if 403 error occurs)")
manual_html = st.text_area("Paste Page Source Here", height=200, help="Right-click shop page -> View Page Source -> Copy All -> Paste Here")

if st.button("🚀 Process Listings"):
    found_ids = []
    
    if manual_html.strip():
        st.info("Parsing IDs from manual HTML paste...")
        found_ids = parse_ids_from_html(manual_html)
    elif shop_link:
        st.info("Attempting automatic scrape...")
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"}
        try:
            res = requests.get(shop_link, headers=headers)
            if res.status_code == 200:
                found_ids = parse_ids_from_html(res.text)
            else:
                st.error(f"Automatic scrape blocked (Error {res.status_code}). Please use Method B.")
        except Exception as e:
            st.error(f"Error: {e}")
            
    if not found_ids:
        st.warning("No listing IDs found. Ensure you are on the shop's main page.")
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
                st.info(f"🔍 [DRY RUN] Ready to report: {l_id}")
            else:
                flag_url = f"{REVERB_API_BASE}/listings/{l_id}/flags"
                payload = {"reason": report_reason, "description": "Bulk fraudulent listings."}
                f_resp = requests.post(flag_url, json=payload, headers=api_headers)
                if f_resp.status_code in [200, 201, 204]:
                    st.write(f"🚩 Reported ID: {l_id}")
                else:
                    st.error(f"Failed {l_id}: {f_resp.status_code}")
            
            progress.progress((idx + 1) / len(found_ids))
            time.sleep(delay)
        st.balloons()
