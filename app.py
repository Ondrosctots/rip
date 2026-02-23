import streamlit as st
import requests
import time
import re

# --- Configuration ---
REVERB_API_BASE = "https://api.reverb.com/api"

def extract_slug(url):
    """Extracts the slug from various Reverb URL formats."""
    url = url.strip().rstrip('/')
    if "reverb.com" in url:
        # Matches /shop/slug, /users/slug, or /p/slug
        match = re.search(r"/(?:shop|users|p)/([^/?#\s]+)", url)
        return match.group(1) if match else url.split('/')[-1]
    return url

# --- UI Setup ---
st.set_page_config(page_title="Reverb Guardian", page_icon="🛡️")
st.title("🛡️ Reverb Guardian: Deep Scraper")
st.markdown("If the Shop API says '0 listings' but you see them live, use this mode.")

with st.sidebar:
    st.header("1. Authentication")
    api_token = st.text_input("Reverb API Token", type="password")
    
    st.header("2. Settings")
    report_reason = "scam" 
    dry_run = st.checkbox("Dry Run (Safe Mode)", value=True)
    delay = st.slider("Request Delay (Seconds)", 1, 10, 2)

seller_url = st.text_input("Target Shop Link or Slug", placeholder="gilmars-shop-5")

if st.button("🚀 Execute Deep Scan"):
    slug = extract_slug(seller_url)
    
    if not api_token or not slug:
        st.error("Missing API Token or Shop Link!")
    else:
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/hal+json",
            "Accept": "application/hal+json",
            "Accept-Version": "3.0"
        }

        # --- STEP 1: DEEP DISCOVERY ---
        st.info(f"Initiating Deep Scan for: **{slug}**...")
        
        # We search specifically for the shop_name in the global listings pool
        # We also add 'shipping_region=all' to ensure no regional blocks occur
        search_url = f"{REVERB_API_BASE}/listings/all?shop_name={slug}&shipping_region=all&state=live"
        
        try:
            response = requests.get(search_url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                raw_listings = data.get("_embedded", {}).get("listings", [])
                
                # Manual validation: Sometimes Reverb's search is too broad.
                # We only keep items where the shop slug matches our target EXACTLY.
                target_items = [
                    item for item in raw_listings 
                    if item.get('shop', {}).get('slug', '').lower() == slug.lower()
                ]
                
                if not target_items:
                    st.warning("Found listings in search, but none matched the Shop Slug exactly.")
                    # Fallback: Check if we can find any item from this seller using a query
                    query_url = f"{REVERB_API_BASE}/listings?query={slug}"
                    q_resp = requests.get(query_url, headers=headers)
                    q_items = q_resp.json().get("_embedded", {}).get("listings", [])
                    target_items = [i for i in q_items if i.get('shop', {}).get('slug', '').lower() == slug.lower()]

                if target_items:
                    st.success(f"🎯 Target Found! Processing {len(target_items)} listings.")
                    
                    progress = st.progress(0)
                    for idx, item in enumerate(target_items):
                        l_id = item.get("id")
                        title = item.get("title")
                        
                        if dry_run:
                            st.info(f"🔍 [DRY RUN] Would report: **{title}** (ID: {l_id})")
                        else:
                            flag_url = f"{REVERB_API_BASE}/listings/{l_id}/flags"
                            payload = {"reason": report_reason, "description": "Coordinated scam listings."}
                            f_resp = requests.post(flag_url, json=payload, headers=headers)
                            
                            if f_resp.status_code in [200, 201, 204]:
                                st.write(f"🚩 Reported: {title}")
                            else:
                                st.error(f"Failed {l_id}: {f_resp.status_code}")
                        
                        progress.progress((idx + 1) / len(target_items))
                        time.sleep(delay)
                    
                    st.balloons()
                else:
                    st.error(f"❌ Could not locate listings for '{slug}' via API.")
                    st.info("Check if the slug in the URL changed. Scammers sometimes 'migrate' slugs.")
            else:
                st.error(f"API Error {response.status_code}: {response.text}")

        except Exception as e:
            st.error(f"Fatal Error: {str(e)}")
