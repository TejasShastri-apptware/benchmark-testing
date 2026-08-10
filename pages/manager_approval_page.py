from playwright.sync_api import Page, expect
from pages.base_page import BasePage

class ManagerApprovalPage(BasePage):

    def navigate_to_dashboard(self):
        self.page.goto("/dashboard")

    # ── Notifications ─────────────────────────────────────────────────────────

    def open_notifications(self):
        """Opens the notification drawer via the verified data-testid."""
        self.page.get_by_test_id("notifications-btn").click()

    def open_first_notification(self):
        """Clicks the first 'open notification' button in the drawer."""
        self.page.get_by_test_id("open-notification-btn").first.click()

    def expect_notification_visible(self):
        """Assert at least one unread notification (mark-read button) is present."""
        expect(self.page.get_by_test_id("mark-read-btn").first).to_be_visible()

    # ── Timesheet approvals ───────────────────────────────────────────────────

    def navigate_to_timesheet_approvals(self):
        self.page.goto("/approvals/timesheets")

    def approve_first_pending_timesheet(self):
        """
        Opens the first timesheet in 'submitted' state from the approvals list
        and clicks Approve. Waits for the success toast.

        NOTE: This action is IRREVERSIBLE in the current environment.
        This method is documented for completeness but the test that calls it
        (TC-TS-04) is marked skip and must not be run against live data.
        """
        self.page.get_by_test_id("timesheet-row-submitted").first.click()
        self.page.get_by_test_id("approve-timesheet-btn").click()
        expect(
            self.page.get_by_text("Timesheet approved successfully")
        ).to_be_visible(timeout=15000)
