import os
from dotenv import load_dotenv
import pytest
from playwright.sync_api import Playwright, BrowserContext
from pages.login_page import LoginPage

# Dynamically find .env.e2e in the same directory as this conftest.py file
# This is robust regardless of where the user runs the pytest command from
env_path = os.path.join(".env.e2e")
load_dotenv(env_path)

def get_auth_state_path(persona: str) -> str:
    # Store auth states in a hidden .auth directory
    os.makedirs(".auth", exist_ok=True)
    return f".auth/{persona}_state.json"

def setup_persona_session(playwright: Playwright, base_url: str, persona: str, email: str, password: str):
    """Logs in and saves the storage state for a specific persona."""
    state_path = get_auth_state_path(persona)
    
    # Optional: check if state is fresh here. For now we just recreate it if it doesn't exist.
    if os.path.exists(state_path):
        return state_path

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
    base_url = pytestconfig.getini("base_url")
    email = os.getenv("E2E_ADMIN_EMAIL")
    password = os.getenv("E2E_ADMIN_PASSWORD")
    if not email or not password:
        pytest.skip("Admin credentials not configured in .env.e2e")
    return setup_persona_session(playwright, base_url, "admin", email, password)

@pytest.fixture(scope="session")
def employee_state(playwright: Playwright, pytestconfig):
    base_url = pytestconfig.getini("base_url")
    email = os.getenv("E2E_EMPLOYEE_EMAIL")
    password = os.getenv("E2E_EMPLOYEE_PASSWORD")
    if not email or not password:
        pytest.skip("Employee credentials not configured in .env.e2e")
    return setup_persona_session(playwright, base_url, "employee", email, password)

@pytest.fixture(scope="session")
def manager_state(playwright: Playwright, pytestconfig):
    base_url = pytestconfig.getini("base_url")
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
        base_url=pytestconfig.getini("base_url")
    )
    page = context.new_page()
    yield page
    context.close()

@pytest.fixture
def employee_page(browser, employee_state, pytestconfig):
    """Provides a fresh page pre-authenticated as an employee."""
    context = browser.new_context(
        storage_state=employee_state,
        base_url=pytestconfig.getini("base_url")
    )
    page = context.new_page()
    yield page
    context.close()

@pytest.fixture
def manager_page(browser, manager_state, pytestconfig):
    """Provides a fresh page pre-authenticated as a manager."""
    context = browser.new_context(
        storage_state=manager_state,
        base_url=pytestconfig.getini("base_url")
    )
    page = context.new_page()
    yield page
    context.close()
