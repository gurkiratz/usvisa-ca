# Use environment variables directly
import os
from datetime import date, datetime
from time import sleep
import random

from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"
NUM_PARTICIPANTS = int(os.getenv("NUM_PARTICIPANTS", "1"))

def select_best_time_slot(appointment_time_options):
    """Select the best available time slot based on preferences"""
    if not appointment_time_options:
        return None
    
    # Filter out any empty or invalid options
    valid_options = [opt for opt in appointment_time_options if opt.text.strip()]
    
    if not valid_options:
        return None
    
    # Try to find morning slots first (before 12 PM)
    morning_slots = []
    afternoon_slots = []
    
    for opt in valid_options:
        time_text = opt.text.strip().lower()
        # Check if it's morning (before 12 PM)
        if any(morning in time_text for morning in ['am', 'morning', '9:', '10:', '11:']):
            morning_slots.append(opt)
        else:
            afternoon_slots.append(opt)
    
    # Prefer morning slots if available
    if morning_slots:
        # Pick a random morning slot to avoid always choosing the same one
        return random.choice(morning_slots)
    elif afternoon_slots:
        # Pick a random afternoon slot
        return random.choice(afternoon_slots)
    else:
        # Fallback to first available slot
        return valid_options[0]

def legacy_reschedule(driver: WebDriver, date_to_book: date):
    """Enhanced rescheduling with better race condition handling"""
    try:
        driver.refresh()
        sleep(1)  # Reduced delay for faster response

        # Continue btn: applicable when there are more than one applicant for scheduling
        if NUM_PARTICIPANTS > 1:
            try:
                continueBtn = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (
                            By.XPATH,
                            "//main[@id='main']/div[@class='mainContent']/form/div[2]/div/input",
                        )
                    )
                )
                continueBtn.click()
                sleep(1)
            except Exception as e:
                print(f"Continue button not found or not needed: {e}")

        # Find and click date selection box
        try:
            date_selection_box = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.ID, "appointments_consulate_appointment_date_input")
                )
            )
            date_selection_box.click()
            sleep(1)  # Reduced delay
        except Exception as e:
            print(f"Failed to find date selection box: {e}")
            return False

        # Move to next month
        def next_month():
            try:
                next_btn = driver.find_element(
                    By.XPATH, "//div[@id='ui-datepicker-div']/div[2]/div/a"
                )
                next_btn.click()
                sleep(0.5)
            except Exception as e:
                print(f"Failed to move to next month: {e}")

        # Check if available in current month
        def cur_month_ava():
            try:
                month = driver.find_element(
                    By.XPATH, "//div[@id='ui-datepicker-div']/div[1]/table/tbody"
                )
                dates = month.find_elements(By.TAG_NAME, "td")
                for date_cell in dates:
                    if date_cell.get_attribute("class") == " undefined":
                        return True
                return False
            except Exception as e:
                print(f"Failed to check current month availability: {e}")
                return False

        # Check the nearest slot is available in # months and move to the month
        def nearest_ava():
            ava_in = 0
            cur = cur_month_ava()
            while not cur and ava_in < 12:  # Limit to 12 months to prevent infinite loop
                next_month()
                cur = cur_month_ava()
                ava_in += 1
            return ava_in

        available_in_months = nearest_ava()
        print(f"Available slot found in {available_in_months} month(s)")

        # Try to pick time and reschedule
        print("Trying to pick time and reschedule...")
        
        # Find available dates in the current month view
        try:
            month = driver.find_element(
                By.XPATH, "//div[@id='ui-datepicker-div']/div[1]/table/tbody"
            )
            dates = month.find_elements(By.TAG_NAME, "td")
            available_date_btn = None
            
            for date_cell in dates:
                if date_cell.get_attribute("class") == " undefined":
                    try:
                        available_date_btn = date_cell.find_element(By.TAG_NAME, "a")
                        break
                    except Exception:
                        continue
            
            if not available_date_btn:
                print("No available date button found")
                return False
                
            # Click the available date
            available_date_btn.click()
            sleep(1)
            
        except Exception as e:
            print(f"Failed to select available date: {e}")
            return False

        # Confirm selected date
        try:
            date_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.ID, "appointments_consulate_appointment_date")
                )
            )
            date_selected = datetime.strptime(
                date_box.get_attribute("value"), "%Y-%m-%d"
            ).date()
            print(f"Selected date: {date_selected}")
            
            if not date_selected <= date_to_book:
                print(
                    f"{datetime.now().strftime('%H:%M:%S')} SLOT '{date_to_book}' no longer available\n"
                )
                return False
            else:
                print(
                    f"{datetime.now().strftime('%H:%M:%S')} SLOT '{date_selected}' is still available. Booking....\n"
                )
                
        except Exception as e:
            print(f"Failed to confirm selected date: {e}")
            return False

        # Select time of the date with better slot selection
        try:
            sleep(1)
            appointment_time = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "appointments_consulate_appointment_time"))
            )
            appointment_time.click()
            sleep(1)
            
            appointment_time_options = appointment_time.find_elements(By.TAG_NAME, "option")
            
            # Use improved time slot selection
            selected_time_option = select_best_time_slot(appointment_time_options)
            
            if selected_time_option:
                selected_time_option.click()
                print(f"Selected time slot: {selected_time_option.text}")
            else:
                print("No valid time slots available")
                return False
                
        except Exception as e:
            print(f"Failed to select time slot: {e}")
            return False

        # Click "Reschedule" button
        try:
            reschedule_btn = driver.find_element(
                By.XPATH,
                "//form[@id='appointment-form']/div[2]/fieldset/ol/li/input",
            )
            reschedule_btn.click()
            sleep(2)
            
        except Exception as e:
            print(f"Failed to click reschedule button: {e}")
            return False

        # Handle confirmation dialog
        try:
            confirm = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "/html/body/div[6]/div/div/a[2]"))
            )
            sleep(1)
            
            if not TEST_MODE:
                confirm.click()
                print("Rescheduling confirmed successfully!")
                return True
            else:
                print("TEST MODE: Would have confirmed rescheduling")
                return True
                
        except Exception as e:
            print(f"Failed to handle confirmation dialog: {e}")
            return False

    except Exception as e:
        print(f"Unexpected error during rescheduling: {e}")
        return False

    return False
