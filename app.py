import streamlit as st
import requests
import time
import re

# --- Configuration ---
REVERB_API_BASE = "https://api.reverb.com/api"

def extract_slug(url):
    """Extracts the slug or user identifier from various Reverb URL formats."""
    url = url.strip().rstrip('/')
    if "reverb.com" in url:
        match = re.search(r"/(?:shop|users|p)/([^/?#\s]+)", url)
        return match.group(1) if match else url.split('/')[-1]
    return url

# --- UI Setup ---
st.set_page_config(page_title="Reverb Guardian", page_icon="🛡️")
st.title("🛡️ Reverb Guardian: Nuclear Mode")
st.markdown("Forcing discovery of 'ghost' listings that hide from standard API calls.")

with st.sidebar:
    st.header("1. Authentication")
    api_token = st.text_input("Reverb API Token", type="password")
    
    st.header("2. Settings")
    report_reason = "scam" 
    dry_run = st.checkbox("Dry Run (Safe Mode)", value=True)
    delay = st.slider("Request Delay (Seconds)", 1, 10, 2)

seller_url = st.text_input("Target Shop Link or Slug", placeholder="gilmars-shop-5")

if st.button("☢️ Launch Nuclear Discovery"):
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

        # --- STEP 1: CROSS-REGION GLOBAL SEARCH ---
        st.info(f"Scanning ALL global regions for keyword: **{slug}**...")
        
        # We query the global 'all' endpoint which is less prone to shop-specific API ghosting.
        # We also manually specify common shipping regions to force results.
        params = {
            "query": slug,
            "state": "live",
            "shipping_region": "all", # Key to finding regional-locked scammers
            "per_page": 50
        }
        
        try:
            # Try the general listings endpoint first
            response = requests.get(f"{REVERB_API_BASE}/listings/all", headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                raw_listings = data.get("_embedded", {}).get("listings", [])
                
                # Manual validation: We match the shop slug OR the shop name in the data
                target_items = [
                    item for item in raw_listings 
                    if slug.lower() in item.get('shop', {}).get('slug', '').lower() 
                    or slug.lower() in item.get('shop', {}).get('name', '').lower()
                ]

                if not target_items:
                    # Final attempt: Search for the exact shop name as a string
                    st.info("No slug match. Trying literal shop name search...")
                    params["shop_name"] = slug
                    del params["query"]
                    response = requests.get(f"{REVERB_API_BASE}/listings/all", headers=headers, params=params)
                    target_items = response.json().get("_embedded", {}).get("listings", []) if response.status_code == 200 else []

                if target_items:
                    st.success(f"🎯 Target Found! {len(target_items)} listings exposed.")
                    
                    progress = st.progress(0)
                    for idx, item in enumerate(target_items):
                        l_id = item.get("id")
                        title = item.get("title")
                        
                        if dry_run:
                            st.info(f"🔍 [DRY RUN] Would report: **{title}** (ID: {l_id})")
                        else:
                            flag_url = f"{REVERB_API_BASE}/listings/{l_id}/flags"
                            payload = {"reason": report_reason, "description": "Coordinated scam patterns detected."}
                            f_resp = requests.post(flag_url, json=payload, headers=headers)
                            
                            if f_resp.status_code in [200, 201, 204]:
                                st.write(f"🚩 Reported: {title}")
                            else:
                                st.error(f"Failed {l_id}: {f_resp.status_code}")
                        
                        progress.progress((idx + 1) / len(target_items))
                        time.sleep(delay)
                    
                    st.balloons()
                else:
                    st.error("❌ Even Nuclear Discovery failed.")
                    st.markdown("""
                    **Possible Reasons:**
                    1. **The 'Ships To' mismatch:** Your API token's account is set to a country the scammer has blocked.
                    2. **Private API Token:** Ensure your token has 'Public' scopes enabled in your Reverb Profile.
                    3. **The Slug is different:** Double-check the URL. If it's `reverb.com/shop/user-1234`, use `user-1234`.
                    """)
            else:
                st.error(f"API Error {response.status_code}: {response.text}")

        except Exception as e:
            st.error(f"Fatal Error: {str(e)}")
