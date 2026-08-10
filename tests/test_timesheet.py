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
    
    ts_page.start_new_timesheet()
    
    # Open the first available working day
    ts_page.open_available_day_by_index(0)
    ts_page.add_project_by_index(0)
    ts_page.log_hours_and_description(0, "8", "Regular development work")
    ts_page.close_day_drawer()
    
    ts_page.save_as_draft()
    
    # Navigate back to list and check status
    ts_page.navigate()
    ts_page.expect_timesheet_in_list("draft")

@pytest.mark.e2e
def test_employee_multi_draft_timesheet(employee_page):
    """
    Test that an employee can navigate to Timesheets, create one,
    add hours to multiple projects on multiple days, save it as a draft, and see it in the list.
    """
    ts_page = TimesheetPage(employee_page)
    ts_page.dismiss_welcome_dialog_if_present()
    ts_page.navigate()

    ts_page.start_new_timesheet()

    # Day 1: Add 2 projects
    ts_page.open_available_day_by_index(0)
    
    ts_page.add_project_by_index(0)
    ts_page.log_hours_and_description(0, "4", "Frontend component development")
    
    ts_page.add_project_by_index(0)
    ts_page.log_hours_and_description(1, "4", "Backend API changes")
    
    ts_page.close_day_drawer()

    # Day 2: Add 2 projects
    ts_page.open_available_day_by_index(0)
    ts_page.add_project_by_index(0)
    ts_page.log_hours_and_description(0, "5", "Writing E2E tests")
    
    ts_page.add_project_by_index(0)
    ts_page.log_hours_and_description(1, "3", "Code review and bug fixes")
    
    ts_page.close_day_drawer()

    ts_page.save_as_draft()
    
    ts_page.navigate()
    ts_page.expect_timesheet_in_list("draft")