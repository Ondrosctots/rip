import streamlit as st
import requests
import time
import re

# --- Configuration ---
REVERB_API_BASE = "https://api.reverb.com/api"

def extract_shop_slug(url):
    url = url.strip().rstrip('/')
    if "reverb.com" in url:
        match = re.search(r"(?:shop|users)/([^/?#\s]+)", url)
        return match.group(1) if match else url
    return url

# --- UI Setup ---
st.set_page_config(page_title="Reverb Guardian", page_icon="🛡️")
st.title("🛡️ Reverb Guardian: Aggressive Mode")

with st.sidebar:
    st.header("1. Authentication")
    api_token = st.text_input("Reverb API Token", type="password")
    
    st.header("2. Settings")
    report_reason = "scam" 
    dry_run = st.checkbox("Dry Run (Safe Mode)", value=True)
    delay = st.slider("Request Delay (Seconds)", 1, 10, 2)

seller_url = st.text_input("Target Shop Link", placeholder="https://reverb.com/shop/gilmars-shop-5")

if st.button("🚀 Force Fetch & Report"):
    slug = extract_shop_slug(seller_url)
    
    if not api_token or not slug:
        st.error("Missing API Token or Shop Link!")
    else:
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/hal+json",
            "Accept": "application/hal+json",
            "Accept-Version": "3.0"
        }

        # --- STEP 1: FORCE DISCOVERY ---
        # We use the global listings endpoint with a shop_name filter 
        # and 'shipping_region=all' to bypass location blocks.
        st.info(f"Searching marketplace for listings from: {slug}...")
        
        search_urls = [
            f"{REVERB_API_BASE}/listings/all?shop_name={slug}&state=live&shipping_region=all",
            f"{REVERB_API_BASE}/listings?query={slug}&state=live"
        ]
        
        found_listings = []
        for url in search_urls:
            try:
                resp = requests.get(url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    raw_items = data.get("_embedded", {}).get("listings", [])
                    # Strict validation: Only keep items where the shop slug matches exactly
                    valid = [i for i in raw_items if i.get('shop', {}).get('slug') == slug]
                    found_listings.extend(valid)
                if found_listings: break
            except Exception as e:
                st.error(f"Search error: {e}")

        # --- STEP 2: REPORTING ---
        if not found_listings:
            st.warning(f"⚠️ Still no listings found for '{slug}' via API.")
            st.info("Check if the slug is correct. If the URL is reverb.com/shop/test-1, use 'test-1'.")
        else:
            # Remove duplicates
            unique_listings = {l['id']: l for l in found_listings}.values()
            st.success(f"🎯 Target Acquired: Found {len(unique_listings)} listings!")
            
            progress = st.progress(0)
            for idx, item in enumerate(unique_listings):
                l_id = item.get("id")
                title = item.get("title")
                
                if dry_run:
                    st.info(f"🔍 [DRY RUN] Would report: {title}")
                else:
                    flag_url = f"{REVERB_API_BASE}/listings/{l_id}/flags"
                    flag_data = {"reason": report_reason, "description": "Coordinated scam listings."}
                    f_resp = requests.post(flag_url, json=flag_data, headers=headers)
                    
                    if f_resp.status_code in [200, 201, 204]:
                        st.write(f"🚩 Reported: {title}")
                    else:
                        st.error(f"Error reporting {l_id}: {f_resp.status_code}")
                
                progress.progress((idx + 1) / len(unique_listings))
                time.sleep(delay)
            
            st.balloons()
