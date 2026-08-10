from playwright.sync_api import Page, expect
import re
from pages.base_page import BasePage

class ManagerApprovalPage(BasePage):
    def navigate_to_dashboard(self):
        self.page.goto("/dashboard")

    def check_and_open_notification(self, employee_name: str):
        self.page.get_by_role("button", name="Notifications").click()
        expect(self.page.get_by_role("button", name="Mark read").first).to_be_visible()
        expect(self.page.get_by_text(re.compile(f".*{employee_name} has requested leave.*")).first).to_be_visible()
        self.page.get_by_role("button", name="Open notification").first.click()
        expect(self.page.get_by_text(re.compile(r".*Approver Notes.*Approve.*Reject.*"))).to_be_visible()

    def navigate_to_leave_approvals(self):
        self.page.get_by_role("link", name="Dashboard", exact=True).click()
        self.page.get_by_role("link", name="Leave Approvals").click()

    def approve_pending_leave(self, employee_name: str, feedback: str):
        row_pattern = re.compile(f".*{employee_name}.*Pending.*", re.IGNORECASE)
        self.page.get_by_role("button", name=row_pattern).first.click()
        
        self.page.get_by_role("textbox", name="Add feedback or notes (optional)").fill(feedback)
        self.page.get_by_role("button", name="Approve").click()

    def verify_leave_is_approved(self):
        expect(self.page.get_by_text(re.compile(r".*This request has been approved.*"))).to_be_visible()
