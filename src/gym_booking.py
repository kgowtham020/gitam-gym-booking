# src/gym_booking.py

import time
import sys
import os
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# No need for pytesseract, PIL, io, or TwoCaptcha if CAPTCHA is readable text
# from PIL import Image
# import pytesseract
# import io
# from twocaptcha import TwoCaptcha

# Add parent directory to path to import config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.settings import (
    GITAM_LOGIN_URL, # USER_ID and PASSWORD are now from os.getenv(), so remove them here
    TARGET_HOUR, TARGET_MINUTE, TARGET_SECOND_BUFFER,
    BOOKING_DATE_OFFSET, TARGET_GYM_SLOT, TARGET_FITNESS_CENTRE,
    IMPLICIT_WAIT_TIME, EXPLICIT_WAIT_TIME
    # CAPTCHA_API_KEY is not needed anymore for this method
)

# --- User Credentials (Read from Environment Variables for Security) ---
# These are correctly read from environment variables, which GitHub Actions will provide.
USER_ID = os.getenv("GITAM_USER_ID")
PASSWORD = os.getenv("GITAM_PASSWORD")

# --- WebDriver Setup ---
def initialize_driver():
    """Initializes and returns a Chrome WebDriver instance."""
    print("Initializing Chrome WebDriver...")
    try:
        options = webdriver.ChromeOptions()
        # GitHub Actions environments are headless, so we must use headless mode
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-gpu")
        options.add_argument("--log-level=3")
        options.add_experimental_option('excludeSwitches', ['enable-logging'])

        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(IMPLICIT_WAIT_TIME)
        print("WebDriver initialized successfully.")
        return driver
    except WebDriverException as e:
        print(f"ERROR: Failed to initialize WebDriver: {e}")
        print("Ensure Chrome is installed and ChromeDriver is compatible. 'webdriver-manager' handles this usually.")
        return None

# --- Core Automation Functions ---

def login(driver, user_id, password):
    """
    Handles the login process, automatically reading CAPTCHA from span elements.
    Returns True on successful login, False otherwise.
    """
    print(f"Navigating to GITAM Login Page: {GITAM_LOGIN_URL}")
    driver.get(GITAM_LOGIN_URL)

    try:
        # Wait for User ID field and enter value
        user_id_field = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.presence_of_element_located((By.ID, "userName"))
        )
        user_id_field.send_keys(user_id)
        print(f"Entered User ID.")

        # Enter Password
        password_field = driver.find_element(By.ID, "password")
        password_field.send_keys(password)
        print("Entered Password.")

        # --- Automated CAPTCHA Handling: Extracting text from spans ---
        # Wait for the CAPTCHA spans to be present
        WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[@class='preview']//span"))
        )
        # Find all span elements within the preview div
        captcha_spans = driver.find_elements(By.XPATH, "//div[@class='preview']//span")
        # Concatenate the text from each span to get the full CAPTCHA
        captcha_text = ''.join([span.get_attribute("innerHTML").strip() for span in captcha_spans])

        # Clean up the CAPTCHA text, ensuring it's only digits (as per your CAPTCHA type)
        # This handles cases where innerHTML might contain spaces or non-digit chars
        solved_captcha = ''.join(filter(str.isdigit, captcha_text))

        if not solved_captcha or len(solved_captcha) != 5: # Assuming it's always 5 digits
            print(f"ERROR: Could not extract valid 5-digit CAPTCHA. Extracted: '{solved_captcha}' (from raw '{captcha_text}')")
            return False

        print("CAPTCHA read automatically:", solved_captcha)

        # Enter the CAPTCHA text into the input field
        captcha_field = driver.find_element(By.ID, "captcha") # Assuming this is still the correct ID
        captcha_field.send_keys(solved_captcha)
        print("CAPTCHA entered into field.")

        # Click Login
        login_button = driver.find_element(By.ID, "login-button")
        login_button.click()
        print("Clicked 'LOGIN' button.")

        # Handle any immediate popups or notifications after login
        try:
            WebDriverWait(driver, 5).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, "modal-backdrop"))
            )
        except TimeoutException:
            pass

        try:
            deny_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Deny')] | //button[contains(text(), 'Cancel')] | //button[contains(text(), 'Close')]"))
            )
            deny_button.click()
            print("Denied popup/notification.")
        except TimeoutException:
            print("No significant popups or notifications detected to deny.")
        except Exception as e:
            print(f"Error while trying to deny popup: {e}")

        # Verify successful login by checking for a known element on the dashboard
        WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.url_contains("dashboard") or EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'My dashboard')]"))
        )
        print("Login successful! Redirected to dashboard.")
        return True
    except TimeoutException as e:
        print(f"Login failed: Timeout while waiting for an element. ({e})")
        return False
    except NoSuchElementException as e:
        print(f"Login failed: Could not find a required element. ({e})")
        print("Website structure might have changed. Please update selectors.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during login: {e}")
        return False

def navigate_to_g_sports(driver):
    """Navigates to the G-Sports application from the dashboard."""
    print("Navigating to G-Sports...")
    try:
        # Click the six dots (App Launcher)
        app_launcher_xpath = "//button[contains(@class, 'app-launcher')] | //div[contains(@class, 'header-right')]//i[contains(@class, 'fa-th')] | //img[contains(@src, 'user.png')]/preceding-sibling::div/button"
        app_launcher = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.element_to_be_clickable((By.XPATH, app_launcher_xpath))
        )
        app_launcher.click()
        print("Clicked the App Launcher (six dots).")

        # Click on "G-Sports" App in the opened menu
        g_sports_app_xpath = "//span[contains(text(), 'G-Sports')] | //div[contains(@class, 'app-icon')]//img[contains(@src, 'sports')]/ancestor::a"
        g_sports_app = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.element_to_be_clickable((By.XPATH, g_sports_app_xpath))
        )
        g_sports_app.click()
        print("Clicked on 'G-Sports' app. This opens the Sports Facilities in Bengaluru page.")
        return True
    except TimeoutException:
        print("Failed to navigate to G-Sports: App launcher or G-Sports app not found.")
        return False
    except Exception as e:
        print(f"An error occurred during G-Sports navigation: {e}")
        return False

def select_fitness_centre(driver):
    """Selects the 'Fitness Centre (Uni Sex)' option within the G-Sports app."""
    print(f"Selecting '{TARGET_FITNESS_CENTRE}' option...")
    try:
        # Locate and click the 'Fitness Centre (Uni Sex)' card/button
        fitness_centre_xpath = f"//div[contains(text(), '{TARGET_FITNESS_CENTRE}')]"
        fitness_centre_element = WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
            EC.element_to_be_clickable((By.XPATH, fitness_centre_xpath))
        )
        fitness_centre_element.click()
        print(f"Selected '{TARGET_FITNESS_CENTRE}'. It opens up the booking interface.")
        return True
    except TimeoutException:
        print(f"Failed to select '{TARGET_FITNESS_CENTRE}': Element not found or not clickable.")
        return False
    except Exception as e:
        print(f"An error occurred while selecting Fitness Centre: {e}")
        return False

def book_gym_slot(driver):
    """
    Attempts to book the specified gym slot for tomorrow's date.
    This function should be called repeatedly during the booking window.
    """
    print("Attempting to book gym slot...")
    try:
        # 1. Choose a Date (Tomorrow's date)
        date_input_xpath = "//input[contains(@placeholder, 'DD-Mon-YYYY')] | //div[contains(@class, 'date-picker')]//input"
        date_input = WebDriverWait(driver, 5).until( # Short wait as we're in the loop
            EC.element_to_be_clickable((By.XPATH, date_input_xpath))
        )
        date_input.click()
        time.sleep(0.5) # Small pause for calendar to render

        # Calculate tomorrow's date string in the expected format (e.g., "22-Jul-2025")
        tomorrow = datetime.now() + timedelta(days=BOOKING_DATE_OFFSET)
        tomorrow_str_day_month_year = tomorrow.strftime("%d-%b-%Y")
        tomorrow_str_day_only = str(tomorrow.day)

        # Select tomorrow's date from the calendar.
        try:
            target_date_element_xpath = f"//div[contains(@class, 'datepicker-days')]//td[contains(@class, 'day') and not(contains(@class, 'old')) and not(contains(@class, 'new')) and text()='{tomorrow_str_day_only}'] | //div[contains(@class, 'datepicker')]//div[contains(text(), '{tomorrow_str_day_month_year}')]"
            target_date_element = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, target_date_element_xpath))
            )
            target_date_element.click()
            print(f"Selected booking date: {tomorrow_str_day_month_year}")
            time.sleep(0.5) # Give page a moment to update slots
        except TimeoutException:
            print(f"Could not find or select tomorrow's date ({tomorrow_str_day_month_year}). It might not be available yet.")
            return False

        # 2. Select court Dropdown (Fitness Centre (Unisex))
        court_dropdown_xpath = "//select[contains(@class, 'form-control') and @name='courtId'] | //select[contains(@name, 'fitnessCentre')]"
        court_dropdown_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, court_dropdown_xpath))
        )
        select_court = Select(court_dropdown_element)
        select_court.select_by_visible_text(TARGET_FITNESS_CENTRE)
        print(f"Selected court: '{TARGET_FITNESS_CENTRE}'.")
        time.sleep(1) # Give page a moment to load slots after court selection

        # 3. Pick an available Time Slot (e.g., 06:00 AM - 07:00 AM)
        target_slot_xpath = f"//div[contains(@class, 'shift-slot-wrap')]//div[contains(text(), '{TARGET_GYM_SLOT}') and not(contains(@class, 'Reserved'))]"
        target_slot_element = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, target_slot_xpath))
        )
        target_slot_element.click()
        print(f"Selected time slot: '{TARGET_GYM_SLOT}'.")
        time.sleep(0.5) # Short pause before clicking reserve

        # 4. Click “Reserve” button
        reserve_button_xpath = "//button[contains(text(), 'Reserve')]"
        reserve_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, reserve_button_xpath))
        )
        reserve_button.click()
        print("Clicked 'Reserve' button.")

        # 5. Verify booking success or failure message
        try:
            success_message_xpath = "//div[contains(@class, 'alert-success')] | //span[contains(text(), 'successfully reserved')] | //div[contains(text(), 'You have reserved 06:00 AM to 07:00 AM slot')]"
            WebDriverWait(driver, EXPLICIT_WAIT_TIME).until(
                EC.presence_of_element_located((By.XPATH, success_message_xpath))
            )
            print("Gym slot reserved successfully!")
            return True
        except TimeoutException:
            # Look for error/already reserved message
            error_message_xpath = "//div[contains(@class, 'alert-danger')] | //div[contains(text(), 'You have reserved 06:00 AM to 07:00 AM slot.')] | //span[contains(text(), 'Error')]"
            try:
                error_message = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, error_message_xpath))
                )
                print(f"Booking attempt failed: {error_message.text}")
            except TimeoutException:
                print("Booking attempt finished, but no clear success or error message appeared within timeout. Manual check might be needed.")
            return False

    except TimeoutException as e:
        print(f"Booking attempt failed: Timeout while waiting for an element ({e}). Slot might not be available or page didn't load.")
        return False
    except NoSuchElementException as e:
        print(f"Booking attempt failed: Could not find a required element ({e}). Website structure might have changed.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during slot booking: {e}")
        return False

def main():
    """Main function to orchestrate the gym slot booking process."""
    if not USER_ID or not PASSWORD:
        print("ERROR: GITAM_USER_ID or GITAM_PASSWORD environment variables are not set.")
        print("Please configure them as GitHub Secrets.")
        return

    driver = initialize_driver()
    if driver is None:
        print("Failed to initialize WebDriver. Exiting.")
        return

    try:
        # Step 1: Login
        if not login(driver, USER_ID, PASSWORD):
            print("Login failed. Exiting.")
            return

        # Step 2: Navigate to G-Sports
        if not navigate_to_g_sports(driver):
            print("Navigation to G-Sports failed. Exiting.")
            return

        # Step 3: Select Fitness Centre
        if not select_fitness_centre(driver):
            print("Selection of Fitness Centre failed. Exiting.")
            return

        # Step 4: Wait for the precise booking time and attempt to book
        current_time_ist = datetime.now()
        print(f"\nCurrent time: {current_time_ist.strftime('%H:%M:%S')} (Assuming IST timezone for booking logic).")
        print(f"Waiting for precise booking time: {TARGET_HOUR:02d}:{TARGET_MINUTE:02d} IST...")
        print("The script will start attempting to book a few seconds before the target time.")
        print("NOTE: CAPTCHA is read directly from HTML elements. This is very reliable if elements remain consistent.")

        while True:
            now = datetime.now()
            target_booking_time_today = now.replace(hour=TARGET_HOUR, minute=TARGET_MINUTE, second=0, microsecond=0)

            if now > target_booking_time_today + timedelta(minutes=5):
                print("Booking window for today has likely passed. Exiting.")
                break

            time_until_start_attempt = (target_booking_time_today - now).total_seconds() - (TARGET_SECOND_BUFFER + 5)
            if time_until_start_attempt > 0:
                print(f"Sleeping for {int(time_until_start_attempt)} seconds until closer to booking window...")
                time.sleep(time_until_start_attempt)
                continue

            print(f"Approaching booking time. Current time: {now.strftime('%H:%M:%S')}. Initiating rapid attempts...")
            booking_success = False
            for attempt in range(10): # Try 10 times in quick succession
                current_time = datetime.now()
                if current_time.hour == TARGET_HOUR and current_time.minute == TARGET_MINUTE and current_time.second >= TARGET_SECOND_BUFFER:
                    print(f"Attempt {attempt + 1}: Booking at {current_time.strftime('%H:%M:%S')}...")
                    if book_gym_slot(driver):
                        print("Booking completed successfully!")
                        booking_success = True
                        break
                    else:
                        print("Booking attempt failed. Retrying in 1 second...")
                        time.sleep(1)
                elif current_time.hour > TARGET_HOUR or (current_time.hour == TARGET_HOUR and current_time.minute > TARGET_MINUTE + 2):
                    print("Booking window likely closed or slot taken. Exiting retries.")
                    break
                else:
                    time.sleep(0.1)

            if booking_success:
                break

            if not booking_success:
                print("All booking attempts failed within the window. Exiting.")
                break

    finally:
        print("\nClosing browser...")
        if driver:
            driver.quit()
        print("Script finished.")

if __name__ == "__main__":
    main()