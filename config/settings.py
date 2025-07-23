# config/settings.py
import os

# --- User Credentials (Read from Environment Variables for Security) ---
# For GitHub Actions, these will be set via repository secrets.
USER_ID = os.getenv("GITAM_USER_ID")
PASSWORD = os.getenv("GITAM_PASSWORD")

# --- Website URLs ---
GITAM_LOGIN_URL = "https://login.gitam.edu/"

# --- Booking Specifics ---
TARGET_HOUR = 15  # 3 PM (24-hour format)
TARGET_MINUTE = 0  # 00 minutes
TARGET_SECOND_BUFFER = 5  # Start trying to book 5 seconds before 3 PM to account for server time
BOOKING_DATE_OFFSET = 1  # Book for tomorrow
TARGET_GYM_SLOT = "06:00 AM to 07:00 AM"
TARGET_FITNESS_CENTRE = "UniSex Fitness Centre"

# --- Selenium Configuration ---
IMPLICIT_WAIT_TIME = 10 # Seconds for implicit waits
EXPLICIT_WAIT_TIME = 20 # Seconds for explicit waits (e.g., for elements to be clickable)