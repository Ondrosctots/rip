import streamlit as st
import requests
import time
import re

# --- Configuration ---
REVERB_API_BASE = "https://api.reverb.com/api"

def extract_shop_slug(url):
    """Extracts the identifier from Reverb shop or user URLs."""
    url = url.strip().rstrip('/')
    # Matches /shop/name, /users/name, or just the name itself
    if "reverb.com" in url:
        match = re.search(r"(?:shop|users)/([^/?#\s]+)", url)
        return match.group(1) if match else None
    return url # Assume it's the slug if no URL is provided

# --- UI Setup ---
st.set_page_config(page_title="Reverb Guardian", page_icon="🛡️")
st.title("🛡️ Reverb Bulk Listing Reporter")
st.markdown("Use this to clean up shop listings that match scam patterns.")

with st.sidebar:
    st.header("1. Authentication")
    api_token = st.text_input("Reverb API Token", type="password")
    
    st.header("2. Settings")
    report_reason = "scam" 
    dry_run = st.checkbox("Dry Run (Safe Mode)", value=True)
    delay = st.slider("Request Delay (Seconds)", 1, 10, 3)
    max_pages = st.number_input("Max Pages to Scan", min_value=1, max_value=5, value=1)

seller_url = st.text_input("Paste Seller Link", placeholder="https://reverb.com/shop/username")

# --- Execution Logic ---
if st.button("🚀 Start Reporting Process"):
    slug = extract_shop_slug(seller_url)
    
    if not api_token:
        st.error("Missing API Token!")
    elif not slug:
        st.error("Could not parse a shop name from that link.")
    else:
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/hal+json",
            "Accept": "application/hal+json",
            "Accept-Version": "3.0"
        }

        all_listings = []
        
        # --- MULTI-METHOD FETCHING ---
        methods = [
            {"name": "Shop API", "url": f"{REVERB_API_BASE}/shops/{slug}/listings?state=live"},
            {"name": "Search Filter", "url": f"{REVERB_API_BASE}/listings/all?shop_name={slug}&state=live"},
            {"name": "Keyword Query", "url": f"{REVERB_API_BASE}/listings?query={slug}&state=live"}
        ]

        for method in methods:
            if all_listings: break # Stop if we found items
            
            st.info(f"Attempting {method['name']}...")
            try:
                for page in range(1, max_pages + 1):
                    paged_url = f"{method['url']}&page={page}"
                    res = requests.get(paged_url, headers=headers)
                    
                    if res.status_code == 200:
                        data = res.json()
                        page_items = data.get("_embedded", {}).get("listings", [])
                        
                        # Verify the shop slug matches to prevent "2 million results" error
                        matched_items = [i for i in page_items if i.get('shop', {}).get('slug') == slug]
                        all_listings.extend(matched_items)
                        
                        if len(page_items) < 20: break # No more pages
                    else:
                        break # Method failed, move to next
            except Exception as e:
                continue

        # --- PROCESS RESULTS ---
        if not all_listings:
            st.warning(f"⚠️ No live listings found for '{slug}'.")
            st.info("Tip: Open the shop link in your browser. If it says 'Page Not Found', Reverb has already banned them!")
        else:
            st.success(f"✅ Found {len(all_listings)} listings for '{slug}'. Starting reports...")
            progress_bar = st.progress(0)
            
            for idx, item in enumerate(all_listings):
                listing_id = item.get("id")
                title = item.get("title")
                
                if dry_run:
                    st.info(f"🔍 [DRY RUN] Found: **{title}** (ID: {listing_id})")
                else:
                    report_url = f"{REVERB_API_BASE}/listings/{listing_id}/flags"
                    payload = {
                        "reason": report_reason, 
                        "description": "Bulk reporting coordinated fraudulent listings from this shop."
                    }
                    rep_resp = requests.post(report_url, json=payload, headers=headers)
                    
                    if rep_resp.status_code in [200, 201, 204]:
                        st.write(f"🚩 Reported: {title}")
                    else:
                        st.error(f"Failed {listing_id}: {rep_resp.status_code}")
                
                progress_bar.progress((idx + 1) / len(all_listings))
                time.sleep(delay)

            st.balloons()
            st.success("Process Complete.")
