import streamlit as st
import requests
import time
import re

# --- Configuration ---
REVERB_API_BASE = "https://api.reverb.com/api"

def extract_shop_slug(url):
    """Extracts the identifier from Reverb shop or user URLs."""
    url = url.strip().rstrip('/')
    # Matches both /shop/name and /users/name
    match = re.search(r"(?:shop|users)/([^/?#\s]+)", url)
    return match.group(1) if match else None

# --- UI Setup ---
st.set_page_config(page_title="Reverb Guardian", page_icon="🛡️")
st.title("🛡️ Reverb Bulk Listing Reporter")

with st.sidebar:
    st.header("1. Authentication")
    api_token = st.text_input("Reverb API Token", type="password")
    
    st.header("2. Settings")
    report_reason = "scam" 
    dry_run = st.checkbox("Dry Run (Safe Mode)", value=True)
    delay = st.slider("Request Delay (Seconds)", 1, 10, 3)

seller_url = st.text_input("Paste Seller Link", placeholder="https://reverb.com/shop/gilmars-shop-5")

# --- Execution Logic ---
if st.button("🚀 Start Reporting Process"):
    slug = extract_shop_slug(seller_url)
    
    if not api_token:
        st.error("Missing API Token!")
    elif not slug:
        st.error("Could not find a shop or user name in that link.")
    else:
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/hal+json",
            "Accept": "application/hal+json",
            "Accept-Version": "3.0"
        }

        listings = []
        
        # METHOD 1: Try as a Shop
        st.info(f"Method 1: Attempting to fetch as a Shop...")
        res = requests.get(f"{REVERB_API_BASE}/shops/{slug}/listings?state=live", headers=headers)
        if res.status_code == 200:
            listings = res.json().get("_embedded", {}).get("listings", [])

        # METHOD 2: Try as a Search Filter (Strictly for this shop name)
        if not listings:
            st.info(f"Method 2: Attempting search filter for '{slug}'...")
            res = requests.get(f"{REVERB_API_BASE}/listings/all?shop_name={slug}&state=live", headers=headers)
            if res.status_code == 200:
                raw_list = res.json().get("_embedded", {}).get("listings", [])
                # Filter to make sure we ONLY get the exact shop (prevents the '2 million results' issue)
                listings = [l for l in raw_list if l.get('shop', {}).get('slug') == slug]

        # METHOD 3: Try generic query
        if not listings:
            st.info(f"Method 3: Final attempt via query...")
            res = requests.get(f"{REVERB_API_BASE}/listings?query={slug}", headers=headers)
            if res.status_code == 200:
                raw_list = res.json().get("_embedded", {}).get("listings", [])
                listings = [l for l in raw_list if l.get('shop', {}).get('slug') == slug]

        # --- Process Results ---
        if not listings:
            st.error(f"❌ Could not find any live listings for '{slug}'. The user may have no items, or the account might already be suspended.")
        else:
            st.success(f"✅ Found {len(listings)} listings! Starting reports...")
            progress_bar = st.progress(0)
            
            for idx, item in enumerate(listings):
                listing_id = item.get("id")
                title = item.get("title")
                
                if dry_run:
                    st.info(f"🔍 [DRY RUN] Would report: **{title}**")
                else:
                    report_url = f"{REVERB_API_BASE}/listings/{listing_id}/flags"
                    payload = {"reason": report_reason, "description": "Bulk reporting coordinated scam listings."}
                    rep_resp = requests.post(report_url, json=payload, headers=headers)
                    
                    if rep_resp.status_code in [200, 201, 204]:
                        st.write(f"🚩 Reported: {title}")
                    else:
                        st.error(f"Failed {listing_id}: {rep_resp.status_code}")
                
                progress_bar.progress((idx + 1) / len(listings))
                time.sleep(delay)

            st.balloons()
