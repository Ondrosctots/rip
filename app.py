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
        return match.group(1) if match else None
    return url

# --- UI Setup ---
st.set_page_config(page_title="Reverb Guardian", page_icon="🛡️")
st.title("🛡️ Reverb Guardian: Watchdog Mode")

with st.sidebar:
    st.header("1. Authentication")
    api_token = st.text_input("Reverb API Token", type="password")
    
    st.header("2. Settings")
    report_reason = "scam" 
    dry_run = st.checkbox("Dry Run (Safe Mode)", value=True)
    delay = st.slider("Check Interval (Minutes)", 1, 60, 5)
    
seller_url = st.text_input("Target Shop Slug/Link", placeholder="gilmars-shop-5")

# --- Logic ---
if st.button("📡 Start Watchdog"):
    slug = extract_shop_slug(seller_url)
    
    if not api_token or not slug:
        st.error("Missing Token or Shop Link!")
    else:
        st.success(f"Monitoring **{slug}** every {delay} minutes. Leave this tab open.")
        status_area = st.empty()
        log_area = st.empty()
        
        headers = {"Authorization": f"Bearer {api_token}", "Accept": "application/hal+json", "Accept-Version": "3.0"}
        
        while True:
            current_time = time.strftime("%H:%M:%S")
            status_area.info(f"Last Check: {current_time} | Status: Scanning...")
            
            try:
                # Targeted check
                res = requests.get(f"{REVERB_API_BASE}/listings/all?shop_name={slug}&state=live", headers=headers)
                items = res.json().get("_embedded", {}).get("listings", []) if res.status_code == 200 else []
                
                # Filter strictly for the slug
                matched = [i for i in items if i.get('shop', {}).get('slug') == slug]
                
                if matched:
                    st.warning(f"🚨 ALERT: Found {len(matched)} new listings at {current_time}!")
                    for item in matched:
                        lid, title = item.get("id"), item.get("title")
                        if not dry_run:
                            requests.post(f"{REVERB_API_BASE}/listings/{lid}/flags", 
                                          json={"reason": report_reason, "description": "Auto-reported by Guardian."}, 
                                          headers=headers)
                            st.write(f"✅ Auto-Reported: {title}")
                        else:
                            st.write(f"🔍 [DRY RUN] Found: {title}")
                else:
                    log_area.write(f"[{current_time}] Shop is still empty/suspended.")
                    
            except Exception as e:
                st.error(f"Error during scan: {e}")
            
            time.sleep(delay * 60) # Sleep for the user-defined interval
