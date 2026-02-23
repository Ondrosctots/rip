import streamlit as st
import requests
import time
import re

# --- Configuration ---
REVERB_API_BASE = "https://api.reverb.com/api"

def extract_shop_slug(url):
    """Extracts the shop identifier from Reverb shop URLs."""
    url = url.strip().rstrip('/')
    match = re.search(r"shop/([^/?#\s]+)", url)
    return match.group(1) if match else None

# --- UI Setup ---
st.set_page_config(page_title="Reverb Guardian", page_icon="🎸")
st.title("🎸 Reverb Bulk Listing Reporter")

with st.sidebar:
    st.header("1. Authentication")
    api_token = st.text_input("Reverb API Token", type="password")
    
    st.header("2. Settings")
    report_reason = "scam" 
    dry_run = st.checkbox("Dry Run (Safe Mode)", value=True)
    delay = st.slider("Request Delay (Seconds)", 1, 10, 3)
    debug_mode = st.checkbox("Show Raw API Data", value=False)

seller_url = st.text_input("Paste Seller Shop Link", placeholder="https://reverb.com/shop/gilmars-shop-5")

# --- Execution Logic ---
if st.button("🚀 Start Reporting Process"):
    shop_slug = extract_shop_slug(seller_url)
    
    if not api_token:
        st.error("Missing API Token!")
    elif not shop_slug:
        st.error("Invalid Reverb Shop URL.")
    else:
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/hal+json",
            "Accept": "application/hal+json",
            "Accept-Version": "3.0", 
            "X-Display-Group": "global"
        }

        st.info(f"🔍 Fetching official shop data for: **{shop_slug}**...")
        
        # FIX: Targeted Shop Endpoint
        # We use /shops/{slug}/listings to ensure we ONLY get that person's items
        fetch_url = f"{REVERB_API_BASE}/shops/{shop_slug}/listings?state=live"
        
        try:
            response = requests.get(fetch_url, headers=headers)
            
            if response.status_code != 200:
                st.error(f"Reverb Error {response.status_code}: {response.text}")
                st.stop()
                
            data = response.json()
            
            if debug_mode:
                st.write("### Debug: Raw API Response")
                st.json(data)
            
            # Reverb HAL+JSON structure for shop-specific listings
            listings = data.get("_embedded", {}).get("listings", [])
            
            if not listings:
                st.warning(f"No live listings found specifically for '{shop_slug}'. The shop may be empty or already banned.")
            else:
                st.success(f"✅ Found {len(listings)} listings for this shop. Starting reports...")
                progress_bar = st.progress(0)
                
                for idx, item in enumerate(listings):
                    listing_id = item.get("id")
                    title = item.get("title")
                    
                    # Double check that the shop name matches (safety layer)
                    current_item_shop = item.get("shop", {}).get("slug", "")
                    
                    if dry_run:
                        st.info(f"🔍 [DRY RUN] Found: **{title}** (ID: {listing_id})")
                    else:
                        # 2. POST the Flag/Report
                        report_url = f"{REVERB_API_BASE}/listings/{listing_id}/flags"
                        payload = {
                            "reason": report_reason, 
                            "description": "Coordinated scam listings from this specific shop profile."
                        }
                        
                        rep_resp = requests.post(report_url, json=payload, headers=headers)
                        
                        if rep_resp.status_code in [200, 201, 204]:
                            st.write(f"🚩 Reported: {title}")
                        else:
                            st.error(f"Failed {listing_id}: {rep_resp.status_code}")
                    
                    progress_bar.progress((idx + 1) / len(listings))
                    time.sleep(delay)

                st.balloons()
                st.success("Process Complete.")

        except Exception as e:
            st.error(f"System Error: {e}")
