import pytest
import re
from playwright.sync_api import Page, expect
from pages.base_page import BasePage

class TimesheetPage(BasePage):
    def navigate(self):
        self.page.goto("/timesheets")
        expect(self.page.get_by_test_id("new-timesheet-btn")).to_be_visible(timeout=15000)

    def navigate_from_dashboard(self):
        """
        Navigates to the timesheets page via the sidebar nav link from the dashboard.
        Used by the dedicated nav smoke test (TC-TS-NAV) only.
        All other tests use navigate() (direct goto) for speed and isolation.
        Selector: data-testid="nav-link-timesheets" (Sidebar.tsx:780)
        """
        self.page.goto("/dashboard")
        self.page.get_by_test_id("nav-rail-time").click()
        self.page.get_by_test_id("nav-link-timesheets").click()
        expect(self.page).to_have_url(re.compile(r".*/timesheets"))
        expect(self.page.get_by_test_id("new-timesheet-btn")).to_be_visible(timeout=15000)
        
    def start_new_timesheet(self):
        self.page.get_by_test_id("new-timesheet-btn").click()
        
    def open_available_day_by_index(self, index: int = 0):
        """
        Finds an available day cell to open.
        First looks for unlogged empty working days [data-testid^="add-time-"].
        If no empty days exist or not enough exist, falls back to days with existing logged hours [data-testid^="edit-time-"].
        If no available/editable working days exist in the period, skips gracefully via pytest.skip.
        """
        # Ensure the grid calendar has loaded before checking element counts
        self.page.locator('[data-testid^="timesheet-day-cell-"]').first.wait_for(state="visible", timeout=15000)
        
        # Wait up to 5s for an add-time or edit-time element to render
        day_action = self.page.locator('[data-testid^="add-time-"], [data-testid^="edit-time-"]')
        try:
            day_action.first.wait_for(state="visible", timeout=5000)
        except Exception:
            pass # If all days in period are blocked (holidays/weekends), fallback to skip below

        add_cells = self.page.locator('[data-testid^="add-time-"]')
        edit_cells = self.page.locator('[data-testid^="edit-time-"]')
        
        # 1. Primary path: Empty unlogged working day
        add_count = add_cells.count()
        if add_count > index:
            cell = add_cells.nth(index)
            expect(cell).to_be_visible(timeout=10000)
            cell.click()
            return

        # 2. Fallback path: Editable day cell with existing logged hours
        edit_count = edit_cells.count()
        if edit_count > 0:
            target_idx = min(index, edit_count - 1)
            cell = edit_cells.nth(target_idx)
            expect(cell).to_be_visible(timeout=10000)
            cell.click()
            return

        # 3. No clickable day cells found
        pytest.skip(f"No available or editable working days found in the active timesheet period (requested index {index}).")
        
    def add_project_by_index(self, index: int):
        """
        Finds the Nth available 'Add work' project button and clicks it.
        If project inputs already exist (e.g. editing an existing day), no-ops gracefully.
        """
        add_btns = self.page.locator('[data-testid^="add-project-"]')
        if add_btns.count() > index:
            btn = add_btns.nth(index)
            expect(btn).to_be_visible(timeout=10000)
            btn.click()
        elif self.page.locator('[data-testid^="hour-input-"]').count() > 0:
            # An entry input already exists for this day, so adding a new project is not strictly required.
            pass
        else:
            expect(add_btns.nth(0)).to_be_visible(timeout=10000)
            add_btns.nth(0).click()
        
    def log_hours_and_description(self, index: int, hours: str, description: str):
        """
        Fills the hours and description for the Nth project input available in the drawer.
        """
        input_field = self.page.locator('[data-testid^="hour-input-"]').nth(index)
        expect(input_field).to_be_visible(timeout=15000)
        input_field.fill(hours)
        input_field.blur()
        
        desc_field = self.page.locator('[data-testid^="description-input-"]').nth(index)
        expect(desc_field).to_be_visible(timeout=15000)
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