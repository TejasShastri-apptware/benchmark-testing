from playwright.sync_api import Page, expect
import re
from pages.base_page import BasePage

class EmployeeLeavePage(BasePage):
    def navigate_to_leave_requests(self):
        self.page.goto("/dashboard")
        self.page.get_by_role("button", name="Time & leave").click()
        self.page.get_by_role("link", name="Leave Requests").click()

    def apply_for_casual_leave(self, dates: list[str], reason: str):
        self.page.get_by_role("button", name="Apply Leave").click()
        
        self.page.get_by_role("combobox", name="Leave type").click()
        self.page.get_by_role("option", name="Casual Leaves").click()
        
        self.page.get_by_placeholder("Select leave period").click()
        
        for date in dates:
            self.page.get_by_role("cell", name=date, exact=True).first.click()
        
        self.page.get_by_role("button", name="Half").nth(2).click()
        self.page.get_by_role("button", name="1st half").click()
        
        self.page.get_by_role("textbox", name="Reason").fill(reason)
        self.page.get_by_role("button", name="Submit request").click()

    def verify_leave_is_pending(self, leave_type: str = "Casual Leaves"):
        expect(self.page.get_by_role("button", name=re.compile(f".*{leave_type}.*Pending.*"))).to_be_visible()
