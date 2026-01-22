"""
SmartSense - Unified Single Page App
Upload properties and chat with the bot on one page
"""

import streamlit as st
from pathlib import Path
import html
from utils import upload_excel, check_api_health, send_chat_message, clear_chat_history, get_preferences

# Page configuration
st.set_page_config(
    page_title="SmartSense - Real Estate Search Engine",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #1976d2;
        color: #000000;
    }
    .bot-message {
        background-color: #f5f5f5;
        border-left: 4px solid #4caf50;
        color: #000000;
    }
    .intent-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        background-color: #fff3cd;
        color: #856404;
        font-size: 0.85rem;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "user_id" not in st.session_state:
    st.session_state.user_id = "default_user"

if "data_uploaded" not in st.session_state:
    st.session_state.data_uploaded = False

if "message_input" not in st.session_state:
    st.session_state.message_input = ""

# Sidebar
with st.sidebar:
    # API Status
    api_status = check_api_health()
    if api_status:
        st.success("✅ API Connected")
    else:
        st.error("❌ API Offline")
        st.caption("Start backend: `uvicorn scripts.api:app --reload --port 8000`")
    
    st.markdown("---")
    
    # Reports Section
    st.markdown("### 📊 Generated Reports")
    reports_dir = Path("reports")
    if reports_dir.exists():
        report_files = sorted(reports_dir.glob("*.pdf"), key=lambda x: x.stat().st_mtime, reverse=True)
        
        if report_files:
            st.caption(f"Found {len(report_files)} report(s)")
            for report in report_files[:10]:  # Show last 10 reports
                with open(report, "rb") as f:
                    st.download_button(
                        label=f"📄 {report.name}",
                        data=f,
                        file_name=report.name,
                        mime="application/pdf",
                        key=f"download_{report.name}"
                    )
        else:
            st.caption("No reports generated yet")
    else:
        st.caption("No reports directory found")
    
    st.markdown("---")
    
    # Saved Preferences
    st.markdown("### 💾 Saved Preferences")
    prefs_result = get_preferences(st.session_state.user_id)
    preferences = prefs_result.get("preferences", {})
    
    if preferences:
        for key, value in preferences.items():
            st.caption(f"**{key}:** {value}")
    else:
        st.caption("No preferences saved yet")
    
    st.markdown("---")
    
    # Clear conversation button
    if st.button("🗑️ Clear Conversation", width="stretch"):
        result = clear_chat_history(st.session_state.user_id)
        st.session_state.messages = []
        st.success("Conversation cleared!")
        st.rerun()

# Main content
st.markdown('<div class="main-header">🏠 SmartSense</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Real Estate Search Engine with Multi-Agent Chatbot</div>', unsafe_allow_html=True)

# ===================== UPLOAD SECTION =====================
st.markdown("## 📁 Upload Properties")

uploaded_file = st.file_uploader(
    "Choose an Excel file to populate the database",
    type=['xlsx', 'xls'],
    help="Upload a file in the same format as Property_list.xlsx"
)

if uploaded_file is not None:
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("🚀 Upload & Process", type="primary", width="stretch"):
            if not api_status:
                st.error("❌ API is not running. Please start the backend first.")
            else:
                # Show progress with stages
                with st.spinner("Running ETL Pipeline..."):
                    progress_text = st.empty()
                    
                    # Upload and process
                    result = upload_excel(uploaded_file)
                    
                    progress_text.empty()
                
                # Display result
                if result.get("status") == "success":
                    st.session_state.data_uploaded = True
                    st.markdown(f"""
                    <div class="success-box">
                        <h3>✅ Success!</h3>
                        <p><strong>Properties Ingested:</strong> {result.get('properties_ingested', 0)}</p>
                        <p>{result.get('message', '')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    st.balloons()
                else:
                    st.markdown(f"""
                    <div class="error-box">
                        <h3>❌ Error</h3>
                        <p>{result.get('message', 'Unknown error occurred')}</p>
                    </div>
                    """, unsafe_allow_html=True)

# Add spacing between upload section and instructions
st.markdown("<br>", unsafe_allow_html=True)

st.info("📝 **Instructions:** Upload your Excel file → Wait for processing → Ask questions below")

st.markdown("---")

# ===================== CHATBOT SECTION =====================
# Only show chatbot after data is uploaded
if st.session_state.data_uploaded:
    st.markdown("## 💬 Chat with SmartSense")

    # Display chat messages
    chat_container = st.container()

    with chat_container:
        if not st.session_state.messages:
            st.info("""
            👋 **Welcome! I can help you with:**
            - 🔍 Search for properties (e.g., "Find 2BHK in Mumbai under 50 lakh")
            - 💰 Estimate renovation costs (e.g., "Estimate renovation for 1200 sqft")
            - 📊 Generate comparison reports
            - 💾 Save your preferences
            - 🌐 Get current market rates
            """)
        else:
            for message in st.session_state.messages:
                if message["role"] == "user":
                    escaped_content = html.escape(message["content"])
                    st.markdown(f"""
                    <div class="chat-message user-message">
                        <strong>You:</strong><br>
                        {escaped_content}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    intent_badge = ""
                    if message.get("intent"):
                        intent_badge = f'<span class="intent-badge">Intent: {message["intent"]}</span>'
                    
                    sources_text = ""
                    if message.get("sources"):
                        sources_list = ', '.join(message['sources'])
                        sources_text = f"<br><small><strong>Sources:</strong> {sources_list}</small>"
                    
                    escaped_content = html.escape(message["content"]).replace('\n', '<br>')
                    
                    st.markdown(f"""
                    <div class="chat-message bot-message">
                        <strong>Bot:</strong><br>
                        {escaped_content}
                        {sources_text}
                        {intent_badge}
                    </div>
                    """, unsafe_allow_html=True)

    # Chat input with Enter key support
    def send_message():
        user_input = st.session_state.message_input
        
        if user_input and user_input.strip():
            if not api_status:
                st.error("❌ API is not running. Please start the backend first.")
            else:
                # Add user message
                st.session_state.messages.append({
                    "role": "user",
                    "content": user_input
                })
                
                # Get bot response
                response = send_chat_message(st.session_state.user_id, user_input)
                
                # Add bot response
                st.session_state.messages.append({
                    "role": "bot",
                    "content": response.get("response", "No response"),
                    "intent": response.get("intent"),
                    "sources": response.get("sources")
                })
                
                # Clear input
                st.session_state.message_input = ""

    col1, col2 = st.columns([5, 1])

    with col1:
        st.text_input(
            "Type your message and press Enter...",
            key="message_input",
            placeholder="Ask me about properties, prices, renovations...",
            label_visibility="collapsed",
            on_change=send_message
        )

    with col2:
        if st.button("Send 📤", type="primary", width="stretch"):
            send_message()
else:
    # Show message when chatbot is not yet available
    st.markdown("## 💬 Chat with SmartSense")
    st.info("🔒 **Chatbot locked.** Please upload property data first to start chatting.")

# Footer
st.markdown("---")
st.caption(f"👤 User: **{st.session_state.user_id}** | 💬 Messages: {len(st.session_state.messages)} | 🚀 SmartSense Phase 3")


