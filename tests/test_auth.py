from playwright.sync_api import Page, expect
import os
import pytest
import re
from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage

def test_raw_login_and_logout_flow(page: Page):
    """
    Tests the complete raw login and logout flow without using pre-existing sessions.
    This ensures the UI mechanism for logging in and out actually works.
    """
    email = os.getenv("E2E_EMPLOYEE_EMAIL")
    password = os.getenv("E2E_EMPLOYEE_PASSWORD")
    
    if not email or not password:
        pytest.skip("Employee credentials not configured in .env.e2e")
        
    login_page = LoginPage(page)
    dashboard_page = DashboardPage(page)
    
    # 1. Test Raw Login
    login_page.navigate()
    login_page.login(email, password)
    
    # Verify we hit the dashboard gracefully
    dashboard_page.verify_is_loaded()
    
    # 2. Test Raw Logout
    dashboard_page.logout()
    
    # Verify we are redirected back to the login page
    expect(page).to_have_url(re.compile(r".*/login"))
    expect(page.get_by_test_id("sign-in-heading")).to_be_visible()


def test_admin_pre_authenticated(admin_page: Page):
    """
    Tests that the admin_page fixture correctly bypasses the login screen
    and injects the session state.
    """
    dashboard_page = DashboardPage(admin_page)
    dashboard_page.navigate()
    dashboard_page.verify_is_loaded()

def test_employee_pre_authenticated(employee_page: Page):
    """
    Tests that the employee_page fixture correctly bypasses the login screen
    and injects the session state.
    """
    dashboard_page = DashboardPage(employee_page)
    dashboard_page.navigate()
    dashboard_page.verify_is_loaded()

def test_manager_pre_authenticated(manager_page: Page):
    """
    Tests that the manager_page fixture correctly bypasses the login screen
    and injects the session state.
    """
    dashboard_page = DashboardPage(manager_page)
    dashboard_page.navigate()
    dashboard_page.verify_is_loaded()
