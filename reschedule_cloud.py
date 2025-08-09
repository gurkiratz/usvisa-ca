import re
import signal
import sys
import time
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

# Import cloud settings if available, fallback to regular settings
try:
    from settings_cloud import *
except ImportError:
    from settings import *


class TimeoutHandler:
    def __init__(self, max_runtime_seconds):
        self.max_runtime_seconds = max_runtime_seconds
        self.start_time = time.time()

    def check_timeout(self):
        elapsed = time.time() - self.start_time
        if elapsed > self.max_runtime_seconds:
            Console.warning(
                f"Approaching timeout limit ({self.max_runtime_seconds}s). Gracefully shutting down..."
            )
            return True
        return False

    def remaining_time(self):
        elapsed = time.time() - self.start_time
        return max(0, self.max_runtime_seconds - elapsed)


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
    driver.find_element(By.ID, "user_email").send_keys(USER_EMAIL)
    driver.find_element(By.ID, "user_password").send_keys(USER_PASSWORD)
    driver.find_element(By.NAME, "commit").click()


def get_appointment_page(driver: WebDriver) -> None:
    WebDriverWait(driver, TIMEOUT).until(
        EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "Continue"))
    ).click()


def get_available_dates(
    driver: WebDriver, request_tracker: RequestTracker
) -> list | None:
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
        if response.status_code != 200:
            Console.error(
                f"Request failed with status code: {response.status_code}", "REQUEST"
            )
            return None
        dates_json = response.json()
        if not dates_json:
            Console.info("No available dates found.")
            return []
    except Exception as e:
        Console.error(f"Request failed: {e}", "REQUEST")
        return None
    dates = [datetime.strptime(item["date"], "%Y-%m-%d").date() for item in dates_json]
    return dates


def reschedule(
    driver: WebDriver, retryCount: int = 0, timeout_handler: TimeoutHandler = None
) -> bool:
    date_request_tracker = RequestTracker(
        retryCount if (retryCount > 0) else DATE_REQUEST_MAX_RETRY,
        30 * retryCount if (retryCount > 0) else DATE_REQUEST_MAX_TIME,
    )
    while date_request_tracker.should_retry():
        # Check for timeout
        if timeout_handler and timeout_handler.check_timeout():
            Console.warning("Timeout reached, stopping reschedule attempts")
            return False

        Console.searching("Checking for available appointment dates...")
        dates = get_available_dates(driver, date_request_tracker)
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
            try:
                Console.info(
                    f"Attempting to reschedule to {earliest_available_date}..."
                )
                if legacy_reschedule(driver, earliest_available_date):
                    Console.reschedule_status(True)
                    return True
                Console.reschedule_status(False)
            except Exception as e:
                Console.error(f"Error during reschedule: {e}", "RESCHEDULE")
                Console.error(traceback.format_exc(), "RESCHEDULE")
        else:
            Console.no_slot(str(earliest_available_date))
        Console.waiting(DATE_REQUEST_DELAY, "before next check")
        sleep(DATE_REQUEST_DELAY)
    return False


def reschedule_with_new_session(timeout_handler: TimeoutHandler = None) -> bool:
    driver = get_chrome_driver()
    session_failures = 0
    while session_failures < NEW_SESSION_AFTER_FAILURES:
        if timeout_handler and timeout_handler.check_timeout():
            driver.quit()
            return False

        try:
            Console.info("Logging in...")
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
    rescheduled = reschedule(driver, 0, timeout_handler)
    driver.quit()
    if rescheduled:
        return True
    else:
        return False


def main():
    Console.separator("US VISA APPOINTMENT RESCHEDULER (Cloud Version)")
    Console.info(
        f"Target date range: {EARLIEST_ACCEPTABLE_DATE} to {LATEST_ACCEPTABLE_DATE}"
    )
    Console.info(f"Consulate: {USER_CONSULATE}")

    # Initialize timeout handler
    timeout_handler = (
        TimeoutHandler(MAX_RUNTIME_SECONDS)
        if "MAX_RUNTIME_SECONDS" in globals()
        else None
    )
    if timeout_handler:
        Console.info(f"Max runtime: {MAX_RUNTIME_SECONDS} seconds")

    Console.separator()

    session_count = 0
    while True:
        if timeout_handler and timeout_handler.check_timeout():
            Console.warning("Maximum runtime reached. Exiting gracefully.")
            break

        session_count += 1
        Console.session_start(session_count)

        if timeout_handler:
            remaining = timeout_handler.remaining_time()
            Console.info(f"Time remaining: {remaining:.0f} seconds")

        rescheduled = reschedule_with_new_session(timeout_handler)
        if rescheduled:
            Console.success("Program completed successfully! Appointment rescheduled.")
            break
        else:
            Console.warning(
                f"Session #{session_count} failed. Retrying in {NEW_SESSION_DELAY} seconds..."
            )
            Console.waiting(NEW_SESSION_DELAY, "before new session")
            sleep(NEW_SESSION_DELAY)


if __name__ == "__main__":
    main()
