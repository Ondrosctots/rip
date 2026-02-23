import streamlit as st
import requests
import time
import re

# --- Configuration ---
REVERB_API_BASE = "https://api.reverb.com/api"

def extract_shop_slug(url):
    """Extracts 'shop-name' from https://reverb.com/shop/shop-name"""
    match = re.search(r"reverb\.com/shop/([^/?#\s]+)", url)
    return match.group(1) if match else None

# --- UI Setup ---
st.set_page_config(page_title="Reverb Guardian", page_icon="🎸")
st.title("🎸 Reverb Bulk Listing Reporter")
st.markdown("Automate the reporting of fraudulent listings from a specific shop.")

with st.sidebar:
    st.header("Authentication")
    api_token = st.text_input("Reverb API Token", type="password", help="Get this from your Reverb Account Settings > API Applications.")
    
    st.header("Settings")
    report_reason = "scam" # Hardcoded per your request
    dry_run = st.checkbox("Dry Run (Don't actually report)", value=True)
    delay = st.slider("Delay between reports (seconds)", 1, 10, 3)

seller_url = st.text_input("Paste Seller Shop Link", placeholder="https://reverb.com/shop/username")

# --- Execution Logic ---
if st.button("🚀 Start Reporting Process"):
    shop_slug = extract_shop_slug(seller_url)
    
    if not api_token:
        st.error("Missing API Token!")
    elif not shop_slug:
        st.error("Invalid Reverb Shop URL. Please use the format: reverb.com/shop/username")
    else:
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/hal+json",
            "Accept": "application/hal+json",
            "X-Display-Group": "global"
        }

        # 1. Fetch Listings
        st.info(f"🔍 Fetching live listings for: **{shop_slug}**...")
        fetch_url = f"{REVERB_API_BASE}/listings/all?shop={shop_slug}&state=live"
        
        try:
            response = requests.get(fetch_url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # Reverb's HAL+JSON structure stores listings in _embedded
            listings = data.get("_embedded", {}).get("listings", [])
            
            if not listings:
                st.warning("No live listings found for this shop.")
            else:
                st.success(f"Found {len(listings)} listings. Starting reports...")
                
                progress_bar = st.progress(0)
                
                for idx, item in enumerate(listings):
                    listing_id = item.get("id")
                    title = item.get("title")
                    
                    if dry_run:
                        st.write(f"🔍 [DRY RUN] Would report: **{title}** (ID: {listing_id})")
                    else:
                        # 2. POST the Flag/Report
                        report_url = f"{REVERB_API_BASE}/listings/{listing_id}/flags"
                        payload = {"reason": report_reason, "description": "Coordinated scam listings."}
                        
                        rep_resp = requests.post(report_url, json=payload, headers=headers)
                        
                        if rep_resp.status_code in [200, 201, 204]:
                            st.write(f"✅ Reported: {title}")
                        else:
                            st.error(f"❌ Failed to report {listing_id}: {rep_resp.status_code}")
                    
                    # Update Progress
                    progress_bar.progress((idx + 1) / len(listings))
                    time.sleep(delay) # Prevent API rate-limiting

                st.balloons()
                st.success("Finished processing all listings.")

        except Exception as e:
            st.error(f"An error occurred: {e}")
