#!/bin/bash
# Local development environment variables template
# Copy this to local_env.sh and update with your actual values

export USER_EMAIL="your_email@example.com"
export USER_PASSWORD="your_password"
export NUM_PARTICIPANTS="1"

export EARLIEST_ACCEPTABLE_DATE="2025-08-10"
export LATEST_ACCEPTABLE_DATE="2026-05-10"
export USER_CONSULATE="Toronto"

export GMAIL_SENDER_NAME="Visa Appointment Reminder"
export GMAIL_EMAIL="your_gmail@gmail.com"
export GMAIL_APPLICATION_PWD="your_16_char_app_password"
export RECEIVER_NAME="Your Name"
export RECEIVER_EMAIL="notifications@example.com"

export SHOW_GUI="true"  # Set to false for headless mode
export TEST_MODE="false"

# Optional: Session renewal settings (defaults are usually fine)
# export SESSION_RENEWAL_MAX_ATTEMPTS="3"
# export SESSION_RENEWAL_DELAY="5"

echo "Environment variables set for local development"
echo "Usage:"
echo "1. Copy this file: cp local_env.example.sh local_env.sh"
echo "2. Edit local_env.sh with your actual credentials"
echo "3. Run: source local_env.sh && python reschedule.py"