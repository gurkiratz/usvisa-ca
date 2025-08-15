# Try to import cloud settings (environment variables), fallback to local settings
import os
import re
import threading
import traceback
from datetime import datetime
from time import sleep

import requests
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from console_utils import Console
from legacy_rescheduler import legacy_reschedule
from request_tracker import RequestTracker

# Import Gmail notification functionality
try:
    from legacy.gmail.gmail import GMail, Message

    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False
    Console.warning(
        "Gmail notification module not available - notifications will be disabled",
        "IMPORT",
    )

# Validate required environment variables
required_vars = [
    "USER_EMAIL",
    "USER_PASSWORD",
    "EARLIEST_ACCEPTABLE_DATE",
    "LATEST_ACCEPTABLE_DATE",
    "USER_CONSULATE",
    "GMAIL_EMAIL",
    "GMAIL_APPLICATION_PWD",
    "RECEIVER_EMAIL",
]

missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(
        f"Missing required environment variables: {', '.join(missing_vars)}"
    )

# Account Info
USER_EMAIL = os.getenv("USER_EMAIL")
USER_PASSWORD = os.getenv("USER_PASSWORD")
NUM_PARTICIPANTS = int(os.getenv("NUM_PARTICIPANTS", "1"))

# Date preferences
EARLIEST_ACCEPTABLE_DATE = os.getenv("EARLIEST_ACCEPTABLE_DATE")
LATEST_ACCEPTABLE_DATE = os.getenv("LATEST_ACCEPTABLE_DATE")

# Consulate configuration
CONSULATES = {
    "Calgary": 89,
    "Halifax": 90,
    "Montreal": 91,
    "Ottawa": 92,
    "Quebec": 93,
    "Toronto": 94,
    "Vancouver": 95,
}
USER_CONSULATE = os.getenv("USER_CONSULATE")

# Gmail notification settings
GMAIL_SENDER_NAME = os.getenv("GMAIL_SENDER_NAME", "Visa Appointment Reminder")
GMAIL_EMAIL = os.getenv("GMAIL_EMAIL")
GMAIL_APPLICATION_PWD = os.getenv("GMAIL_APPLICATION_PWD")
RECEIVER_NAME = os.getenv("RECEIVER_NAME", "User")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")

# Pushover notification settings
PUSHOVER_APP_TOKEN = os.getenv("PUSHOVER_APP_TOKEN")
PUSHOVER_USER_KEY = os.getenv("PUSHOVER_USER_KEY")
PUSHOVER_ENABLED = os.getenv("PUSHOVER_ENABLED", "true").lower() == "true"

# Runtime settings
SHOW_GUI = os.getenv("SHOW_GUI", "false").lower() == "true"
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"
DETACH = False  # Always False for cloud
NEW_SESSION_AFTER_FAILURES = int(os.getenv("NEW_SESSION_AFTER_FAILURES", "5"))
NEW_SESSION_DELAY = int(os.getenv("NEW_SESSION_DELAY", "60"))
TIMEOUT = int(os.getenv("TIMEOUT", "10"))
FAIL_RETRY_DELAY = int(os.getenv("FAIL_RETRY_DELAY", "30"))
DATE_REQUEST_DELAY = int(os.getenv("DATE_REQUEST_DELAY", "10"))
DATE_REQUEST_MAX_RETRY = int(os.getenv("DATE_REQUEST_MAX_RETRY", "1000"))
DATE_REQUEST_MAX_TIME = int(os.getenv("DATE_REQUEST_MAX_TIME", "1800"))

# Race condition handling settings
BOOKING_RETRY_ATTEMPTS = int(os.getenv("BOOKING_RETRY_ATTEMPTS", "3"))
BOOKING_RETRY_DELAY = int(os.getenv("BOOKING_RETRY_DELAY", "2"))
FAST_MODE = os.getenv("FAST_MODE", "true").lower() == "true"

# Session renewal settings
SESSION_RENEWAL_MAX_ATTEMPTS = int(os.getenv("SESSION_RENEWAL_MAX_ATTEMPTS", "4"))
SESSION_RENEWAL_DELAY = int(os.getenv("SESSION_RENEWAL_DELAY", "5"))

# Cloud platform timeout
MAX_RUNTIME_SECONDS = int(os.getenv("MAX_RUNTIME_SECONDS", "18000"))  # 5 hours default

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


def get_chrome_driver() -> WebDriver:
    options = webdriver.ChromeOptions()
    if not SHOW_GUI:
        options.add_argument("--headless")
        options.add_argument("--window-size=1920x1080")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")  # Required for cloud deployment
        options.add_argument("--disable-dev-shm-usage")  # Required for cloud deployment
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-images")  # Faster loading
        options.add_argument(
            "user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
        )
    options.add_experimental_option("detach", DETACH)
    options.add_argument("--incognito")
    driver = webdriver.Chrome(options=options)
    return driver


def login(driver: WebDriver) -> None:
    driver.get(LOGIN_URL)
    timeout = TIMEOUT

    email_input = WebDriverWait(driver, timeout).until(
        EC.visibility_of_element_located((By.ID, "user_email"))
    )
    email_input.send_keys(USER_EMAIL)

    password_input = WebDriverWait(driver, timeout).until(
        EC.visibility_of_element_located((By.ID, "user_password"))
    )
    password_input.send_keys(USER_PASSWORD)

    policy_checkbox = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "icheckbox"))
    )
    policy_checkbox.click()

    login_button = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((By.NAME, "commit"))
    )
    login_button.click()


def get_appointment_page(driver: WebDriver) -> None:
    timeout = TIMEOUT
    continue_button = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((By.LINK_TEXT, "Continue"))
    )
    continue_button.click()
    sleep(2)
    current_url = driver.current_url
    url_id = re.search(r"/(\d+)", current_url).group(1)
    appointment_url = APPOINTMENT_PAGE_URL.format(id=url_id)
    driver.get(appointment_url)


def get_available_dates(
    driver: WebDriver, request_tracker: RequestTracker
) -> list | None | str:
    request_tracker.log_retry()
    request_tracker.retry()
    current_url = driver.current_url
    request_url = current_url + AVAILABLE_DATE_REQUEST_SUFFIX
    request_header_cookie = "".join(
        [f"{cookie['name']}={cookie['value']};" for cookie in driver.get_cookies()]
    )
    request_headers = REQUEST_HEADERS.copy()
    request_headers["Cookie"] = request_header_cookie
    request_headers["User-Agent"] = driver.execute_script("return navigator.userAgent")
    try:
        response = requests.get(request_url, headers=request_headers, timeout=30)
    except Exception as e:
        error_msg = str(e)
        Console.error(f"Get available dates request failed: {e}", "REQUEST")

        # Check for specific network connection errors that should trigger login renewal
        if (
            ("Connection aborted" in error_msg and "RemoteDisconnected" in error_msg)
            or "Remote end closed connection" in error_msg
            or "Connection broken" in error_msg
            or "ConnectionError" in error_msg
        ):
            Console.warning(
                "Network connection lost - triggering session renewal to login again",
                "NETWORK",
            )
            return "SESSION_EXPIRED"

        return None

    if response.status_code == 401:
        Console.error(f"Failed with status code {response.status_code}", "HTTP")
        Console.debug(f"Response Text: {response.text}")
        # Check if it's a session expiry
        try:
            error_data = response.json()
            if "session expired" in error_data.get("error", "").lower():
                Console.warning(
                    "Session expired - need to create new session", "SESSION"
                )
                return "SESSION_EXPIRED"
        except:
            pass
        Console.warning("Authentication failed - need to create new session", "SESSION")
        return "SESSION_EXPIRED"
    elif response.status_code != 200:
        Console.error(f"Failed with status code {response.status_code}", "HTTP")
        Console.debug(f"Response Text: {response.text}")
        return None

    try:
        dates_json = response.json()
    except:
        Console.error("Failed to decode JSON response", "PARSE")
        Console.debug(f"Response Text: {response.text}")
        return None
    dates = [datetime.strptime(item["date"], "%Y-%m-%d").date() for item in dates_json]
    return dates


def notify_slot_found_async(date_str: str, consulate: str):
    """Send email notification asynchronously when a slot is found"""

    def send_notification():
        try:
            if not GMAIL_AVAILABLE:
                Console.warning("Gmail not available - skipping notification", "NOTIFY")
                return False

            gmail = GMail(f"{GMAIL_SENDER_NAME} <{GMAIL_EMAIL}>", GMAIL_APPLICATION_PWD)
            msg = Message(
                f"🎯 VISA APPOINTMENT SLOT FOUND: {date_str} at {consulate}",
                to=f"{RECEIVER_NAME} <{RECEIVER_EMAIL}>",
                text=f"""
🎯 APPOINTMENT SLOT FOUND! 🎯

Date: {date_str}
Consulate: {consulate}
Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

The system is attempting to book this slot automatically.
Please check your visa account to confirm the booking.

If you need to manually book, log in immediately at:
https://ais.usvisa-info.com/en-ca/niv/users/sign_in

Good luck! 🍀
            """,
            )
            gmail.send(msg)
            Console.email_sent(RECEIVER_EMAIL)
            Console.info(f"Email notification sent for slot on {date_str}")
            return True
        except Exception as e:
            Console.error(f"Failed to send email notification: {e}", "NOTIFY")
            return False

    # Start notification in background thread - don't wait for it
    notification_thread = threading.Thread(target=send_notification, daemon=True)
    notification_thread.start()
    Console.info(f"Email notification started in background for slot on {date_str}")


def send_pushover_notification(
    title: str,
    message: str,
    priority: int = 1,
    sound: str = "pushover",
    url: str = "",
    url_title: str = "",
) -> bool:
    """Send instant push notification via Pushover

    Args:
        title: Notification title
        message: Notification message
        priority: -2 (lowest), -1 (low), 0 (normal), 1 (high), 2 (emergency)
        sound: Sound name (pushover, bike, bugle, cashregister, classical, cosmic, falling,
               gamelan, incoming, intermission, magic, mechanical, pianobar, siren,
               spacealarm, tugboat, alien, climb, persistent, echo, updown, none)

    Returns:
        bool: True if notification sent successfully, False otherwise
    """
    if not PUSHOVER_ENABLED:
        Console.info("Pushover notifications disabled - skipping")
        return False

    if not PUSHOVER_APP_TOKEN or not PUSHOVER_USER_KEY:
        Console.warning(
            "Pushover credentials not configured - skipping notification", "PUSHOVER"
        )
        return False

    try:
        pushover_url = "https://api.pushover.net/1/messages.json"
        data = {
            "token": PUSHOVER_APP_TOKEN,
            "user": PUSHOVER_USER_KEY,
            "title": title,
            "message": message,
            "priority": priority,
            "sound": sound,
            "url": url,
            "url_title": url_title,
        }

        # Add emergency priority settings if needed
        if priority == 2:
            data["retry"] = 30  # Retry every 30 seconds
            data["expire"] = 3600  # Stop retrying after 1 hour

        response = requests.post(pushover_url, data=data, timeout=10)

        if response.status_code == 200:
            result = response.json()
            if result.get("status") == 1:
                Console.info("Pushover notification sent successfully", "PUSHOVER")
                return True
            else:
                Console.error(
                    f"Pushover API error: {result.get('errors', 'Unknown error')}",
                    "PUSHOVER",
                )
                return False
        else:
            Console.error(
                f"Pushover HTTP error: {response.status_code} - {response.text}",
                "PUSHOVER",
            )
            return False

    except requests.exceptions.RequestException as e:
        Console.error(f"Pushover request failed: {e}", "PUSHOVER")
        return False
    except Exception as e:
        Console.error(f"Pushover notification failed: {e}", "PUSHOVER")
        return False


def notify_slot_found_pushover_and_email(date_str: str, consulate: str):
    """Send both instant Pushover notification and email notification when a slot is found"""
    # Send instant Pushover notification first (synchronous for immediate delivery)
    pushover_success = send_pushover_notification(
        title=f"🎯 VISA SLOT FOUND: {date_str}",
        message=f"Available at {consulate}!\nThe system is booking automatically.\nCheck your account to confirm!\n\nhttps://ais.usvisa-info.com/en-ca/niv/users/sign_in",
        priority=2,  # Emergency priority for instant delivery
        sound="alien",  # Attention-grabbing sound
        url="https://ais.usvisa-info.com/en-ca/niv/schedule/60227641/appointment",
        url_title="Login to your account",
    )

    if pushover_success:
        Console.info(f"Instant Pushover notification sent for slot on {date_str}")

    # Also send email notification (async - don't wait for it)
    notify_slot_found_async(date_str, consulate)


def notify_reschedule_success_async(date_str: str, consulate: str):
    """Send email notification asynchronously when rescheduling is successful"""

    def send_notification():
        try:
            if not GMAIL_AVAILABLE:
                return False

            gmail = GMail(f"{GMAIL_SENDER_NAME} <{GMAIL_EMAIL}>", GMAIL_APPLICATION_PWD)
            msg = Message(
                f"✅ VISA APPOINTMENT RESCHEDULED SUCCESSFULLY: {date_str}",
                to=f"{RECEIVER_NAME} <{RECEIVER_EMAIL}>",
                text=f"""
✅ APPOINTMENT SUCCESSFULLY RESCHEDULED! ✅

New Date: {date_str}
Consulate: {consulate}
Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Your visa appointment has been automatically rescheduled to {date_str}.
Please log in to your visa account to confirm the new appointment details.

Login at: https://ais.usvisa-info.com/en-ca/niv/users/sign_in

Congratulations! 🎉
            """,
            )
            gmail.send(msg)
            Console.email_sent(RECEIVER_EMAIL)
            Console.info(f"Success notification sent for {date_str}")
            return True
        except Exception as e:
            Console.error(f"Failed to send success notification: {e}", "NOTIFY")
            return False

    # Start notification in background thread
    notification_thread = threading.Thread(target=send_notification, daemon=True)
    notification_thread.start()
    Console.info(f"Success notification started in background for {date_str}")


def notify_reschedule_success_pushover_and_email(date_str: str, consulate: str):
    """Send both Pushover and email notifications for successful rescheduling"""
    # Send instant Pushover notification
    pushover_success = send_pushover_notification(
        title=f"✅ VISA APPOINTMENT BOOKED!",
        message=f"Successfully rescheduled to {date_str} at {consulate}!\nConfirm in your visa account.",
        priority=1,  # High priority
        sound="magic",  # Success sound
    )

    if pushover_success:
        Console.info(f"Success Pushover notification sent for {date_str}")

    # Also send email notification (async)
    notify_reschedule_success_async(date_str, consulate)


def notify_reschedule_failed_async(date_str: str, consulate: str, error_msg: str):
    """Send email notification asynchronously when rescheduling fails"""

    def send_notification():
        try:
            if not GMAIL_AVAILABLE:
                return False

            gmail = GMail(f"{GMAIL_SENDER_NAME} <{GMAIL_EMAIL}>", GMAIL_APPLICATION_PWD)
            msg = Message(
                f"❌ VISA APPOINTMENT RESCHEDULING FAILED: {date_str}",
                to=f"{RECEIVER_NAME} <{RECEIVER_EMAIL}>",
                text=f"""
❌ APPOINTMENT RESCHEDULING FAILED ❌

Target Date: {date_str}
Consulate: {consulate}
Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Error: {error_msg}

The system found a slot but failed to book it. This could be due to:
- The slot was taken by someone else
- Technical issues with the website
- Session timeout

The system will continue trying to find and book other available slots.

You may want to manually check for available appointments at:
https://ais.usvisa-info.com/en-ca/niv/users/sign_in
            """,
            )
            gmail.send(msg)
            Console.email_sent(RECEIVER_EMAIL)
            Console.info(f"Failure notification sent for {date_str}")
            return True
        except Exception as e:
            Console.error(f"Failed to send failure notification: {e}", "NOTIFY")
            return False

    # Start notification in background thread
    notification_thread = threading.Thread(target=send_notification, daemon=True)
    notification_thread.start()
    Console.info(f"Failure notification started in background for {date_str}")


def notify_reschedule_failed_pushover_and_email(
    date_str: str, consulate: str, error_msg: str
):
    """Send both Pushover and email notifications for failed rescheduling"""
    # Send instant Pushover notification
    pushover_success = send_pushover_notification(
        title=f"❌ BOOKING FAILED: {date_str}",
        message=f"Failed to book {date_str} at {consulate}.\nReason: {error_msg[:100]}...\nContinuing to search...",
        priority=1,  # High priority
        sound="falling",  # Failure sound
    )

    if pushover_success:
        Console.info(f"Failure Pushover notification sent for {date_str}")

    # Also send email notification (async)
    notify_reschedule_failed_async(date_str, consulate, error_msg)


def reschedule(driver: WebDriver, retryCount: int = 0) -> bool | str:
    date_request_tracker = RequestTracker(
        retryCount if (retryCount > 0) else DATE_REQUEST_MAX_RETRY,
        30 * retryCount if (retryCount > 0) else DATE_REQUEST_MAX_TIME,
    )
    while date_request_tracker.should_retry():
        Console.searching("Checking for available appointment dates...")
        dates = get_available_dates(driver, date_request_tracker)

        # Handle session expiry
        if dates == "SESSION_EXPIRED":
            Console.warning(
                "Session expired during reschedule - triggering new session", "SESSION"
            )
            return "SESSION_EXPIRED"

        if not dates:
            Console.error("Error occurred when requesting available dates", "FETCH")
            Console.waiting(DATE_REQUEST_DELAY, "before retry")
            sleep(DATE_REQUEST_DELAY)
            continue

        earliest_available_date = dates[0]
        latest_acceptable_date = datetime.strptime(
            LATEST_ACCEPTABLE_DATE, "%Y-%m-%d"
        ).date()

        if earliest_available_date <= latest_acceptable_date:
            Console.found_slot(str(earliest_available_date))

            # Send immediate notification that slot was found (Pushover + email)
            notify_slot_found_pushover_and_email(
                str(earliest_available_date), USER_CONSULATE
            )

            try:
                Console.info(
                    f"Attempting to reschedule to {earliest_available_date}..."
                )

                # Try to reschedule with retry logic for race conditions
                max_booking_attempts = BOOKING_RETRY_ATTEMPTS
                for attempt in range(max_booking_attempts):
                    if attempt > 0:
                        Console.info(
                            f"Retry attempt {attempt + 1}/{max_booking_attempts} for booking..."
                        )
                        sleep(BOOKING_RETRY_DELAY)  # Use configured delay

                    if legacy_reschedule(driver, earliest_available_date):
                        Console.reschedule_status(True)
                        # Send success notification (Pushover + email)
                        notify_reschedule_success_pushover_and_email(
                            str(earliest_available_date), USER_CONSULATE
                        )
                        return True
                    else:
                        if attempt < max_booking_attempts - 1:
                            Console.warning(
                                f"Booking attempt {attempt + 1} failed, retrying...",
                                "BOOKING",
                            )
                        else:
                            Console.reschedule_status(False)
                            # Send failure notification (Pushover + email)
                            notify_reschedule_failed_pushover_and_email(
                                str(earliest_available_date),
                                USER_CONSULATE,
                                "Slot no longer available",
                            )
                            return False

            except Exception as e:
                Console.error(f"Rescheduling failed: {e}", "RESCHEDULE")
                Console.debug(traceback.format_exc())
                # Send failure notification (Pushover + email)
                notify_reschedule_failed_pushover_and_email(
                    str(earliest_available_date), USER_CONSULATE, str(e)
                )
                continue
        else:
            Console.date_check(str(earliest_available_date), acceptable=False)

        Console.waiting(DATE_REQUEST_DELAY, "before next check")
        sleep(DATE_REQUEST_DELAY)
    return False


def reschedule_with_new_session(retryCount: int = DATE_REQUEST_MAX_RETRY) -> bool:
    driver = get_chrome_driver()
    session_failures = 0

    # Login and setup session
    while session_failures < NEW_SESSION_AFTER_FAILURES:
        try:
            Console.info("Logging into visa appointment system...")
            login(driver)
            Console.login_status(True)
            Console.info("Navigating to appointment page...")
            get_appointment_page(driver)
            break
        except Exception as e:
            Console.error(f"Unable to get appointment page: {e}", "SESSION")
            session_failures += 1
            Console.waiting(FAIL_RETRY_DELAY, "before session retry")
            sleep(FAIL_RETRY_DELAY)
            continue

    # Main reschedule loop with session renewal
    session_renewal_attempts = 0
    while True:
        rescheduled = reschedule(driver, retryCount)

        # Handle different return values
        if rescheduled == "SESSION_EXPIRED":
            session_renewal_attempts += 1
            if session_renewal_attempts > SESSION_RENEWAL_MAX_ATTEMPTS:
                Console.error(
                    f"Maximum session renewal attempts ({SESSION_RENEWAL_MAX_ATTEMPTS}) exceeded",
                    "SESSION",
                )
                driver.quit()
                return False

            Console.info(
                f"Session expired - attempting to renew session (attempt {session_renewal_attempts}/{SESSION_RENEWAL_MAX_ATTEMPTS})..."
            )
            try:
                # Clear cookies and start fresh
                driver.delete_all_cookies()
                sleep(SESSION_RENEWAL_DELAY)

                # Navigate back to login page and re-login
                driver.get(LOGIN_URL)
                sleep(2)
                login(driver)
                Console.login_status(True)
                Console.info("Navigating to appointment page...")
                get_appointment_page(driver)
                Console.success("Session renewed successfully!", "SESSION")
                # Reset renewal attempts on success
                session_renewal_attempts = 0
                # Continue the loop to try rescheduling again
                continue
            except Exception as e:
                Console.error(
                    f"Failed to renew session (attempt {session_renewal_attempts}): {e}",
                    "SESSION",
                )
                Console.waiting(SESSION_RENEWAL_DELAY, "before next renewal attempt")
                sleep(SESSION_RENEWAL_DELAY)
                # Continue to retry session renewal
                continue
        elif rescheduled == True:
            driver.quit()
            return True
        else:
            # rescheduled == False - normal failure, exit
            driver.quit()
            return False


if __name__ == "__main__":
    Console.separator("US VISA APPOINTMENT RESCHEDULER")
    Console.info(
        f"Target date range: {EARLIEST_ACCEPTABLE_DATE} to {LATEST_ACCEPTABLE_DATE}"
    )
    Console.info(f"Consulate: {USER_CONSULATE}")

    # Add timeout handling for cloud deployment
    import time

    start_time = time.time()
    if MAX_RUNTIME_SECONDS:
        Console.info(
            f"Max runtime: {MAX_RUNTIME_SECONDS} seconds ({MAX_RUNTIME_SECONDS / 3600:.1f} hours)"
        )

    Console.separator()

    session_count = 0
    while True:
        # Check timeout for cloud deployment
        if MAX_RUNTIME_SECONDS:
            elapsed = time.time() - start_time
            if elapsed > MAX_RUNTIME_SECONDS:
                Console.warning(
                    f"Maximum runtime ({MAX_RUNTIME_SECONDS}s) reached. Exiting gracefully."
                )
                break
            remaining = MAX_RUNTIME_SECONDS - elapsed
            Console.info(f"Time remaining: {remaining:.0f} seconds")

        session_count += 1
        Console.session_start(session_count)
        rescheduled = reschedule_with_new_session()
        if rescheduled:
            Console.success("Program completed successfully! Appointment rescheduled.")
            break
        else:
            Console.warning(
                f"Session #{session_count} failed. Retrying in {NEW_SESSION_DELAY} seconds..."
            )
            Console.waiting(NEW_SESSION_DELAY, "before new session")
            sleep(NEW_SESSION_DELAY)
