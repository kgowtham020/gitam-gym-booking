# GITAM Gym Slot Booking Automation

This project provides a Python script to automate the process of booking gym slots at GITAM.
It uses Selenium to interact with the web interface and integrates with a CAPTCHA solving service
to enable fully automated execution on GitHub Actions.

**Disclaimer:** This script is provided for educational purposes and personal use.
Use it responsibly and in accordance with GITAM's terms of service.
Automating web interactions may violate terms of service.

## Features

* Fully automates login to the GITAM portal.
* Integrates with a CAPTCHA solving service (e.g., 2Captcha) to bypass CAPTCHA.
* [cite_start]Navigates to the G-Sports application. [cite: 13]
* [cite_start]Selects the "Fitness Centre (Uni Sex)" option. [cite: 17]
* [cite_start]Waits for the precise booking time (3:00 PM IST)[cite: 18].
* [cite_start]Attempts to select tomorrow's 06:00 AM - 07:00 AM slot [cite: 23] [cite_start]and reserve it[cite: 24].
* Designed to run on GitHub Actions, allowing execution even when your laptop is off.

## Prerequisites

Before setting up, you will need:

* A GitHub account.
* An account with a CAPTCHA solving service (e.g., 2Captcha.com) and an API key. This will incur a minimal cost for each CAPTCHA solved.

## Setup

1.  **Fork/Clone the Repository:**
    ```bash
    git clone [https://github.com/YourUsername/gitam-gym-booking.git](https://github.com/YourUsername/gitam-gym-booking.git)
    cd gitam-gym-booking
    ```
    (If you fork it, remember to change "YourUsername" to your GitHub username.)

2.  **Configure GitHub Secrets:**
    Your sensitive information (GITAM credentials and CAPTCHA API key) must be stored as GitHub Secrets for security.

    * Go to your GitHub repository.
    * Click on **Settings** (top right).
    * In the left sidebar, click **Secrets and variables** > **Actions**.
    * Click **New repository secret**.
    * Add the following secrets with their respective values:
        * [cite_start]`GITAM_USER_ID`: Your GITAM User ID (e.g., `BU22CSEN0400136`) [cite: 2]
        * [cite_start]`GITAM_PASSWORD`: Your GITAM Password (e.g., `Gowtham@08`) [cite: 4]
        * `CAPTCHA_API_KEY`: Your API key from the CAPTCHA solving service (e.g., from 2Captcha)

3.  **Review the GitHub Actions Workflow:**
    The workflow file is located at `.github/workflows/main.yml`. It's configured to run daily.

    * **Schedule:** The `cron` schedule is set to `28 9 * * *`. This means 28 minutes past 9 AM UTC.
        * **Important:** You are in Alur Duddanahally, Karnataka, India. IST is UTC+5:30.
        * 3:00 PM IST (booking time) = 15:00 IST
        * 15:00 IST - 5:30 hours = 09:30 UTC
        * To run **just before** 3:00 PM IST, we want to start the script around 09:28 UTC.
        * So, `28 9 * * *` is the correct cron expression for 9:28 AM UTC, ensuring it starts before the 3:00 PM IST (9:30 AM UTC) booking window.

4.  **Enable GitHub Actions:**
    * Go to your GitHub repository.
    * Click on **Actions** (top menu).
    * If prompted, enable GitHub Actions for the repository.
    * You should see the "Gym Slot Booker" workflow listed.

## How it Runs (Automatically)

Once configured, the GitHub Action will automatically:

1.  Trigger every day at 9:28 AM UTC (which is 2:58 PM IST).
2.  Set up a Python environment and install dependencies.
3.  Install Google Chrome.
4.  Run your `src/gym_booking.py` script.
5.  The script will:
    * Use the provided GitHub Secrets for your GITAM User ID and Password.
    * [cite_start]Navigate to the GITAM login page. [cite: 1]
    * [cite_start]Extract the CAPTCHA image and send it to the CAPTCHA solving service using your `CAPTCHA_API_KEY`. [cite: 5, 6]
    * Receive the solved CAPTCHA and input it.
    * Proceed with login.
    * [cite_start]Navigate to G-Sports [cite: 13] [cite_start]and the Fitness Centre booking section[cite: 17].
    * [cite_start]Wait for the precise booking time (3:00 PM IST)[cite: 18].
    * [cite_start]Attempt to select the 06:00 AM - 07:00 AM slot for tomorrow [cite: 23] [cite_start]and click reserve[cite: 24].
    * Log its progress in the GitHub Actions workflow run logs.

You can monitor the runs by going to the "Actions" tab in your repository. Look for the "Gym Slot Booker" workflow and click on the latest run to see its logs.

## Troubleshooting

* **GitHub Actions Workflow Failure:**
    * Check the "Actions" tab in your repository. Click on the failed workflow run to see detailed logs.
    * Common issues: incorrect environment variables/secrets, syntax errors in `.yml` file, or issues during dependency installation.
* **Selenium Element Not Found Errors:**
    * Websites can change their HTML structure. If the script fails, it's likely due to outdated element selectors (XPath, ID, Class Name).
    * You will need to run the script locally (temporarily comment out `--headless` in `initialize_driver()` for visual debugging) and use your browser's developer tools (F12) to inspect the elements on the GITAM portal. Update the `By.ID`, `By.XPATH`, etc., values in `src/gym_booking.py` accordingly.
* **CAPTCHA Solving Failures:**
    * Check your CAPTCHA service account for balance.
    * Verify your `CAPTCHA_API_KEY` is correct in GitHub Secrets.
    * Some CAPTCHAs are harder for services. Ensure the CAPTCHA type is supported.
* **Timing Issues:**
    * The script attempts to book very close to 3:00 PM IST. Network latency and server response times can play a role. The script includes retry logic.
    * Ensure the `cron` expression in `.github/workflows/main.yml` is correctly set for your desired local time in UTC.

---