import os
from typing import Dict

# Account Info - use environment variables for security
USER_EMAIL = os.getenv("USER_EMAIL", "")
USER_PASSWORD = os.getenv("USER_PASSWORD", "")
NUM_PARTICIPANTS = int(os.getenv("NUM_PARTICIPANTS", "1"))

# Date preferences
EARLIEST_ACCEPTABLE_DATE = os.getenv("EARLIEST_ACCEPTABLE_DATE", "2025-08-10")
LATEST_ACCEPTABLE_DATE = os.getenv("LATEST_ACCEPTABLE_DATE", "2026-05-10")

# Consulate configuration
CONSULATES: Dict[str, int] = {
    "Calgary": 89,
    "Halifax": 90,
    "Montreal": 91,
    "Ottawa": 92,
    "Quebec": 93,
    "Toronto": 94,
    "Vancouver": 95,
}
USER_CONSULATE = os.getenv("USER_CONSULATE", "Toronto")

# Gmail notification settings
GMAIL_SENDER_NAME = os.getenv("GMAIL_SENDER_NAME", "Visa Appointment Reminder")
GMAIL_EMAIL = os.getenv("GMAIL_EMAIL", "")
GMAIL_APPLICATION_PWD = os.getenv("GMAIL_APPLICATION_PWD", "")

# Email notification receiver
RECEIVER_NAME = os.getenv("RECEIVER_NAME", "")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL", "")

# Cloud deployment settings
SHOW_GUI = os.getenv("SHOW_GUI", "false").lower() == "true"
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"

# Runtime configuration
DETACH = False  # Set to False for cloud deployment
NEW_SESSION_AFTER_FAILURES = int(os.getenv("NEW_SESSION_AFTER_FAILURES", "5"))
NEW_SESSION_DELAY = int(os.getenv("NEW_SESSION_DELAY", "60"))
TIMEOUT = int(os.getenv("TIMEOUT", "10"))
FAIL_RETRY_DELAY = int(os.getenv("FAIL_RETRY_DELAY", "30"))
DATE_REQUEST_DELAY = int(os.getenv("DATE_REQUEST_DELAY", "30"))
DATE_REQUEST_MAX_RETRY = int(os.getenv("DATE_REQUEST_MAX_RETRY", "1000"))
DATE_REQUEST_MAX_TIME = int(os.getenv("DATE_REQUEST_MAX_TIME", "1800"))  # 30 minutes

# Race condition handling settings
BOOKING_RETRY_ATTEMPTS = int(os.getenv("BOOKING_RETRY_ATTEMPTS", "3"))
BOOKING_RETRY_DELAY = int(os.getenv("BOOKING_RETRY_DELAY", "2"))
FAST_MODE = os.getenv("FAST_MODE", "true").lower() == "true"  # Reduce delays for faster response

# Cloud platform timeout (6 hours for GitHub Actions)
MAX_RUNTIME_SECONDS = int(os.getenv("MAX_RUNTIME_SECONDS", "21600"))  # 6 hours

# URLs and endpoints
LOGIN_URL = "https://ais.usvisa-info.com/en-ca/niv/users/sign_in"
AVAILABLE_DATE_REQUEST_SUFFIX = (
    f"/days/{CONSULATES[USER_CONSULATE]}.json?appointments[expedite]=false"
)
APPOINTMENT_PAGE_URL = "https://ais.usvisa-info.com/en-ca/niv/schedule/{id}/appointment"
PAYMENT_PAGE_URL = "https://ais.usvisa-info.com/en-ca/niv/schedule/{id}/payment"
REQUEST_HEADERS = {
    "X-Requested-With": "XMLHttpRequest",
}
