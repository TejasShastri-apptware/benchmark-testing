# End-to-End (E2E) Testing Project

## Overview
This repository contains the End-to-End (E2E) tests for the web application, built with Playwright and Pytest. Currently, the test suite actively focuses on **Authentication** and **Timesheets**. 

> Note: Leave-related tests (`test_leave.py`) are deliberately kept aside for now and should not be considered part of the active test execution.

## Setup Instructions

To get started, follow these setup steps:

1. **Virtual Environment**: 
   It's highly recommended to use a Python virtual environment to keep dependencies isolated.
   ```bash
   # Create a virtual environment
   python -m venv testvenv

   # Activate it (Windows)
   testvenv\Scripts\activate
   ```

2. **Install Dependencies**:
   Install the required Python packages listed in `requirements.txt`.
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright Browsers**:
   After installing the Python dependencies, you must install the Playwright browser binaries.
   ```bash
   playwright install
   ```

4. **Environment Variables**:
   Ensure that the `.env.e2e` file in the root directory is correctly configured with the necessary environment variables, such as base URLs and test credentials.

5. **Google Reporter & OAuth Setup**:
   The test suite utilizes a custom reporter (`utils/google_reporter.py`) to automatically log test results to Google Sheets and upload failure screenshots to Google Drive.
   - You **must** ensure a valid `client_secrets.json` file is present in the root directory. This contains the OAuth client ID and secret required for Google APIs.
   - Upon running tests for the first time, a local server will start and a browser window will open to authenticate the Google account.
   - Once authorized, a `token.json` file will be generated automatically to store your access tokens, allowing subsequent runs to bypass the manual login step.

## Running the Tests

The project is configured via `pytest.ini`. By default, running tests will generate a self-contained HTML report (`e2e-report.html`) and capture screenshots, videos, and tracing data upon test failure.

### Authentication Tests (`test_auth.py`)
These tests verify the core login flows and session fixtures. Specifically, they cover:
- **Raw Login & Logout Flow**: Verifies the actual UI mechanism of entering credentials, reaching the dashboard, and logging out successfully. Expect this to use the credentials from `.env.e2e`.
- **Pre-Authenticated Fixtures**: Three distinct tests ensure that the `admin_page`, `employee_page`, and `manager_page` pytest fixtures correctly inject session state, completely bypassing the login screen for faster test execution. Expect these to instantly land on the dashboard without interacting with the login form.

- **To run authentication tests:**
  ```bash
  pytest tests/test_auth.py
  ```

### Timesheet Tests (`test_timesheet.py`)
These tests cover the core timesheet functionality from the perspective of an employee and a manager. What to expect:
- **Navigation (`ts_nav`)**: Verifies that the sidebar navigation correctly opens the Timesheets list page from the dashboard.
- **Draft Creation (`ts_draft`)**: Simulates an employee creating a new timesheet, selecting a project, logging hours (for single and multi-day scenarios), and saving it. Expect these tests to leave "Draft" entries in the timesheet list.
- **Submission (`ts_submit`)**: Simulates an employee seeding a day, auto-filling the rest of the week, and submitting it. Expect a timesheet to transition to the "Submitted" state (which a manager can manually reject later to clean up).
- **Manager Approval (`ts_approve`)**: Simulates a manager approving a submitted timesheet. **Note: This test is permanently skip-guarded in the code by default.**

### ⚠️ IMPORTANT CAUTION: Timesheet Approvals
**Do NOT directly run all timesheet tests blindly.** 
Timesheet approval actions (tested under the `ts_approve` marker) are **irreversible** in the backend system. Running approval tests will permanently transition test timesheets into an "Approved" state, which cannot be undone or easily reset for subsequent test runs.

To safely test timesheet functionality without triggering irreversible approvals, you should selectively run the tests using pytest markers. This will be fixed soon.

**How to run safely:**
You should choose to only run tests related to navigation (`ts_nav`), drafts (`ts_draft`), and submissions (`ts_submit`).

- **Run all timesheet tests EXCEPT approvals and submission (Recommended):**
  ```bash
  pytest -m "auth or ts_nav or ts_draft" --headed
  ```
  **The above command runs test that validate the following:**
  
  Manual employee login and logout, assertion that pages after actions are actually visible
  
  Inject admin, employee_manager and employee auth status and validate logins

  Assert navigation to timesheet module through user-taken path

  Enter an entry in the timesheet

  Enter multiple entries in the timesheet

- **Run only draft creation tests:**
  ```bash
  pytest -m ts_draft
  ```
  **Run only timesheet navigation check:**
  ```bash
  pytest -m ts_nav
- **Run only submission tests(does not have a cleanup as of now):**
  ```bash
  pytest -m ts_submit
  ```

## What to Expect
- **Test Reports**: After execution, view the detailed run results by opening `e2e-report.html` in your browser.
- **Debugging Artifacts**: If any test fails, check the `test-results/` directory. Playwright will automatically save state traces, video recordings, and screenshots to help you diagnose the failure.

