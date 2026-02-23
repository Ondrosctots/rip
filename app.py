import streamlit as st
import time
import re
import urllib.parse

def clean_id_list(input_text):
    """Extracts all 7-10 digit numbers from text."""
    return re.findall(r'(\d{7,10})', input_text)

# --- UI Setup ---
st.set_page_config(page_title="Reverb Guardian", page_icon="🛡️")
st.title("🛡️ Reverb Guardian: Support Bypass Mode")

st.markdown("""
### ⚠️ Why are you getting 404?
The Reverb API is blocking your account from "seeing" these scam listings because they are likely **region-locked**. 
However, you can still report them manually using the **Direct Support Links** generated below.
""")

with st.sidebar:
    st.header("1. Settings")
    report_reason = st.selectbox("Reason", ["Fraudulent Listing", "Off-site Transaction", "Stolen Photos"])
    delay = st.slider("Link Generation Delay", 0.1, 2.0, 0.5)

# --- Input Area ---
raw_input = st.text_area("Paste Listing IDs or URLs here:", height=200, placeholder="94627157, https://reverb.com/item/94627157...")

if st.button("🔗 Generate Direct Report Links"):
    if not raw_input.strip():
        st.error("Please paste at least one ID.")
    else:
        found_ids = list(set(clean_id_list(raw_input)))
        
        if not found_ids:
            st.error("❌ No valid IDs found.")
        else:
            st.success(f"✅ Generated {len(found_ids)} human-readable report links.")
            
            st.info("Click each link below to open the official Reverb report page with the ID pre-loaded. This bypasses the API 404 error.")
            
            for idx, l_id in enumerate(found_ids):
                # Constructing the manual report URL
                # Note: Reverb often uses a help center ticket or the listing page itself for reports
                report_url = f"https://reverb.com/item/{l_id}"
                support_query = urllib.parse.quote(f"Reporting fraudulent listing {l_id}. Reason: {report_reason}")
                direct_help_url = f"https://help.reverb.com/hc/en-us/requests/new?ticket_form_id=360000325514&tf_subject=Scam+Report+{l_id}&tf_description={support_query}"
                
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.write(f"**ID: {l_id}**")
                with col2:
                    st.link_button(f"🚩 Open Report Form", direct_help_url)
                
                time.sleep(delay)
            
            st.balloons()
