import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
import re

# --- Configuration ---
REVERB_API_BASE = "https://api.reverb.com/api"

def extract_listings_via_scrape(shop_url):
    """Scrapes the HTML of the shop page to find listing IDs."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(shop_url, headers=headers)
        if response.status_code != 200:
            st.error(f"Could not load page. Status: {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Reverb listings usually have a data-listing-id attribute 
        # or IDs embedded in links like /item/12345678-title
        listing_ids = set()
        
        # Method A: Look for data attributes
        for tag in soup.find_all(attrs={"data-listing-id": True}):
            listing_ids.add(tag["data-listing-id"])
            
        # Method B: Regex search in links if Method A fails
        if not listing_ids:
            links = soup.find_all("a", href=re.compile(r"/item/(\d+)"))
            for link in links:
                match = re.search(r"/item/(\d+)", link['href'])
                if match:
                    listing_ids.add(match.group(1))
                    
        return list(listing_ids)
    except Exception as e:
        st.error(f"Scrape Error: {e}")
        return []

# --- UI Setup ---
st.set_page_config(page_title="Reverb Guardian", page_icon="🛡️")
st.title("🛡️ Reverb Guardian: Web Scraper Mode")
st.markdown("Bypasses API blocks by reading the shop page directly.")

with st.sidebar:
    st.header("1. Authentication")
    api_token = st.text_input("Reverb API Token", type="password")
    
    st.header("2. Settings")
    report_reason = "scam" 
    dry_run = st.checkbox("Dry Run (Safe Mode)", value=True)
    delay = st.slider("Request Delay (Seconds)", 1, 10, 2)

shop_link = st.text_input("Full Shop URL", placeholder="https://reverb.com/shop/gilmars-shop-5")

if st.button("🔍 Scrape & Report"):
    if not api_token or not shop_link:
        st.error("Missing API Token or Shop URL!")
    else:
        st.info("Reading shop page HTML...")
        found_ids = extract_listings_via_scrape(shop_link)
        
        if not found_ids:
            st.warning("No listing IDs found on the page. Ensure the URL is a direct link to the shop's listings.")
        else:
            st.success(f"🎯 Detected {len(found_ids)} listings in the HTML! Starting reports...")
            
            headers = {
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/hal+json",
                "Accept": "application/hal+json",
                "Accept-Version": "3.0"
            }
            
            progress = st.progress(0)
            for idx, l_id in enumerate(found_ids):
                if dry_run:
                    st.info(f"🔍 [DRY RUN] Would report Listing ID: **{l_id}**")
                else:
                    flag_url = f"{REVERB_API_BASE}/listings/{l_id}/flags"
                    payload = {"reason": report_reason, "description": "Reporting fraudulent listings identified via shop scan."}
                    f_resp = requests.post(flag_url, json=payload, headers=headers)
                    
                    if f_resp.status_code in [200, 201, 204]:
                        st.write(f"🚩 Reported ID: {l_id}")
                    else:
                        st.error(f"Failed to report {l_id}: {f_resp.status_code}")
                
                progress.progress((idx + 1) / len(found_ids))
                time.sleep(delay)
            
            st.balloons()
