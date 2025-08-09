import re
import traceback
from datetime import datetime
from time import sleep

import requests
from gmail import GMail, Message
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from console_utils import Console
from request_tracker import RequestTracker
from reschedule import get_chrome_driver, login
from settings import *

# The gmail folder is reusing [gmail-sender](https://github.com/paulc/gmail-sender/tree/master).
# I'm copying it since it's not published to pip yet.


def notify_receiver(title_str: str, msg_str: str):
    gmail = GMail(
        f"{GMAIL_SENDER_NAME} <{GMAIL_EMAIL}>", GMAIL_APPLICATION_PWD
    )  # Sender gmail
    msg = Message(title_str, to=f"{RECEIVER_NAME} <{RECEIVER_EMAIL}>", text=msg_str)
    gmail.send(msg)
    Console.email_sent(RECEIVER_EMAIL)
    Console.info(f"Subject: {title_str}")
    Console.info(f"Message: {msg_str}")


def get_dates_from_payment_page(driver: WebDriver) -> None:
    timeout = TIMEOUT
    continue_button = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((By.LINK_TEXT, "Continue"))
    )
    continue_button.click()
    current_url = driver.current_url
    url_id = re.search(r"/(\d+)", current_url).group(1)
    payment_url = PAYMENT_PAGE_URL.format(id=url_id)
    driver.get(payment_url)

    content_table = WebDriverWait(driver, timeout).until(
        EC.visibility_of_element_located((By.CLASS_NAME, "for-layout"))
    )
    text_elements = content_table.find_elements(By.TAG_NAME, "td")
    loc_str_array = [e.text for i, e in enumerate(text_elements) if i % 2 == 0]
    date_str_array = [e.text for i, e in enumerate(text_elements) if i % 2 == 1]
    return loc_str_array, date_str_array


def detect_and_notify(loc_str_array: list, date_str_array: list) -> bool:
    earliest_acceptable_date = datetime.strptime(
        EARLIEST_ACCEPTABLE_DATE, "%Y-%m-%d"
    ).date()
    latest_acceptable_date = datetime.strptime(
        LATEST_ACCEPTABLE_DATE, "%Y-%m-%d"
    ).date()

    length = len(loc_str_array)
    detected = False
    for i in range(length):
        loc_str = loc_str_array[i]
        date_str = date_str_array[i]
        if date_str == "No Appointments Available":
            continue
        date = datetime.strptime(date_str, "%d %B, %Y").date()

        if earliest_acceptable_date <= date <= latest_acceptable_date:
            Console.found_slot(f"{date} at {loc_str}")
            Console.info("Sending email notification...")
            notify_receiver(
                f"New slot found with date: {date}, location: {loc_str}",
                f"New slot found with date: {date}, location: {loc_str}",
            )
            detected = True
        else:
            Console.date_check(f"{date} at {loc_str}", acceptable=False)
    return detected


def detect_with_new_session() -> bool:
    driver = get_chrome_driver()
    session_failures = 0
    detected = False
    while session_failures < NEW_SESSION_AFTER_FAILURES:
        try:
            login(driver)
            loc_str_array, date_str_array = get_dates_from_payment_page(driver)
            detected = detect_and_notify(loc_str_array, date_str_array)
            break
        except Exception as e:
            Console.error(f"Unable to get payment page: {e}", "SESSION")
            session_failures += 1
            Console.waiting(FAIL_RETRY_DELAY, "before session retry")
            sleep(FAIL_RETRY_DELAY)
            continue
    driver.quit()
    return detected


if __name__ == "__main__":
    Console.separator("US VISA APPOINTMENT DETECTOR")
    Console.info(
        f"Target date range: {EARLIEST_ACCEPTABLE_DATE} to {LATEST_ACCEPTABLE_DATE}"
    )
    Console.info(f"Consulate: {USER_CONSULATE}")
    Console.separator()

    session_count = 0
    while True:
        session_count += 1
        Console.session_start(session_count)
        detected = detect_with_new_session()
        if detected:
            Console.success(
                "Appointment slot detected! Waiting 10 minutes before continuing..."
            )
            Console.waiting(600, "cooldown period")
            sleep(600)
        else:
            Console.warning(
                f"Session #{session_count} completed. Retrying in {NEW_SESSION_DELAY} seconds..."
            )
            Console.waiting(NEW_SESSION_DELAY, "before new session")
            sleep(NEW_SESSION_DELAY)
