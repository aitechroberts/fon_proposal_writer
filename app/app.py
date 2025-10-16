# app.py - Updated with HigherGov integration
import streamlit as st
import os
from pathlib import Path
import tempfile
import shutil
import logging
from main import process_opportunity, import_from_highergov_and_process

_LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, _LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logging.getLogger("azure").setLevel(logging.WARNING)
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)

log = logging.getLogger("app")
log.info("Streamlit logging initialized")

# ============= Streamlit App =============
# Page config
st.set_page_config(
    page_title="RFP Compliance Matrix Generator",
    # layout="wide"
)

st.title("RFP Compliance Matrix Generator")
st.markdown("Connect to HigherGov API or upload PDF, Word, or Excel")

# Check for HigherGov API key
try:
    has_highergov_key = bool(os.getenv("HIGHERGOV_API_KEY"))
except Exception:
    has_highergov_key = False
    log.info("No HigherGov API key found in environment")

st.divider()

# ============= Input Method =============
st.header("1. Choose Input Method")

input_method = st.radio(
    "How would you like to provide documents?",
    options=["HigherGov Opportunity ID", "Manual File Upload"],
    index=0 if has_highergov_key else 1,
    horizontal=True,
)

use_highergov = (input_method == "HigherGov Opportunity ID")

if use_highergov and not has_highergov_key:
    st.error(
        "⚠️ HigherGov API key not configured. "
        "Add `HIGHERGOV_API_KEY=your-key-here` to your .env file."
    )
    st.info("Get Jonathan to integrate API Key")
    st.stop()

st.subheader("Output Settings")
custom_filename = st.text_input(
    "Output Filename (optional)",
    value="",
    placeholder="my-proposal-compliance-matrix",
    help="Custom name for the output Excel file. If empty, will use opportunity ID."
)

st.divider()

# ============= Input Fields =============
st.header("2. Provide Documents")

opportunity_id = None
uploaded_files = []

if use_highergov:
    # HigherGov ID input
    st.subheader("HigherGov Opportunity ID")
    
    opportunity_id = st.text_input(
        "Opportunity ID",
        placeholder="e.g., abc123xyz or SAM notice ID",
        help="Enter the opportunity ID from HigherGov or SAM.gov"
    )

    preview_clicked = st.button(
        "Preview Opportunity Details",
        type="secondary",
        disabled=not opportunity_id
    )

    # Preview opportunity details
    if preview_clicked and opportunity_id:
        try:
            from src.integrations.highergov import get_opportunity_preview
            
            with st.spinner("Fetching opportunity details..."):
                preview = get_opportunity_preview(opportunity_id.strip())
            
            # Display preview in info box
            st.success("✓ Opportunity found!")
            st.info(
                f"**{preview['title']}**\n\n"
                f"**Agency:** {preview['agency']}  \n"
                f"**Posted:** {preview['posted']} | **Due:** {preview['due']}  \n"
                f"**NAICS:** {preview['naics']} | **Set-Aside:** {preview['set_aside']}  \n"
                f"**Documents:** {preview['docs']} attachments"
            )
        
        except Exception as e:
            st.error(f"Failed to fetch opportunity: {str(e)}")
            st.info(
                "**Troubleshooting:**\n"
                "- Double-check the opportunity ID\n"
                "- Verify your API key is valid\n"
                "- Ensure opportunity is accessible with your account"
            )

else:
    # Manual file upload
    st.subheader("Upload Documents Manually")
    
    uploaded_files = st.file_uploader(
        "Upload PDF, Word, or Excel files",
        type=["pdf", "docx", "doc", "xlsx", "xls"],
        accept_multiple_files=True,
        help="Upload documents to extract requirements from"
    )
    
    if uploaded_files:
        st.success(f"✓ {len(uploaded_files)} file(s) selected")
        with st.expander("Uploaded Files"):
            for file in uploaded_files:
                file_size_mb = len(file.getvalue()) / (1024 * 1024)
                st.write(f"- {file.name} ({file_size_mb:.2f} MB)")

st.divider()

# ============= Processing =============
st.header("3. Process Documents")

# Validate inputs
can_process = False
if use_highergov:
    can_process = bool(opportunity_id and opportunity_id.strip())
else:
    can_process = bool(uploaded_files)

# Process button
process_clicked = st.button(
    "🚀 Extract Requirements",
    type="primary",
    disabled=not can_process,
)

if process_clicked:
    try:
        if use_highergov:
            # HigherGov workflow
            st.info("📥 Downloading documents from HigherGov...")
            
            with st.spinner("Fetching documents from HigherGov API..."):
                # This downloads files and processes them
                output_name = custom_filename.strip() if custom_filename.strip() else opportunity_id
                sas_url = process_opportunity(opportunity_id, output_name=output_name)
            
            st.success("✅ Processing complete!")
            
        else:
            # Manual upload workflow
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                st.info("📁 Processing uploaded files...")
                
                opportunity_id = "manual-upload"
                output_dir = Path("data/inputs") / opportunity_id
                output_dir.mkdir(parents=True, exist_ok=True)
                
                # Save uploaded files
                for uploaded_file in uploaded_files:
                    file_path = output_dir / uploaded_file.name
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getvalue())
                
                st.success(f"✓ Saved {len(uploaded_files)} file(s)")
                
                # Process documents
                st.info("⚙️ Extracting requirements...")
                
                with st.spinner("Processing documents with AI... This may take several minutes."):
                    sas_url = process_opportunity(opportunity_id)
                
                st.success("✅ Processing complete!")
                
                # Cleanup option
                if st.button("🗑️ Clear for new opportunity"):
                    shutil.rmtree(output_dir, ignore_errors=True)
                    st.rerun()
        
        # Download results (common for both workflows)
        st.markdown("### 📥 Download Results")
        st.markdown(
            f"[**⬇️ Download Excel Compliance Matrix**]({sas_url})",
            unsafe_allow_html=True
        )
        st.info("🔗 Link valid for 24 hours")
        st.download_button(
            label="Download Matrix",
            data=sas_url,
        )
    
    except Exception as e:
        st.error(f"❌ Processing failed: {str(e)}")
        
        # Provide helpful error messages
        error_str = str(e).lower()
        
        if "expired" in error_str or "60 min" in error_str:
            st.warning(
                "**Download links expired** (HigherGov URLs expire after 60 minutes)\n\n"
                "**Solution:** Click 'Extract Requirements' again to fetch fresh links."
            )
        elif "api key" in error_str or "401" in error_str or "403" in error_str:
            st.warning(
                "**API authentication issue**\n\n"
                "Check your HIGHERGOV_API_KEY in .env file and restart the app."
            )
        elif "not found" in error_str or "404" in error_str:
            st.warning(
                "**Opportunity not found**\n\n"
                "Double-check the opportunity ID. Try copying it directly from HigherGov URL."
            )
        
        with st.expander("🐛 Show full error"):
            st.exception(e)
