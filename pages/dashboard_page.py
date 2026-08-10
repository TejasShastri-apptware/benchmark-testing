from playwright.sync_api import expect
import re
from pages.base_page import BasePage

class DashboardPage(BasePage):
    def navigate(self):
        self.page.goto("/dashboard")
        
    def verify_is_loaded(self):
        expect(self.page).to_have_url(re.compile(r".*/dashboard"))
        expect(self.page.get_by_test_id("user-menu-btn")).to_be_visible()

    def logout(self):
        self.page.get_by_test_id("user-menu-btn").click()
        self.page.get_by_test_id("logout-menu-item").click()