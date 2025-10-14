import streamlit as st
from main import process_opportunity
# 1) configure logging once per Streamlit session
if not st.session_state.get("_logging_ready"):
    from logging_config import setup_logging
    setup_logging(app_level="INFO", lib_level="ERROR")
    st.session_state["_logging_ready"] = True

# 2) now do your usual imports
import logging
from main import process_opportunity  # <- will inherit our config

log = logging.getLogger("app")

st.set_page_config(page_title="Compliance Matrix Generator", layout="centered")
st.title("📄Compliance Matrix Generator")
st.caption("Input an Opportunity ID from HigherGov and Click Submit to generate a compliance matrix Excel file.")

opportunity_id = st.text_input("Opportunity ID", placeholder="e.g., RFQ897983")

if st.button("Submit"):
    if not opportunity_id.strip():
        st.warning("Please enter an Opportunity ID.")
    else:
        with st.spinner("Running DSPy pipeline and generating Excel… this may take a bit."):
            try:
                download_url = process_opportunity(opportunity_id.strip())
            except Exception as e:
                st.error(f"Processing failed: {e}")
                st.stop()

        st.success("Compliance matrix generated!")
        st.markdown(f"✅ **[Download from Azure Blob]({download_url})**")
        # Browser notification (best-effort)
        st.markdown(
            """
            <script>
            if ('Notification' in window) {
                Notification.requestPermission().then(function (p) {
                    if (p === "granted") {
                        new Notification("Compliance matrix ready for download.");
                    }
                });
            }
            </script>
            """,
            unsafe_allow_html=True,
        )
