import pytest
from datetime import datetime
from pages.timesheet_page import TimesheetPage
from pages.manager_approval_page import ManagerApprovalPage

@pytest.mark.e2e
@pytest.mark.ts_nav
def test_nav_to_timesheets_from_dashboard(employee_page):
    """
    TC-TS-NAV: Verifies that the Timesheets sidebar nav link correctly navigates
    from the dashboard to the timesheets list page.

    This is the only timesheet test that exercises UI navigation.
    All subsequent tests (TC-TS-01 onward) use direct goto() for speed and
    isolation — they test timesheet functionality, not navigation.

    Selector: data-testid="nav-link-timesheets" (Sidebar.tsx:780)
    """
    ts_page = TimesheetPage(employee_page)
    ts_page.dismiss_welcome_dialog_if_present()
    ts_page.navigate_from_dashboard()

@pytest.mark.e2e
@pytest.mark.ts_draft
def test_employee_draft_timesheet(employee_page):

    """
    TC-TS-01: Employee creates a single-project, single-day draft.
    Verifies the draft appears in the timesheet list.
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
@pytest.mark.ts_draft
def test_employee_multi_draft_timesheet(employee_page):
    """
    TC-TS-02: Employee creates a multi-day draft with the single available project.
    Verifies the draft appears in the timesheet list.
    """
    ts_page = TimesheetPage(employee_page)
    ts_page.dismiss_welcome_dialog_if_present()
    ts_page.navigate()

    ts_page.start_new_timesheet()

    # Day 1: Add project
    ts_page.open_available_day_by_index(0)
    
    ts_page.add_project_by_index(0)
    ts_page.log_hours_and_description(0, "4", "Frontend component development")
    
    ts_page.close_day_drawer()

    # Day 2: Add project
    # Since day 1 was logged, the next available day is now at index 0
    ts_page.open_available_day_by_index(0)
    ts_page.add_project_by_index(0)
    ts_page.log_hours_and_description(0, "5", "Writing E2E tests")
    
    ts_page.close_day_drawer()

    ts_page.save_as_draft()
    
    ts_page.navigate()
    ts_page.expect_timesheet_in_list("draft")

@pytest.mark.e2e
@pytest.mark.ts_submit
def test_employee_submit_timesheet(employee_page):
    """
    TC-TS-03: Employee submits a timesheet via auto-fill.

    Flow:
      1. Navigate to /timesheets and create a new timesheet.
      2. Log hours on at least one day manually so there is a project seed for auto-fill.
      3. Call auto_fill() — fills all empty working days up to today using the
         logged project split, satisfying the submitGate (no missing/underfilled days).
      4. Submit the timesheet and assert the success toast.
      5. Confirm the timesheet appears with status 'submitted' in the list.

    Environment note:
      A submitted timesheet can be REJECTED by the manager, returning it to
      an editable draft state. This makes submission safe to run against the
      live environment. This test is ENABLED and should be run as part of the
      standard suite.

    Recovery:
      If this test leaves a timesheet in 'submitted' state, a manager must
      manually reject it via /approvals/timesheets to reset it.
    """
    ts_page = TimesheetPage(employee_page)
    ts_page.dismiss_welcome_dialog_if_present()
    ts_page.navigate()

    ts_page.start_new_timesheet()

    # Log hours on the first available working day to seed the project split.
    # auto_fill() will use this split to populate remaining days.
    ts_page.open_available_day_by_index(0)
    ts_page.add_project_by_index(0)
    ts_page.log_hours_and_description(0, "8", "Seeding auto-fill split")
    ts_page.close_day_drawer()

    # Auto-fill all empty working days up to today.
    # This is required to unblock the submitGate before submission.
    ts_page.auto_fill()

    # Submit and verify the success toast.
    ts_page.submit_timesheet()

    # After submission router.push("/timesheets") fires; verify list state.
    ts_page.expect_timesheet_in_list("submitted")


@pytest.mark.e2e
@pytest.mark.ts_approve
@pytest.mark.skip(
    reason=(
        "TC-TS-04 [GUARDED]: Manager approval is IRREVERSIBLE in the current environment. "
        "There is no mechanism to undo an approval. Do not run this test against live data. "
        "Enable only in a dedicated test environment with a full data reset capability."
    )
)
def test_manager_approves_timesheet(manager_page):
    """
    TC-TS-04: Manager approves the first submitted timesheet.

    Precondition: TC-TS-03 must have run and a timesheet must be in 'submitted' state.
    This test is permanently skip-guarded. See the @pytest.mark.skip reason above.
    """
    approval_page = ManagerApprovalPage(manager_page)
    approval_page.navigate_to_timesheet_approvals()
    approval_page.approve_first_pending_timesheet()