# Timesheet Submission E2E Testing Plan

## Overview
This plan outlines the approach to writing robust End-to-End (E2E) tests for the timesheet submission flow. In accordance with our updated testing guidelines, we will heavily utilize `data-testid` locators to ensure tests are resilient against UI changes.

## Step 1: Inject `data-testid` Attributes
We need to update the React components in the Next.js app to expose testable IDs.

**1. `src/app/(dashboard)/timesheets/page.tsx` & `TimesheetList.tsx`**
- `data-testid="new-timesheet-btn"`: The button to create a new timesheet.
- `data-testid="timesheet-row-{status}"`: Identifiers for the rows in the timesheet list to easily find pending/draft timesheets.

**2. `src/components/timesheets/TimesheetGrid.tsx`**
- `data-testid="project-select"`: The dropdown to select a project for the timesheet row.
- `data-testid="hour-input-{projectId}-{date}"`: The specific input cells for logging hours.
- `data-testid="save-draft-btn"`: The button to save progress.
- `data-testid="submit-timesheet-btn"`: The button to finalize and submit.

## Step 2: Create Page Objects (`e2e/pages/timesheet_page.py`)
We will create a new Page Object Model (POM) to abstract the timesheet interactions.

- `navigate_to_timesheets()`: Navigates to `/timesheets`.
- `start_new_timesheet()`: Clicks the New Timesheet button.
- `add_project(project_name)`: Selects a project to add a row.
- `log_hours(project_name, date, hours)`: Fills a specific cell.
- `save_as_draft()`: Clicks the save draft button.
- `submit_timesheet()`: Clicks the submit button and confirms the dialog.

## Step 3: Write Detailed Test Cases (`e2e/tests/test_timesheets.py`)

1. **Test: Multi-Project & Multi-Day Draft**
   - Log in as Employee.
   - Start a New Timesheet (or open existing draft for the month).
   - Open a working day drawer.
   - Add first project, log 4 hours.
   - Add second project, log 4 hours.
   - Close drawer.
   - Save as Draft.
   - Verify it appears as "Draft" in the Timesheets list.

2. **Test: Auto-fill & Submit Timesheet**
   - Log in as Employee.
   - Open the existing "Draft" timesheet from the list.
   - Click the "Auto-fill" button to populate remaining required working days up to today.
   - Click "Submit".
   - Verify the timesheet appears as "Pending approval" (submitted) in the list.

3. **Test: Manager Approval (Pending)**
   - Log in as Manager.
   - Navigate to Timesheet Approvals.
   - Open the submitted timesheet.
   - Approve it.
   - Verify status changes to "Approved".

## Step 4: Additional `data-testid` Injections
- Add `data-testid="auto-fill-btn"` to the Auto-fill button in `TimesheetGrid.tsx`.
- Update POM methods to support `.nth(index)` for selecting multiple projects in a single day drawer.
