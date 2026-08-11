import time
import os
from dotenv import load_dotenv
import pytest
from playwright.sync_api import Playwright, BrowserContext
from pages.login_page import LoginPage
from utils.google_reporter import GoogleReporter

reporter = None

AUTH_STATE_TTL_SECONDS = 55*60

# Dynamically find .env.e2e in the same directory as this conftest.py file
# This is robust regardless of where the user runs the pytest command from
env_path = os.path.join(".env.e2e")
load_dotenv(env_path)

def pytest_configure(config):
    """Override base_url from the E2E_BASE_URL environment variable if set.
    This allows CI and staging runs to target the correct environment without
    editing pytest.ini (e.g. E2E_BASE_URL=https://staging.example.com pytest).
    Falls back to the value in pytest.ini (http://localhost:3000) for local dev.
    """
    env_base_url = os.getenv("E2E_BASE_URL")
    if env_base_url:
        # pytest-playwright reads base_url from config.option.base_url first,
        # then falls back to the ini value, so setting it here takes precedence.
        config.option.__dict__.setdefault("base_url", env_base_url)
        config.option.base_url = env_base_url

    global reporter
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
    cred_path = os.getenv("GOOGLE_CREDENTIALS_PATH")
    if sheet_id and folder_id and cred_path:
        reporter = GoogleReporter(cred_path, sheet_id, folder_id)

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()

    if rep.when == "call":
        test_name = item.name
        status = rep.outcome
        duration = f"{rep.duration:.2f}s"
        error_msg = str(rep.longrepr) if rep.failed else ""
        screenshot_link = ""

        page = None
        for fixture_name in ["page", "admin_page", "employee_page", "manager_page"]:
            if fixture_name in item.funcargs:
                page = item.funcargs[fixture_name]
                break
        
        if page and reporter:
            os.makedirs("test-results", exist_ok=True)
            screenshot_path = f"test-results/{test_name}.png"
            try:
                page.screenshot(path=screenshot_path)
                screenshot_link = reporter.upload_screenshot(screenshot_path)
            except Exception as e:
                print(f"Failed to capture screenshot: {e}")
                
        if reporter:
            # We truncate error_msg to avoid huge cells in Sheets
            error_short = error_msg[:500] + "..." if len(error_msg) > 500 else error_msg
            reporter.append_row(test_name, status, duration, error_short, screenshot_link)

def get_auth_state_path(persona: str) -> str:
    # Store auth states in a hidden .auth directory
    os.makedirs(".auth", exist_ok=True)
    return f".auth/{persona}_state.json"

def setup_persona_session(playwright: Playwright, base_url: str, persona: str, email: str, password: str):
    """Logs in and saves the storage state for a specific persona."""
    state_path = get_auth_state_path(persona)
    
    # Optional: check if state is fresh here. For now we just recreate it if it doesn't exist.
    if os.path.exists(state_path):
        age_seconds = time.time() - os.path.getmtime(state_path)
        if age_seconds < AUTH_STATE_TTL_SECONDS:
            return state_path
        # delete stale state and perform a fresh login
        os.remove(state_path)

    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(base_url=base_url)
    page = context.new_page()
    
    login_page = LoginPage(page)
    login_page.navigate()
    login_page.login(email, password)
    
    # Save the auth state
    context.storage_state(path=state_path)
    browser.close()
    return state_path

@pytest.fixture(scope="session")
def admin_state(playwright: Playwright, pytestconfig):
    base_url = getattr(pytestconfig.option, "base_url", None) or pytestconfig.getini("base_url")
    email = os.getenv("E2E_ADMIN_EMAIL")
    password = os.getenv("E2E_ADMIN_PASSWORD")
    if not email or not password:
        pytest.skip("Admin credentials not configured in .env.e2e")
    return setup_persona_session(playwright, base_url, "admin", email, password)

@pytest.fixture(scope="session")
def employee_state(playwright: Playwright, pytestconfig):
    base_url = getattr(pytestconfig.option, "base_url", None) or pytestconfig.getini("base_url")
    email = os.getenv("E2E_EMPLOYEE_EMAIL")
    password = os.getenv("E2E_EMPLOYEE_PASSWORD")
    if not email or not password:
        pytest.skip("Employee credentials not configured in .env.e2e")
    return setup_persona_session(playwright, base_url, "employee", email, password)

@pytest.fixture(scope="session")
def manager_state(playwright: Playwright, pytestconfig):
    base_url = getattr(pytestconfig.option, "base_url", None) or pytestconfig.getini("base_url")
    email = os.getenv("E2E_MANAGER_EMAIL")
    password = os.getenv("E2E_MANAGER_PASSWORD")
    if not email or not password:
        pytest.skip("Manager credentials not configured in .env.e2e")
    return setup_persona_session(playwright, base_url, "manager", email, password)

@pytest.fixture
def admin_page(browser, admin_state, pytestconfig):
    """Provides a fresh page pre-authenticated as an admin."""
    context = browser.new_context(
        storage_state=admin_state,
        base_url=getattr(pytestconfig.option, "base_url", None) or pytestconfig.getini("base_url")
    )
    page = context.new_page()
    yield page
    context.close()

@pytest.fixture
def employee_page(browser, employee_state, pytestconfig):
    """Provides a fresh page pre-authenticated as an employee."""
    context = browser.new_context(
        storage_state=employee_state,
        base_url=getattr(pytestconfig.option, "base_url", None) or pytestconfig.getini("base_url")
    )
    page = context.new_page()
    yield page
    context.close()

@pytest.fixture
def manager_page(browser, manager_state, pytestconfig):
    """Provides a fresh page pre-authenticated as a manager."""
    context = browser.new_context(
        storage_state=manager_state,
        base_url=getattr(pytestconfig.option, "base_url", None) or pytestconfig.getini("base_url")
    )
    page = context.new_page()
    yield page
    context.close()
