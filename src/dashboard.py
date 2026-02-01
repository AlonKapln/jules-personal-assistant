import streamlit as st
import sys
import os

# Ensure src is in path if running directly
sys.path.append(os.getcwd())

from src.config import config

st.set_page_config(
    page_title="Kernel Dashboard",
    page_icon="🤖",
    layout="centered"
)

# Custom CSS for Google-like feel
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
        font-family: 'Roboto', sans-serif;
    }
    h1 {
        color: #202124;
    }
    .stButton>button {
        background-color: #1a73e8;
        color: white;
        border-radius: 4px;
        border: none;
    }
    .stButton>button:hover {
        background-color: #1557b0;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🤖 Kernel Settings")

st.markdown("Configure Kernel's behavior and personality.")

# Reload config to ensure we have latest
config.reload_settings()

with st.form("settings_form"):
    st.subheader("General Settings")

    col1, col2 = st.columns(2)
    with col1:
        ai_filtering = st.checkbox(
            "Enable AI Email Filtering",
            value=config.get_setting("ai_email_filtering", True),
            help="If enabled, Gemini will analyze emails for importance. If disabled, all unread emails trigger alerts."
        )

    with col2:
        poll_interval = st.number_input(
            "Polling Interval (minutes)",
            min_value=1,
            max_value=60,
            value=int(config.get_setting("email_check_interval_minutes", 5)),
            help="Note: Changing this requires restarting the bot."
        )

    st.subheader("Brain Configuration")

    system_prompt = st.text_area(
        "System Prompt (Personality)",
        value=config.get_setting("system_prompt", ""),
        height=150,
        help="Instructions for how the bot should behave and speak."
    )

    importance_criteria = st.text_area(
        "Email Importance Criteria",
        value=config.get_setting("importance_criteria", ""),
        height=100,
        help="Criteria used by Gemini to decide if an email is important."
    )

    submitted = st.form_submit_button("Save Changes")

    if submitted:
        config.update_setting("ai_email_filtering", ai_filtering)
        config.update_setting("email_check_interval_minutes", poll_interval)
        config.update_setting("system_prompt", system_prompt)
        config.update_setting("importance_criteria", importance_criteria)

        st.success("Settings saved! The bot will update on the next poll cycle.")

st.markdown("---")
st.caption("Running locally on your machine.")
