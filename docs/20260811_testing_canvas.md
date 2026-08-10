# 20260811 E2E Testing Canvas
## Authentication & Timesheets — Scope, Verification & Execution

> **Context:** This document defines the authoritative state of our E2E test framework
> for the two domains currently in scope: **Authentication** and **Timesheets**.
> Leaves are explicitly frozen and excluded. This document is intended to carry
> forward into the next working day (2026-08-11) as the single source of truth.

---

## 1. Scope & Guardrails

### In Scope
| Domain | Coverage |
|---|---|
| Authentication | Login, logout, session fixture integrity (3 personas) |
| Timesheets | Draft (single + multi-day), Submit (with auto-fill), Manager approval (guarded) |

### Explicitly Frozen
| Domain | Status | Reason |
|---|---|---|
| Leaves | Frozen | Halted by lead direction. Tests exist in test_leave.py but are not part of this canvas. |

### Environment Constraint
> WARNING: This framework runs against the live application. There is no dedicated test environment.

The implications for test design:

| Action | Reversible? | Test Status |
|---|---|---|
| Login / Logout | Yes | Enabled |
| Save Draft | Yes (can edit/delete) | Enabled |
| Submit Timesheet | Yes (manager can reject => returns to draft) | ENABLED |
| Manager Approval | No reversal mechanism | Permanently guarded (pytest.mark.skip) |

---

## 2. Code Fixes Applied (2026-08-10)

Three bugs identified during source code audit and fixed before this document was written.

### Fix 1 — timesheet_page.py: Brittle "Add time" text selector
File: e2e_repo/pages/timesheet_page.py

| | Before | After |
|---|---|---|
| Selector | page.get_by_text("Add time").nth(index) | page.locator('[data-testid^="add-time-"]').nth(index) |
| Risk | Breaks on any text/copy change | Anchored to source-verified data-testid |

Source confirmation: TimesheetGrid.tsx:1956 — data-testid={`add-time-${format(date, "yyyy-MM-dd")}`}

---

### Fix 2 — manager_approval_page.py: Stale role-based locators and outdated methods
File: e2e_repo/pages/manager_approval_page.py

Full rewrite. The old file mixed role-based locators with unverified text patterns and included
leave approval methods not relevant to this canvas.

New file uses only source-verified data-testid attributes and contains only timesheet-relevant methods:
- navigate_to_timesheet_approvals() -> /approvals/timesheets
- approve_first_pending_timesheet() -> timesheet-row-submitted + approve-timesheet-btn

---

### Fix 3 — test_timesheet.py: Missing submit test and submitGate unawareness
File: e2e_repo/tests/test_timesheet.py

Added TC-TS-03 (test_employee_submit_timesheet) which:
1. Seeds one day manually (required so auto_fill() has a project template to clone)
2. Calls auto_fill() to satisfy the submitGate (all working days up to today filled)
3. Submits the timesheet and verifies the success toast

Also added auto_fill() method to timesheet_page.py that clicks auto-fill-btn and
waits for the confirmation toast: "Filled working days up to today"

Added TC-TS-04 (test_manager_approves_timesheet) permanently guarded with pytest.mark.skip.

---

## 3. Verified data-testid Contract

All entries confirmed against the live Next.js source code. No aspirational IDs in this table.

### Authentication

| data-testid | Component | File | Line | Used By |
|---|---|---|---|---|
| sign-in-heading | h1 Sign in | LoginForm.tsx | 154 | TC-AUTH-01 logout assertion |
| sign-in-with-password-btn | "Sign in with password" button | LoginForm.tsx | 208 | LoginPage.login() |
| email-input | Email Input | LoginForm.tsx | 250 | LoginPage.login() |
| password-input | Password Input | LoginForm.tsx | 277 | LoginPage.login() |
| sign-in-btn | Submit button | LoginForm.tsx | 304 | LoginPage.login() |
| user-menu-btn | User menu trigger | SidebarUserMenu.tsx | 244 | DashboardPage.logout() |
| logout-menu-item | Logout dropdown item | SidebarUserMenu.tsx | 282 | DashboardPage.logout() |

### Timesheets

| data-testid | Pattern | Component | File | Line | Used By |
|---|---|---|---|---|---|
| new-timesheet-btn | Static | "New Timesheet" button | timesheets/page.tsx | 59 | TimesheetPage.start_new_timesheet() |
| add-time-{yyyy-MM-dd} | Dynamic (date) | "Add time" div in day cell | TimesheetGrid.tsx | 1956 | open_available_day_by_index() |
| add-project-{slot.id} | Dynamic (UUID) | Add work button per project slot | TimesheetGrid.tsx | 2193 | add_project_by_index() |
| hour-input-{slot.id} | Dynamic (UUID) | Hours Input in drawer | TimesheetGrid.tsx | 2120 | log_hours_and_description() |
| description-input-{slot.id} | Dynamic (UUID) | Notes Textarea in drawer | TimesheetGrid.tsx | 2152 | log_hours_and_description() |
| done-day-btn | Static | "Done" button closing the drawer | TimesheetGrid.tsx | 2205 | close_day_drawer() |
| auto-fill-btn | Static | "Auto-fill" button in toolbar | TimesheetGrid.tsx | 1548 | auto_fill() |
| save-draft-btn | Static | "Save Draft" button | TimesheetGrid.tsx | 1559 | save_as_draft() |
| submit-timesheet-btn | Static | "Submit" button (conditionally disabled) | TimesheetGrid.tsx | 1579 | submit_timesheet() |
| timesheet-row-{status} | Dynamic (status) | Status cell div in list table | TimesheetList.tsx | 198 | expect_timesheet_in_list() |
| timesheet-row-submitted | Static instance | Status=submitted row | TimesheetList.tsx | 198 | approve_first_pending_timesheet() |
| approve-timesheet-btn | Static | "Approve" button in grid toolbar | TimesheetGrid.tsx | 1531 | approve_first_pending_timesheet() |

### Known Behavioral Notes (from source)

| Element | Behavioral Note | Impact on Tests |
|---|---|---|
| sign-in-btn | After success, router.push("/dashboard") fires after a 1-second setTimeout (LoginForm.tsx:96) | login() assertion on URL must allow time for redirect |
| submit-timesheet-btn | Disabled when submitGate.blocked = true (missing or underfilled days) | auto_fill() must be called before submit_timesheet() |
| auto-fill-btn | Fires a toast on completion; never overwrites existing hours | auto_fill() waits on toast text "Filled working days up to today" |
| add-time-{date} | Only rendered when: current month, not future, no hours logged, not read-only | open_available_day_by_index(0) may fail if all days already have hours |

---

## 4. Authentication Test Suite

### TC-AUTH-01: Raw Login and Logout Flow
File: tests/test_auth.py -> test_raw_login_and_logout_flow
Persona: Employee (raw credentials, no session injection)
Status: ENABLED

| Step | Action | Assertion | Selector / Method |
|---|---|---|---|
| 1 | Navigate to /login | - | LoginPage.navigate() |
| 2 | Login with employee credentials | Redirects to /dashboard | LoginPage.login(email, password) |
| 3 | Verify dashboard is loaded | Dashboard renders | DashboardPage.verify_is_loaded() |
| 4 | Logout | Redirects to /login | DashboardPage.logout() |
| 5 | Verify login page visible | sign-in-heading present | expect(page).to_have_url(re.compile(r".*/login")) |

Preconditions: E2E_EMPLOYEE_EMAIL and E2E_EMPLOYEE_PASSWORD set in .env.e2e

---

### TC-AUTH-02: Admin Pre-Authenticated Session
File: tests/test_auth.py -> test_admin_pre_authenticated
Persona: Admin (session fixture)
Status: ENABLED

| Step | Action | Assertion |
|---|---|---|
| 1 | admin_page fixture injects stored auth state | No login screen shown |
| 2 | Navigate directly to /dashboard | Dashboard renders without redirect to login |

---

### TC-AUTH-03: Employee Pre-Authenticated Session
File: tests/test_auth.py -> test_employee_pre_authenticated
Persona: Employee (session fixture)
Status: ENABLED

Same flow as TC-AUTH-02 using the employee_page fixture.

---

### TC-AUTH-04: Manager Pre-Authenticated Session
File: tests/test_auth.py -> test_manager_pre_authenticated
Persona: Manager (session fixture)
Status: ENABLED

Same flow as TC-AUTH-02 using the manager_page fixture.

---

## 5. Timesheet Test Suite

### TC-TS-01: Employee Creates Single-Project Draft
File: tests/test_timesheet.py -> test_employee_draft_timesheet
Persona: Employee
Status: ENABLED

| Step | Action | Assertion | Key Selector |
|---|---|---|---|
| 1 | Navigate to /timesheets | new-timesheet-btn visible | TimesheetPage.navigate() |
| 2 | Start new timesheet | Grid opens | new-timesheet-btn |
| 3 | Open first available day | Day drawer opens | [data-testid^="add-time-"] nth(0) |
| 4 | Add project | Project slot appears | [data-testid^="add-project-"] nth(0) |
| 5 | Log 8h + description | Fields filled | hour-input-{id}, description-input-{id} |
| 6 | Close drawer | Drawer closed | done-day-btn |
| 7 | Save as draft | Toast: "Draft saved successfully" | save-draft-btn |
| 8 | Navigate back to /timesheets | Draft row visible in list | timesheet-row-draft |

---

### TC-TS-02: Employee Creates Multi-Project, Multi-Day Draft
File: tests/test_timesheet.py -> test_employee_multi_draft_timesheet
Persona: Employee
Status: ENABLED

Same flow as TC-TS-01 but:
- Day 1: 2 projects (4h + 4h)
- Day 2: 2 projects (5h + 3h)
- Final assertion: timesheet-row-draft in list

---

### TC-TS-03: Employee Submits Timesheet via Auto-fill
File: tests/test_timesheet.py -> test_employee_submit_timesheet
Persona: Employee
Status: ENABLED — safe for live environment

| Step | Action | Assertion | Key Selector |
|---|---|---|---|
| 1 | Navigate to /timesheets | new-timesheet-btn visible | TimesheetPage.navigate() |
| 2 | Start new timesheet | Grid opens | new-timesheet-btn |
| 3 | Open first available day | Day drawer opens | [data-testid^="add-time-"] nth(0) |
| 4 | Add project + log 8h | Provides template for auto-fill | add-project-*, hour-input-* |
| 5 | Close drawer | - | done-day-btn |
| 6 | Auto-fill | Toast: "Filled working days up to today" | auto-fill-btn |
| 7 | Submit | Toast: "Timesheet submitted successfully!" | submit-timesheet-btn |
| 8 | Verify list | timesheet-row-submitted visible | TimesheetList.tsx:198 |

Why auto-fill is mandatory before submit:
TimesheetGrid.tsx:1577 — disabled={isSubmitting || submitGate.blocked}
submitGate.blocked is true when any working day up to today has zero or underfilled hours.
Auto-fill resolves this by filling all empty days using the manually seeded project split.

Recovery if this leaves dirty state:
Manager navigates to /approvals/timesheets -> finds the submitted timesheet -> clicks Reject.
The timesheet returns to draft state, available for the next run.

---

### TC-TS-04: Manager Approves Submitted Timesheet [GUARDED — DO NOT RUN]
File: tests/test_timesheet.py -> test_manager_approves_timesheet
Persona: Manager
Status: PERMANENTLY GUARDED via pytest.mark.skip

  @pytest.mark.skip(
      reason="TC-TS-04 [GUARDED]: Manager approval is IRREVERSIBLE..."
  )

| Step | Action | Assertion | Key Selector |
|---|---|---|---|
| 1 | Navigate to /approvals/timesheets | - | ManagerApprovalPage.navigate_to_timesheet_approvals() |
| 2 | Open first submitted timesheet | Grid opens | timesheet-row-submitted |
| 3 | Approve | Toast: "Timesheet approved successfully" | approve-timesheet-btn |

Precondition: TC-TS-03 must have run and left a timesheet in submitted state.
Re-enable only in a dedicated test environment with full data reset capability.

---

## 6. Session Fixture Architecture

conftest.py
  admin_state   (scope=session) -> .auth/admin_state.json
  employee_state (scope=session) -> .auth/employee_state.json
  manager_state (scope=session) -> .auth/manager_state.json

TTL: 55 minutes (AUTH_STATE_TTL_SECONDS = 55*60)
If stale: deletes JSON file, performs fresh login, saves new state

Fixture hierarchy per test:
  admin_page / employee_page / manager_page (scope=function)
    -> creates fresh BrowserContext from stored state
    -> new_page() yields page
    -> context.close() on teardown

Implication for test isolation: Each test gets a brand new browser context (cookies, storage)
but shares the same login session token. Tests are isolated at the UI level but share DB state.

---

## 7. Execution Runbook

Prerequisites:
  cd C:\Users\Admin\Desktop\e2e_repo
  .\testvenv\Scripts\Activate.ps1
  # Verify .env.e2e has all three personas configured

Run Full Suite (Auth + Timesheets, skipping leaves and guarded tests):
  pytest tests/test_auth.py tests/test_timesheet.py -v --html=e2e-report.html

Run Auth Only:
  pytest tests/test_auth.py -v

Run Timesheets Only (excludes guarded TC-TS-04 automatically):
  pytest tests/test_timesheet.py -v -k "not manager_approves"

What "Passing" looks like:
  tests/test_auth.py::test_raw_login_and_logout_flow          PASSED
  tests/test_auth.py::test_admin_pre_authenticated            PASSED
  tests/test_auth.py::test_employee_pre_authenticated         PASSED
  tests/test_auth.py::test_manager_pre_authenticated          PASSED
  tests/test_timesheet.py::test_employee_draft_timesheet      PASSED
  tests/test_timesheet.py::test_employee_multi_draft_timesheet PASSED
  tests/test_timesheet.py::test_employee_submit_timesheet     PASSED
  tests/test_timesheet.py::test_manager_approves_timesheet    SKIPPED

8 tests collected: 7 passed, 1 skipped is a clean run.

---

## 8. Known Open Items & Next Steps

| # | Item | Priority | Notes |
|---|---|---|---|
| 1 | auto_fill() toast text match | Medium | Matches "Filled working days up to today". If no seed project exists, the toast says the full string with hours details — substring match via get_by_text should still work. Verify on first run. |
| 2 | TC-TS-03 and TC-TS-01 conflict within one session | Medium | If TC-TS-01 runs first and creates a draft, TC-TS-03's start_new_timesheet() click may open that draft instead of creating new. App may only allow one active timesheet per period. Observe on first combined run. |
| 3 | Post-submission list navigation timing | Low | After submit, router.push("/timesheets") fires server-side. expect_timesheet_in_list("submitted") waits for element. Should pass; add wait_for_url if flaky. |
| 4 | Session TTL in CI | Low | Auth state TTL is 55 minutes. Long-running CI pipelines must ensure sessions are refreshed. Handled by conftest.py TTL check. |
| 5 | Manager approval (TC-TS-04) re-enable path | Future | Enable only once dedicated test/staging environment available with data reset capability. |

---

Document created: 2026-08-10
Next session: 2026-08-11 — continue from this canvas
