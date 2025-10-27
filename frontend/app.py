# frontend/app.py
import streamlit as st
import requests
import os
import time
import tempfile
from pathlib import Path
from typing import Optional, List
import logging
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("frontend")

# Configuration
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")
API_BASE = f"{BACKEND_API_URL}/api/v1"

# Parker Tide brand styling
st.markdown("""
<style>
    /* Professional font family (Inter with system fallbacks) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

    :root {
        /* Parker Tide brand palette */
        --brand-navy: #04395E;   /* dark navy */
        --brand-navy-600: #0A2E4D; 
        --brand-cyan: #00A3E0;   /* bright cyan */
        --brand-cyan-100: #E6F6FD; /* light background tint */
        --app-font: 'Inter', 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', 'Liberation Sans', sans-serif;
    }

    html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {
        font-family: var(--app-font) !important;
    }

    .main-header {
        background: linear-gradient(90deg, var(--brand-navy) 0%, var(--brand-navy-600) 55%, var(--brand-cyan) 100%);
        padding: 1.25rem 1.5rem;
        border-radius: 10px;
        margin-bottom: 1.25rem;
        color: #ffffff;
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .main-header img {
        height: 48px;
    }

    /* Ensure header can host positioned elements */
    .main-header { position: relative; }

    /* Logo contrast badge to avoid gradient wash-out */
    .main-header .logo-badge {
        background: rgba(255,255,255,0.92);
        backdrop-filter: blur(2px) saturate(120%);
        -webkit-backdrop-filter: blur(2px) saturate(120%);
        border-radius: 10px;
        padding: 6px 10px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.08);
        display: flex;
        align-items: center;
    }
    .main-header .logo-badge img { height: 48px; display: block; }

    /* Reusable card header bar */
    .card-header {
        background: linear-gradient(90deg, var(--brand-navy) 0%, var(--brand-navy-600) 55%, var(--brand-cyan) 100%);
        color: #ffffff;
        font-weight: 800;
        font-size: 1.6rem; /* larger header font */
        padding: 0.9rem 1.15rem;
        border-radius: 10px;
        margin-bottom: 0.7rem;
        display: flex;
        align-items: center;
        gap: 0.65rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.06);
        letter-spacing: 0.2px;
    }

    .status-card {
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        text-align: center;
    }
    .status-queued { background: #e3f2fd; border-left: 4px solid #2196f3; }
    .status-running { background: #fff3e0; border-left: 4px solid #ff9800; }
    .status-completed { background: #e8f5e8; border-left: 4px solid #4caf50; }
    .status-failed { background: #ffebee; border-left: 4px solid #f44336; }

    .upload-area {
        border: 2px dashed var(--brand-cyan);
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        background: var(--brand-cyan-100);
        margin: 1rem 0;
    }

    .stButton > button {
        background: linear-gradient(90deg, var(--brand-cyan) 0%, #15b6ef 100%);
        color: #ffffff;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.2s ease-in-out;
    }
    .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 4px 14px rgba(0,163,224,0.35); }

    /* Style Streamlit's top header to match brand */
    header[data-testid="stHeader"] {
        background: linear-gradient(90deg, var(--brand-navy) 0%, var(--brand-navy-600) 55%, var(--brand-cyan) 100%);
    }
    header[data-testid="stHeader"] * { color: #ffffff !important; }
</style>
""", unsafe_allow_html=True)

# Page config
st.set_page_config(
    page_title="RFP Compliance Matrix Generator",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

def check_backend_health() -> bool:
    """Check if backend API is available."""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        return response.status_code == 200
    except Exception as e:
        log.error(f"Backend health check failed: {e}")
        return False

def submit_job(opportunity_id: str, custom_filename: str, use_highergov: bool, blob_urls: List[str] = None) -> Optional[str]:
    """Submit a job to the backend API."""
    try:
        payload = {
            "opportunity_id": opportunity_id,
            "custom_filename": custom_filename,
            "use_highergov": use_highergov,
            "blob_urls": blob_urls or []
        }
        
        response = requests.post(f"{API_BASE}/jobs/submit", json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return result["job_id"]
        
    except Exception as e:
        st.error(f"Failed to submit job: {str(e)}")
        log.error(f"Job submission failed: {e}")
        return None

def get_job_status(job_id: str) -> Optional[dict]:
    """Get job status from backend API."""
    try:
        response = requests.get(f"{API_BASE}/jobs/{job_id}/status", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        log.error(f"Failed to get job status: {e}")
        return None

def get_job_results(job_id: str) -> Optional[dict]:
    """Get job results from backend API."""
    try:
        response = requests.get(f"{API_BASE}/jobs/{job_id}/results", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        log.error(f"Failed to get job results: {e}")
        return None

def upload_files_to_blob(files: List[bytes], filenames: List[str]) -> List[str]:
    """Upload files to Azure Blob Storage and return URLs."""
    # For now, return mock URLs - in production, implement actual blob upload
    return [f"https://mock-blob-url.com/{filename}" for filename in filenames]

# Main UI
def main():
    # Header
    # Build header with optional logo
    logo_path = os.getenv("COMPANY_LOGO_PATH", "static/logo.png")
    logo_url = os.getenv("COMPANY_LOGO_URL")
    logo_img_tag = ""
    try:
        if logo_url:
            logo_img_tag = f'<img src="{logo_url}" alt="Company Logo" />'
        elif Path(logo_path).exists():
            # Embed the local logo as base64 so it renders in the browser
            mime = "image/svg+xml" if str(logo_path).lower().endswith(".svg") else "image/png"
            with open(logo_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
            logo_img_tag = f'<img src="data:{mime};base64,{encoded}" alt="Company Logo" />'
    except Exception:
        logo_img_tag = ""

    st.markdown(
        f"""
        <div class="main-header">
            {f'<div class="logo-badge">{logo_img_tag}</div>' if logo_img_tag else ''}
            <div>
                <h1 style="margin: 0;">RFP Compliance Matrix Generator</h1>
                <p style="margin: 0; opacity: 0.9;">Transform government RFPs into compliance matrices with AI-powered extraction</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Backend health check
    if not check_backend_health():
        st.error("⚠️ Backend API is not available. Please ensure the backend service is running.")
        st.stop()
    
    # Sidebar for job history
    with st.sidebar:
        st.markdown("### 📊 Job History")
        if "job_history" not in st.session_state:
            st.session_state.job_history = []
        
        if st.session_state.job_history:
            for job in reversed(st.session_state.job_history[-5:]):  # Show last 5 jobs
                with st.expander(f"Job {job['job_id'][:8]}..."):
                    st.write(f"**Status:** {job['status']}")
                    st.write(f"**Created:** {job['created_at']}")
                    if job.get('file_count'):
                        st.write(f"**Requirements:** {job['file_count']}")
        else:
            st.info("No jobs submitted yet")
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Card 1: Job submission and output settings
        with st.container(border=True):
            st.markdown('<div class="card-header">➕ Submit New Job</div>', unsafe_allow_html=True)

            # Input method selection
            input_method = st.radio(
                "Choose input method:",
                options=["HigherGov Opportunity ID", "Manual File Upload"],
                horizontal=True,
                index=1,  # Default to Manual File Upload
                help="Select how you want to provide documents for processing",
            )

            use_highergov = input_method == "HigherGov Opportunity ID"

            # HigherGov API key check
            has_highergov_key = bool(os.getenv("HIGHERGOV_API_KEY"))
            if use_highergov and not has_highergov_key:
                st.error("⚠️ HigherGov API key not configured. Add `HIGHERGOV_API_KEY` to your environment.")
                st.stop()

            # Output settings
            st.subheader("Matrix File Name")
            custom_filename = st.text_input(
                "Custom filename (optional):",
                placeholder="my-proposal-compliance-matrix",
                help="Custom name for the output Excel file",
            )

        # Card 2: Provide documents
        with st.container(border=True):
            st.markdown('<div class="card-header">📁 Provide Documents</div>', unsafe_allow_html=True)

            opportunity_id = None
            uploaded_files = []
            blob_urls = []

            if use_highergov:
                st.subheader("HigherGov Integration")
                opportunity_id = st.text_input(
                    "Opportunity ID:",
                    placeholder="e.g., abc123xyz or SAM notice ID",
                    help="Enter the opportunity ID from HigherGov or SAM.gov",
                )

                if opportunity_id:
                    st.success(f"✓ Opportunity ID: {opportunity_id}")
            else:
                st.subheader("Manual File Upload")
                st.markdown('<div class="upload-area">', unsafe_allow_html=True)
                uploaded_files = st.file_uploader(
                    "Upload PDF, Word, or Excel files:",
                    type=["pdf", "docx", "doc", "xlsx", "xls"],
                    accept_multiple_files=True,
                    help="Upload documents to extract requirements from",
                )
                st.markdown('</div>', unsafe_allow_html=True)

                if uploaded_files:
                    st.success(f"✓ {len(uploaded_files)} file(s) selected")
                    with st.expander("📋 Uploaded Files"):
                        for file in uploaded_files:
                            file_size_mb = len(file.getvalue()) / (1024 * 1024)
                            st.write(f"• {file.name} ({file_size_mb:.2f} MB)")

                    # Upload to blob storage (mock implementation)
                    if st.button("📤 Upload to Cloud Storage"):
                        with st.spinner("Uploading files..."):
                            filenames = [f.name for f in uploaded_files]
                            blob_urls = upload_files_to_blob([f.getvalue() for f in uploaded_files], filenames)
                            st.success("✓ Files uploaded successfully")
    
    with col2:
        with st.container(border=True):
            st.markdown('<div class="card-header">⚙️ Processing</div>', unsafe_allow_html=True)

            # Validate inputs
            can_process = False
            if use_highergov:
                can_process = bool(opportunity_id and opportunity_id.strip())
            else:
                can_process = bool(uploaded_files or blob_urls)

            if not can_process:
                st.info("👆 Please provide documents to process")
            else:
                # Process button
                if st.button("🚀 Extract Requirements", type="primary", disabled=not can_process):
                    # Generate opportunity ID for manual uploads
                    if not opportunity_id:
                        opportunity_id = f"manual-upload-{int(time.time())}"

                    # Submit job
                    with st.spinner("Submitting job..."):
                        job_id = submit_job(opportunity_id, custom_filename, use_highergov, blob_urls)

                    if job_id:
                        st.session_state.current_job_id = job_id
                        st.session_state.job_history.append({
                            "job_id": job_id,
                            "status": "queued",
                            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "opportunity_id": opportunity_id,
                        })
                        st.success(f"✅ Job submitted successfully! Job ID: {job_id[:8]}...")
                        st.rerun()
    
    # Job status monitoring
    if "current_job_id" in st.session_state:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.header("📊 Job Status")
        
        job_id = st.session_state.current_job_id
        status_data = get_job_status(job_id)
        
        if status_data:
            status = status_data["status"]
            progress = status_data.get("progress", 0)
            message = status_data.get("message", "")
            
            # Status card
            status_class = f"status-{status}"
            st.markdown(f"""
            <div class="status-card {status_class}">
                <h3>Status: {status.upper()}</h3>
                <p>{message}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Progress bar
            if status in ["queued", "running"]:
                st.progress(progress / 100)
                st.info(f"Progress: {progress:.1f}%")
                
                # Auto-refresh for running jobs
                if status == "running":
                    time.sleep(2)
                    st.rerun()
            
            # Results display
            if status == "completed":
                results = get_job_results(job_id)
                if results and results.get("sas_url"):
                    st.success("🎉 Processing completed successfully!")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Requirements Extracted", results.get("file_count", 0))
                    with col2:
                        st.metric("Job ID", job_id[:8])
                    
                    # Download button
                    st.markdown(f"""
                    <a href="{results['sas_url']}" target="_blank" style="text-decoration: none;">
                        <button style="background: linear-gradient(90deg, #4caf50 0%, #45a049 100%); color: white; border: none; padding: 1rem 2rem; border-radius: 8px; font-size: 1.1rem; cursor: pointer; width: 100%;">
                            📥 Download Compliance Matrix
                        </button>
                    </a>
                    """, unsafe_allow_html=True)
                    
                    # Clear current job
                    if st.button("🔄 Process New Job"):
                        del st.session_state.current_job_id
                        st.rerun()
            
            elif status == "failed":
                st.error("❌ Processing failed")
                if status_data.get("error_message"):
                    st.error(f"Error: {status_data['error_message']}")
                
                if st.button("🔄 Try Again"):
                    del st.session_state.current_job_id
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
