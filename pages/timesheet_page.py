from playwright.sync_api import Page, expect
from pages.base_page import BasePage

class TimesheetPage(BasePage):
    def navigate(self):
        self.page.goto("/timesheets")
        # Ensure the page has loaded by checking for the new timesheet button
        expect(self.page.get_by_test_id("new-timesheet-btn")).to_be_visible()
        
    def start_new_timesheet(self):
        self.page.get_by_test_id("new-timesheet-btn").click()
        
    def open_first_available_day(self):
        """
        Finds the first available day cell that has 'Add time' and clicks it.
        """
        cell = self.page.get_by_text("Add time").first
        expect(cell).to_be_visible()
        cell.click()
        
    def add_first_project(self):
        """
        Finds the first available 'Add work' project button and clicks it.
        """
        add_btn = self.page.locator('button[data-testid^="add-project-"]').first
        expect(add_btn).to_be_visible()
        add_btn.click()
        
    def log_hours_for_first_project(self, hours: str):
        """
        Fills the hours for the first project input available in the drawer.
        """
        input_field = self.page.locator('input[data-testid^="hour-input-"]').first
        expect(input_field).to_be_visible()
        input_field.fill(hours)
        input_field.blur()
        
    def close_day_drawer(self):
        self.page.get_by_test_id("done-day-btn").click()
        
    def save_as_draft(self):
        self.page.get_by_test_id("save-draft-btn").click()
        # Wait for potential toast notification
        expect(self.page.get_by_text("Draft saved successfully")).to_be_visible(timeout=5000)
        
    def submit_timesheet(self):
        self.page.get_by_test_id("submit-timesheet-btn").click()
        expect(self.page.get_by_text("Timesheet submitted successfully!")).to_be_visible(timeout=5000)

    def expect_timesheet_in_list(self, status: str):
        """
        Verifies that at least one timesheet row with the given status exists.
        Status could be 'draft', 'submitted', 'approved', 'rejected'.
        """
        expect(self.page.get_by_test_id(f"timesheet-row-{status}").first).to_be_visible()