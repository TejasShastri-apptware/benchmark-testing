from playwright.sync_api import Page
from pages.employee_leave_page import EmployeeLeavePage
from pages.manager_approval_page import ManagerApprovalPage

def test_employee_applies_and_manager_approves_leave(employee_page: Page, manager_page: Page):
    """
    End-to-End Test for Leave Workflow.
    1. Employee logs in and applies for leave.
    2. Manager logs in, sees the request, and approves it.
    """
    employee_leave = EmployeeLeavePage(employee_page)
    manager_approval = ManagerApprovalPage(manager_page)
    
    # ---------------------------------------------------------
    # ACT 1: Employee applies for leave
    # ---------------------------------------------------------
    employee_leave.navigate_to_leave_requests()
    employee_leave.apply_for_casual_leave(dates=["17", "18"], reason="playwright - testing leave application")
    employee_leave.verify_leave_is_pending("Casual Leaves")
    
    # ---------------------------------------------------------
    # ACT 2: Manager approves the leave
    # ---------------------------------------------------------
    manager_approval.navigate_to_dashboard()
    manager_approval.check_and_open_notification(employee_name="John Employee")
    manager_approval.navigate_to_leave_approvals()
    manager_approval.approve_pending_leave(employee_name="John Employee", feedback="playwright - leave approved")
    manager_approval.verify_leave_is_approved()
