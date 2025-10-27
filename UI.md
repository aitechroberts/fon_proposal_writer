## UI Guidelines and Best Practices

This document summarizes the UI decisions and patterns used in the Streamlit frontend (`frontend/app.py`) and how to extend them safely.

### Branding and Theme
- **Primary palette**: Navy `#04395E`, Navy-600 `#0A2E4D`, Cyan `#00A3E0`, Light Cyan `#E6F6FD`.
- **Streamlit theme**: Configured in `frontend/.streamlit/config.toml` to align default accents and text with Parker Tide colors.
- **CSS variables**: Colors are defined as CSS variables for consistency and easy updates.

### Typography
- **Font stack**: Inter (via Google Fonts) with professional system fallbacks: `Inter, Segoe UI, Roboto, Helvetica Neue, Arial, Noto Sans, Liberation Sans, sans-serif`.
- **Global application**: Applied to the Streamlit app container and sidebar for consistency.

### Header and Logo
- **Gradient header**: A brand gradient (navy → cyan) provides a distinctive masthead.
- **Logo badge**: The logo is wrapped in a semi‑opaque white "badge" with subtle blur to ensure contrast over any background.
  - Advantages: Works for light/dark logo regions without swapping gradient sides.
- **Logo sourcing**:
  - Local (preferred for dev): place `frontend/static/logo.png`.
  - Or set `COMPANY_LOGO_PATH` (path) / `COMPANY_LOGO_URL` (hosted) env vars.
  - Local assets are embedded as Base64 data URIs to render reliably in the browser.

### Card Structure
- **Use `st.container(border=True)`** for cards. Avoid raw HTML wrappers that open/close tags across multiple Streamlit calls (can create blank artifacts).
- **Card headers**: Reusable `.card-header` with brand gradient, white text, and subtle shadow for clear visual grouping.
  - Font size increased for hierarchy and scannability.

### Inputs and Defaults
- **Default input method**: Radio defaults to “Manual File Upload” to optimize for the most common path.
- **Field labeling**: Explicit labels like “Matrix File Name” to clarify purpose.
- **Help text**: Concise `help=` on interactive widgets to reduce confusion.

### Upload Experience
- **Dropzone styling**: Dashed cyan border with light cyan background for strong affordance.
- **Progress and feedback**: Success messages after file selection and mock upload confirmation for clarity.

### Status and Feedback
- **Status cards**: `.status-{queued|running|completed|failed}` with distinct colors and left accents.
- **Processing panel**: Validates inputs and disables submit until ready; uses progress indicators and messages.

### Layout
- **Wide layout** with a 2:1 column split (`col1` for inputs, `col2` for processing/status) to minimize vertical scrolling.
- **Sidebar** for recent job history without cluttering the main flow.

### Accessibility and Usability
- **Contrast**: Navy/white and cyan/white meet contrast expectations for headers and buttons.
- **Hit targets**: Large buttons and header sizes improve usability.
- **Icons**: Decorative; text remains the primary label (e.g., ➕ Submit New Job).

### Performance and Safety
- **Embedded images**: Base64 data URIs reduce path issues and improve reliability in containerized environments.
- **Minimal custom HTML**: Used sparingly with `unsafe_allow_html=True`; no nested widgets inside raw HTML to avoid interaction issues.

### Extending the UI
- To add a new card:
  1. Create a bordered container.
  2. Add a `.card-header` title.
  3. Place widgets inside the same container block.

```python
with st.container(border=True):
    st.markdown('<div class="card-header">📂 New Section</div>', unsafe_allow_html=True)
    # ... widgets ...
```

### Configuration Quick Reference
- Theme: `frontend/.streamlit/config.toml`.
- Logo: `frontend/static/logo.png`, or set `COMPANY_LOGO_PATH` / `COMPANY_LOGO_URL`.
- Colors/Styles: CSS block in `frontend/app.py` under “Parker Tide brand styling”.

### Rationale Summary
- Prioritize clarity, contrast, and predictability.
- Keep Streamlit-native containers for structure; use CSS for polish.
- Brand consistently through theme, typography, and headers without sacrificing readability.


