import re
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
from settings import *


def get_chrome_driver() -> WebDriver:
    options = webdriver.ChromeOptions()
    if not SHOW_GUI:
        options.add_argument("headless")
        options.add_argument("window-size=1920x1080")
        options.add_argument("disable-gpu")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
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
        response = requests.get(request_url, headers=request_headers)
    except Exception as e:
        Console.error(f"Get available dates request failed: {e}", "REQUEST")
        return None
    if response.status_code != 200:
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


def reschedule(driver: WebDriver, retryCount: int = 0) -> bool:
    date_request_tracker = RequestTracker(
        retryCount if (retryCount > 0) else DATE_REQUEST_MAX_RETRY,
        30 * retryCount if (retryCount > 0) else DATE_REQUEST_MAX_TIME,
    )
    while date_request_tracker.should_retry():
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
                return False
            except Exception as e:
                Console.error(f"Rescheduling failed: {e}", "RESCHEDULE")
                Console.debug(traceback.format_exc())
                continue
        else:
            Console.date_check(str(earliest_available_date), acceptable=False)
        Console.waiting(DATE_REQUEST_DELAY, "before next check")
        sleep(DATE_REQUEST_DELAY)
    return False


def reschedule_with_new_session(retryCount: int = DATE_REQUEST_MAX_RETRY) -> bool:
    driver = get_chrome_driver()
    session_failures = 0
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
    rescheduled = reschedule(driver, retryCount)
    driver.quit()
    if rescheduled:
        return True
    else:
        return False


if __name__ == "__main__":
    Console.separator("US VISA APPOINTMENT RESCHEDULER")
    Console.info(
        f"Target date range: {EARLIEST_ACCEPTABLE_DATE} to {LATEST_ACCEPTABLE_DATE}"
    )
    Console.info(f"Consulate: {USER_CONSULATE}")
    Console.separator()

    session_count = 0
    while True:
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
