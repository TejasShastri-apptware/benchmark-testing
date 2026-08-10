from playwright.sync_api import Page, expect
from pages.base_page import BasePage

class TimesheetPage(BasePage):
    def navigate(self):
        self.page.goto("/timesheets")
        expect(self.page.get_by_test_id("new-timesheet-btn")).to_be_visible()
        
    def start_new_timesheet(self):
        self.page.get_by_test_id("new-timesheet-btn").click()
        
    def open_available_day_by_index(self, index: int = 0):
        """
        Finds the Nth available day cell with data-testid^="add-time-" and clicks it.
        Uses the data-testid prefix locator instead of text matching for robustness.
        """
        cell = self.page.locator('[data-testid^="add-time-"]').nth(index)
        expect(cell).to_be_visible()
        cell.click()
        
    def add_project_by_index(self, index: int):
        """
        Finds the Nth available 'Add work' project button and clicks it.
        """
        add_btn = self.page.locator('[data-testid^="add-project-"]').nth(index)
        expect(add_btn).to_be_visible()
        add_btn.click()
        
    def log_hours_and_description(self, index: int, hours: str, description: str):
        """
        Fills the hours and description for the Nth project input available in the drawer.
        """
        input_field = self.page.locator('[data-testid^="hour-input-"]').nth(index)
        expect(input_field).to_be_visible()
        input_field.fill(hours)
        input_field.blur()
        
        desc_field = self.page.locator('[data-testid^="description-input-"]').nth(index)
        expect(desc_field).to_be_visible()
        desc_field.fill(description)
        desc_field.blur()
        
    def close_day_drawer(self):
        self.page.get_by_test_id("done-day-btn").click()
        
    def save_as_draft(self):
        self.page.get_by_test_id("save-draft-btn").click()
        # After a successful save the app calls router.push("/timesheets").
        # Waiting for that navigation is more reliable than asserting on an
        # ephemeral toast which can be dismissed before Playwright sees it.
        self.page.wait_for_url("**/timesheets", timeout=15000)

    def auto_fill(self):
        """
        Clicks the Auto-fill button which fills all empty working days up to today
        with the expected hours. Required before submitting to pass the submitGate check.
        """
        self.page.get_by_test_id("auto-fill-btn").click()
        # Auto-fill is a client-side state mutation — no navigation fires.
        # The real proof it worked is that submitGate.blocked becomes false,
        # which directly enables the submit button (TimesheetGrid.tsx:1577).
        # This avoids matching against toast text that varies by whether a
        # project template exists or not.
        expect(self.page.get_by_test_id("submit-timesheet-btn")).to_be_enabled(timeout=15000)

    def submit_timesheet(self):
        """
        Submits the timesheet. Requires auto_fill() to have been called first
        to ensure the submitGate is unblocked (all working days up to today are filled).
        """
        self.page.get_by_test_id("submit-timesheet-btn").click()
        # After a successful submit the app calls router.push("/timesheets")
        # (TimesheetGrid.tsx:1008) — same path as save_as_draft. Waiting for
        # the URL is a durable assertion that survives any copy changes to the toast.
        self.page.wait_for_url("**/timesheets", timeout=15000)

    def open_first_draft_from_list(self):
        """
        From the timesheets list page, clicks the first row with status 'draft'
        to open it in the grid view.
        """
        self.page.get_by_test_id("timesheet-row-draft").first.click()

    def expect_timesheet_in_list(self, status: str):
        expect(self.page.get_by_test_id(f"timesheet-row-{status}").first).to_be_visible(timeout=15000)