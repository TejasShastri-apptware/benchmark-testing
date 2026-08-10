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
        Finds the Nth available day cell that has 'Add time' and clicks it.
        """
        cell = self.page.get_by_text("Add time").nth(index)
        expect(cell).to_be_visible()
        cell.click()
        
    def add_project_by_index(self, index: int):
        """
        Finds the Nth available 'Add work' project button and clicks it.
        """
        add_btn = self.page.locator('button[data-testid^="add-project-"]').nth(index)
        expect(add_btn).to_be_visible()
        add_btn.click()
        
    def log_hours_and_description(self, index: int, hours: str, description: str):
        """
        Fills the hours and description for the Nth project input available in the drawer.
        """
        input_field = self.page.locator('input[data-testid^="hour-input-"]').nth(index)
        expect(input_field).to_be_visible()
        input_field.fill(hours)
        input_field.blur()
        
        desc_field = self.page.locator('textarea[data-testid^="description-input-"]').nth(index)
        expect(desc_field).to_be_visible()
        desc_field.fill(description)
        desc_field.blur()
        
    def close_day_drawer(self):
        self.page.get_by_test_id("done-day-btn").click()
        
    def save_as_draft(self):
        self.page.get_by_test_id("save-draft-btn").click()
        expect(self.page.get_by_text("Draft saved successfully")).to_be_visible(timeout=5000)
        
    def submit_timesheet(self):
        self.page.get_by_test_id("submit-timesheet-btn").click()
        expect(self.page.get_by_text("Timesheet submitted successfully!")).to_be_visible(timeout=5000)

    def expect_timesheet_in_list(self, status: str):
        expect(self.page.get_by_test_id(f"timesheet-row-{status}").first).to_be_visible()