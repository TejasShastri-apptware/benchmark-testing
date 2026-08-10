import pytest
from datetime import datetime
from pages.timesheet_page import TimesheetPage

@pytest.mark.e2e
def test_employee_draft_timesheet(employee_page):
    """
    Test that an employee can navigate to Timesheets, create a new one,
    add hours to a day, save it as a draft, and see it in the list.
    """
    ts_page = TimesheetPage(employee_page)
    ts_page.dismiss_welcome_dialog_if_present()
    ts_page.navigate()
    
    # Check if a draft or submitted timesheet already exists for this month.
    # If not, create a new one. (We just start new timesheet which redirects to it)
    ts_page.start_new_timesheet()
    
    # Open the first available working day (past or present)
    ts_page.open_first_available_day()
    ts_page.add_first_project()
    ts_page.log_hours_for_first_project("8")
    ts_page.close_day_drawer()
    
    ts_page.save_as_draft()
    
    # Navigate back to list and check status
    ts_page.navigate()
    ts_page.expect_timesheet_in_list("draft")
