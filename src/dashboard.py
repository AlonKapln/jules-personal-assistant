import streamlit as st
import sys
import os
from datetime import datetime

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
    .stApp {
        font-family: 'Roboto', sans-serif;
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

    st.subheader("Daily Learning")

    col3, col4 = st.columns(2)
    with col3:
        wotd_enabled = st.checkbox(
            "Enable Word of the Day",
            value=config.get_setting("wotd_enabled", False)
        )

    with col4:
        # Parse existing time setting or default
        current_time_str = config.get_setting("wotd_time", "09:00")
        try:
            t = datetime.strptime(current_time_str, "%H:%M").time()
        except:
            t = datetime.strptime("09:00", "%H:%M").time()

        wotd_time = st.time_input(
            "Time for Word of the Day",
            value=t,
            help="Time to send the daily word (requires bot restart to apply change)."
        )

    learning_level = st.selectbox(
        "Learning Level",
        ["Beginner", "Intermediate", "Advanced", "Business", "Academic"],
        index=["Beginner", "Intermediate", "Advanced", "Business", "Academic"].index(config.get_setting("learning_level", "Intermediate"))
    )

    submitted = st.form_submit_button("Save Changes")

    if submitted:
        config.update_setting("ai_email_filtering", ai_filtering)
        config.update_setting("email_check_interval_minutes", poll_interval)
        config.update_setting("system_prompt", system_prompt)
        config.update_setting("importance_criteria", importance_criteria)

        config.update_setting("wotd_enabled", wotd_enabled)
        config.update_setting("wotd_time", wotd_time.strftime("%H:%M"))
        config.update_setting("learning_level", learning_level)

        st.success("Settings saved! The bot will update on the next poll cycle (restart required for schedule changes).")

st.markdown("---")
st.caption("Running locally on your machine.")
