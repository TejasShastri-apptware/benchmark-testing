# E2E Framework Analysis — 2026-08-11

> **Scope**: Auth + Timesheet flows only. Leave tests are deliberately excluded from active scope.
> **Repo**: `C:\Users\Admin\Desktop\e2e_repo`
> **App Under Test**: NextJS at `C:\Users\Admin\Desktop\Benchmark\Benchmark2\apptware-bench-mark` (running on `http://localhost:3000`)

---

## 1. High-Level Architecture

```
e2e_repo/
├── conftest.py              # Fixtures, session management, reporting hook
├── pytest.ini               # Global pytest config (base_url, addopts, tracing/video)
├── .env.e2e                 # Credentials + Google reporting config (gitignored)
├── pages/                   # Page Object Model (POM) layer
│   ├── base_page.py         # BasePage — shared helpers (dismiss_welcome_dialog)
│   ├── login_page.py        # LoginPage
│   ├── dashboard_page.py    # DashboardPage
│   ├── timesheet_page.py    # TimesheetPage (most complex POM)
│   ├── manager_approval_page.py
│   └── employee_leave_page.py  # [OUT OF ACTIVE SCOPE]
├── tests/
│   ├── test_auth.py         # 4 tests (3 active + TC-AUTH-01 raw)
│   ├── test_timesheet.py    # 4 tests (3 active + TC-TS-04 guarded)
│   └── test_leave.py        # [OUT OF ACTIVE SCOPE]
└── utils/
    └── google_reporter.py   # Google Sheets + Drive reporter
```

### Design Principles (from canvas + code)
- **Selector strategy**: Exclusively `data-testid` / `data-testid^=` prefix selectors via Playwright's `get_by_test_id()` and `.locator('[data-testid^="..."]')`. Zero reliance on CSS classes, XPath, or visual/role-based selectors (except for the leave page, which is out of scope and intentionally not migrated).
- **Page Object Model**: Every page has a dedicated class inheriting `BasePage`. Tests never touch raw selectors directly.
- **Session reuse (TTL-based)**: Auth states are stored as JSON files in `.auth/` and reused across the session if age < 55 minutes. Avoids repeated login network calls.
- **Persona isolation**: Three distinct personas (Admin, Employee, Manager), each with their own stored state and page fixture. Each test gets a **fresh browser context** (isolated cookies/storage) built on a **shared login token**.
- **Google Sheets reporting**: Built as an opt-in side-effect. If the three Google env vars are present, every test result (name, status, duration, error, screenshot Drive link) is appended to the sheet automatically.

---

## 2. Framework Orchestration (conftest.py)

### Startup Sequence

```
pytest_configure()
  ├── Load .env.e2e  (via python-dotenv)
  ├── Override base_url from E2E_BASE_URL env var if set
  │     (falls back to pytest.ini: http://localhost:3000)
  └── Initialize GoogleReporter if GOOGLE_SHEET_ID + GOOGLE_DRIVE_FOLDER_ID + GOOGLE_CREDENTIALS_PATH all set
```

### Fixture Hierarchy

```
playwright (provided by pytest-playwright)
│
├── admin_state  [scope=session]
│     ├── reads E2E_ADMIN_EMAIL / E2E_ADMIN_PASSWORD from env
│     ├── checks .auth/admin_state.json age (< 55 min → reuse, else delete + fresh login)
│     └── saves context.storage_state() → .auth/admin_state.json
│
├── employee_state  [scope=session]
│     └── same pattern → .auth/employee_state.json
│
└── manager_state  [scope=session]
      └── same pattern → .auth/manager_state.json

browser (provided by pytest-playwright, scope=function)
│
├── admin_page  [scope=function]
│     ├── browser.new_context(storage_state=admin_state)
│     ├── context.new_page() → yields page
│     └── context.close() on teardown
│
├── employee_page  [scope=function]   ← used by all timesheet tests
│     └── same pattern
│
└── manager_page  [scope=function]
      └── same pattern
```

> **Key implication**: Tests share DB state but are isolated at the browser context level. TC-TS-01 (draft) and TC-TS-03 (submit) both hit the same employee account and therefore interact with the same live timesheet data. Run order matters.

### Reporting Hook

```
pytest_runtest_makereport  [tryfirst=True, hookwrapper]
  ├── Fires on rep.when == "call" (actual test body, not setup/teardown)
  ├── Extracts page from funcargs: [page, admin_page, employee_page, manager_page]
  ├── Takes screenshot → test-results/{test_name}.png
  ├── Uploads screenshot to Google Drive (public reader link)
  └── Appends row to Google Sheet:
        [timestamp, test_name, status, duration, error_msg[:500], screenshot_link]
```

---

## 3. Page Object Model — Method Index

### BasePage (`pages/base_page.py`)
| Method | Selector Used | Notes |
|---|---|---|
| `dismiss_welcome_dialog_if_present()` | `get-started-btn` | Silent timeout if dialog absent |

### LoginPage (`pages/login_page.py`) → extends BasePage
| Method | Selector Used | Notes |
|---|---|---|
| `navigate()` | — | `goto("/login")` |
| `login(email, password)` | `sign-in-with-password-btn`, `email-input`, `password-input`, `sign-in-btn` | Handles Google Auth toggle; asserts redirect to `/dashboard` |

### DashboardPage (`pages/dashboard_page.py`) → extends BasePage
| Method | Selector Used | Notes |
|---|---|---|
| `navigate()` | — | `goto("/dashboard")` |
| `verify_is_loaded()` | `user-menu-btn` | URL regex + element check |
| `logout()` | `user-menu-btn`, `logout-menu-item` | Two-click flow |

### TimesheetPage (`pages/timesheet_page.py`) → extends BasePage
| Method | Selector Used | Notes |
|---|---|---|
| `navigate()` | `new-timesheet-btn` | `goto("/timesheets")` + assert btn visible |
| `start_new_timesheet()` | `new-timesheet-btn` | Clicks to open grid |
| `open_available_day_by_index(index)` | `[data-testid^="add-time-"]` nth(n) | Prefix selector — robust to dynamic IDs |
| `add_project_by_index(index)` | `[data-testid^="add-project-"]` nth(n) | Same prefix pattern |
| `log_hours_and_description(index, hours, desc)` | `[data-testid^="hour-input-"]` nth(n), `[data-testid^="description-input-"]` nth(n) | fill + blur to trigger validation |
| `close_day_drawer()` | `done-day-btn` | |
| `save_as_draft()` | `save-draft-btn` | Waits for URL `**/timesheets` (15s timeout) instead of toast |
| `auto_fill()` | `auto-fill-btn`, then `submit-timesheet-btn` enabled | Waits for submit-btn to become enabled — proxy for submitGate unblock |
| `submit_timesheet()` | `submit-timesheet-btn` | Waits for URL `**/timesheets` (15s) |
| `open_first_draft_from_list()` | `timesheet-row-draft` .first | |
| `expect_timesheet_in_list(status)` | `timesheet-row-{status}` .first | 15s timeout |

### ManagerApprovalPage (`pages/manager_approval_page.py`) → extends BasePage
| Method | Selector Used | Notes |
|---|---|---|
| `navigate_to_dashboard()` | — | `goto("/dashboard")` |
| `open_notifications()` | `notifications-btn` | |
| `open_first_notification()` | `open-notification-btn` .first | |
| `expect_notification_visible()` | `mark-read-btn` .first | |
| `navigate_to_timesheet_approvals()` | — | `goto("/approvals/timesheets")` |
| `approve_first_pending_timesheet()` | `timesheet-row-submitted`, `approve-timesheet-btn` | **IRREVERSIBLE** — only called by guarded TC-TS-04 |

---

## 4. Auth Test Suite (test_auth.py)

**4 tests total — 4 active.**

### TC-AUTH-01 — `test_raw_login_and_logout_flow`
- **Fixture**: `page` (bare, no pre-auth)
- **Persona**: Employee (raw credentials from env)
- **Flow**: `navigate("/login")` → `login(email, pw)` → `verify_is_loaded()` → `logout()` → assert URL matches `r".*/login"` + `sign-in-heading` visible
- **Purpose**: Validates that the UI login/logout mechanism actually works end-to-end. Independent of session fixtures.

### TC-AUTH-02 — `test_admin_pre_authenticated`
- **Fixture**: `admin_page`
- **Flow**: `navigate("/dashboard")` → `verify_is_loaded()`
- **Purpose**: Validates that the `admin_state` fixture correctly injects stored auth and bypasses the login screen.

### TC-AUTH-03 — `test_employee_pre_authenticated`
- **Fixture**: `employee_page`
- **Flow**: Same as TC-AUTH-02
- **Purpose**: Same for employee persona.

### TC-AUTH-04 — `test_manager_pre_authenticated`
- **Fixture**: `manager_page`
- **Flow**: Same as TC-AUTH-02
- **Purpose**: Same for manager persona.

> **Pattern note**: TC-AUTH-02/03/04 are lightweight session-validity smoke tests. If any of these fail, it usually means the `.auth/*.json` file is stale or the app's auth cookie changed — clear `.auth/` and re-run.

---

## 5. Timesheet Test Suite (test_timesheet.py)

**4 tests total — 3 active, 1 permanently guarded.**

All active tests use the `employee_page` fixture.

### TC-TS-01 — `test_employee_draft_timesheet`
- **Mark**: `@pytest.mark.e2e`
- **Flow**:
  1. `dismiss_welcome_dialog_if_present()`
  2. `navigate()` → `start_new_timesheet()`
  3. `open_available_day_by_index(0)` → `add_project_by_index(0)` → `log_hours_and_description(0, "8", "Regular development work")` → `close_day_drawer()`
  4. `save_as_draft()` → waits for URL redirect
  5. `navigate()` → `expect_timesheet_in_list("draft")`
- **Assertion**: `timesheet-row-draft` visible in list

### TC-TS-02 — `test_employee_multi_draft_timesheet`
- **Mark**: `@pytest.mark.e2e`
- **Flow**: Same as TC-TS-01 but spans 2 days with 2 projects each:
  - Day 1: `(4h, "Frontend component development")` + `(4h, "Backend API changes")`
  - Day 2: `(5h, "Writing E2E tests")` + `(3h, "Code review and bug fixes")`
- **Note**: `open_available_day_by_index(0)` is called again for day 2 — after day 1's drawer closes, the next available cell becomes index 0 again.

> [!WARNING]
> **Known conflict (Open Item #2)**: If TC-TS-01 runs first and creates a draft for the current period, TC-TS-02's `start_new_timesheet()` may re-open the existing draft rather than creating a new one (the app may only allow one active timesheet per period). Observe on the first combined run.

### TC-TS-03 — `test_employee_submit_timesheet`
- **Mark**: `@pytest.mark.e2e`
- **Flow**:
  1. `navigate()` → `start_new_timesheet()`
  2. Seed one day: `open_available_day_by_index(0)` → `add_project_by_index(0)` → `log_hours_and_description(0, "8", "Seeding auto-fill split")` → `close_day_drawer()`
  3. `auto_fill()` → clicks `auto-fill-btn`, then waits for `submit-timesheet-btn` to become **enabled** (proxy for `submitGate.blocked = false`)
  4. `submit_timesheet()` → waits for URL `**/timesheets`
  5. `expect_timesheet_in_list("submitted")`
- **Why auto-fill is mandatory**: `TimesheetGrid.tsx:1577` — `disabled={isSubmitting || submitGate.blocked}`. `submitGate.blocked` is true when any working day up to today has zero/underfilled hours.
- **Safety**: A submitted timesheet can be rejected by a manager, returning it to draft. This test is safe against live data.
- **Recovery**: Manager navigates to `/approvals/timesheets` → finds the submitted timesheet → clicks Reject.

### TC-TS-04 — `test_manager_approves_timesheet` [GUARDED]
- **Mark**: `@pytest.mark.e2e` + `@pytest.mark.skip(reason="TC-TS-04 [GUARDED]: ...")`
- **Fixture**: `manager_page`
- **Status**: Permanently skipped. Manager approval is **IRREVERSIBLE** in the current environment.
- **Precondition**: TC-TS-03 must have run and left a timesheet in `submitted` state.
- **Re-enable path**: Only in a dedicated test environment with full data reset capability.

---

## 6. Selector Strategy — Compliance Assessment

| Component | Strategy Used | Compliant with Canvas? |
|---|---|---|
| LoginPage | `get_by_test_id()` for all fields | ✅ Yes |
| DashboardPage | `get_by_test_id()` for user-menu, logout | ✅ Yes |
| TimesheetPage — static elements | `get_by_test_id()` | ✅ Yes |
| TimesheetPage — dynamic cells | `[data-testid^="add-time-"]` nth(n) | ✅ Yes — prefix match, index-based |
| TimesheetPage — dynamic inputs | `[data-testid^="hour-input-"]` nth(n) | ✅ Yes |
| ManagerApprovalPage | `get_by_test_id()` | ✅ Yes |
| EmployeeLeavePage | `get_by_role()`, `get_by_placeholder()` | ⚠️ **Non-compliant** — but intentionally out of scope |
| BasePage | `get_by_test_id("get-started-btn")` | ✅ Yes |

> **Verdict**: The in-scope flows (auth + timesheets) are **fully compliant** with the data-testid strategy. The leave page was not migrated and is deliberately excluded.

---

## 7. Reporting Architecture

### Google Sheets Integration

```
GoogleReporter (utils/google_reporter.py)
  ├── Auth: OAuth2 user credentials (token.json + client_secrets.json)
  │         Auto-refreshes expired tokens via refresh_token
  ├── Sheet: append_row() → sheet1 of GOOGLE_SHEET_ID
  │         Columns: [timestamp, test_name, status, duration, error_msg, screenshot_link]
  └── Drive: upload_screenshot() → uploads PNG to GOOGLE_DRIVE_FOLDER_ID
             Sets 'anyone reader' permission → returns webViewLink
```

### Opt-in Behavior
- Reporter is **only instantiated** if all three env vars are set: `GOOGLE_SHEET_ID`, `GOOGLE_DRIVE_FOLDER_ID`, `GOOGLE_CREDENTIALS_PATH`
- If any are missing, `reporter = None` and all reporting is silently skipped
- Reporter init failures are caught and logged — they do not fail the test run

### pytest.ini — Retained Artifacts
```ini
--tracing=retain-on-failure    # Playwright trace zip saved only on failure
--video=retain-on-failure      # Video recording saved only on failure  
--screenshot=only-on-failure   # Playwright auto-screenshot on failure
--html=e2e-report.html         # pytest-html report always generated
--self-contained-html          # HTML report is a single portable file
```

---

## 8. Execution Runbook

### Prerequisites
```powershell
cd C:\Users\Admin\Desktop\e2e_repo
.\testvenv\Scripts\Activate.ps1
# Ensure .env.e2e has all three personas + Google vars configured
```

### Commands
| Goal | Command |
|---|---|
| Full active suite | `pytest tests/test_auth.py tests/test_timesheet.py -v --html=e2e-report.html` |
| Auth only | `pytest tests/test_auth.py -v` |
| Timesheets only | `pytest tests/test_timesheet.py -v -k "not manager_approves"` |
| Clear stale sessions | Delete `.auth/*.json` then re-run |

### Expected Clean Run Output
```
tests/test_auth.py::test_raw_login_and_logout_flow          PASSED
tests/test_auth.py::test_admin_pre_authenticated            PASSED
tests/test_auth.py::test_employee_pre_authenticated         PASSED
tests/test_auth.py::test_manager_pre_authenticated          PASSED
tests/test_timesheet.py::test_employee_draft_timesheet      PASSED
tests/test_timesheet.py::test_employee_multi_draft_timesheet PASSED
tests/test_timesheet.py::test_employee_submit_timesheet     PASSED
tests/test_timesheet.py::test_manager_approves_timesheet    SKIPPED

8 collected: 7 passed, 1 skipped ← clean run
```

---

## 9. Open Items (from canvas, status as of 2026-08-11)

| # | Item | Priority | Status |
|---|---|---|---|
| 1 | `auto_fill()` implementation uses `submit-btn enabled` as proxy instead of toast text | Medium | ✅ Resolved by design — avoids brittle toast matching |
| 2 | TC-TS-01 / TC-TS-03 conflict: one active timesheet per period | Medium | ⚠️ Open — observe on first combined run |
| 3 | Post-submission list navigation timing (router.push flakiness) | Low | ✅ Mitigated — `wait_for_url()` used instead of toast |
| 4 | Session TTL in CI (55-min limit) | Low | ✅ Handled in conftest.py TTL check |
| 5 | TC-TS-04 manager approval re-enable | Future | 🔒 Guarded — needs dedicated test env |

---

## 10. Things to Discuss / Potential Improvements

1. **TC-TS-01 vs TC-TS-03 test isolation**: These two tests operate on the same employee account and may collide on the same timesheet period. Consider whether they should be sequenced (use `pytest-ordering`) or whether the app behavior when an active draft already exists needs to be verified.

2. **`save_as_draft()` wait strategy**: Currently uses `wait_for_url("**/timesheets")`. The canvas notes this relies on `router.push("/timesheets")` firing server-side. If the app ever changes to in-place navigation (SPA update without URL change), this assertion would silently pass incorrectly. A secondary `expect_timesheet_in_list("draft")` after navigate is the safety net — which is correctly in place.

3. **Leave page migration**: `employee_leave_page.py` still uses `get_by_role()` and `get_by_placeholder()` — not compliant with the data-testid strategy. Out of scope currently but worth flagging if leave tests are ever re-enabled.

4. **Reporter auth model**: Currently uses OAuth2 user credentials (interactive `run_local_server` if `token.json` is missing). In CI, this would block. A **service account** key approach would be more CI-friendly.

5. **No `conftest.py` fixture for bare `page`**: `test_raw_login_and_logout_flow` uses pytest-playwright's default `page` fixture directly. This means it uses whatever `base_url` is configured in `pytest.ini` but does NOT get the env-overridden base_url set by `pytest_configure`. Verify this works correctly if `E2E_BASE_URL` is set.

---

*Document created: 2026-08-11 | Author: Antigravity (analysis) | Based on: 20260811_testing_canvas.md*
