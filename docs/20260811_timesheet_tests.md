# Timesheet Tests � Focused Analysis
**Date**: 2026-08-11
**Scope**: `tests/test_timesheet.py`, `pages/timesheet_page.py`, `pages/manager_approval_page.py`
**App Under Test**: `TimesheetGrid.tsx`, `TimesheetList.tsx`, `timesheets/page.tsx`, `timesheets/[id]/page.tsx`

---

## 1. Actual Frontend User Flow (Source of Truth)

Understanding the real navigation chain is critical before validating tests:

```
/timesheets                     ? List page (page.tsx)
  "New Timesheet" btn click
    ? router navigates to /timesheets/new
        ? [id]/page.tsx with id="new"
            ? renders TimesheetGrid.tsx (writable mode)
                ? user opens a day cell (Sheet drawer)
                ? adds project, fills hours + description
                ? clicks Done ? drawer closes
                ? save-draft-btn OR auto-fill + submit-timesheet-btn
                ? on success: router.push("/timesheets")
  Row click in list
    ? router.push("/timesheets/{id}")  (TimesheetList.tsx:247)
        ? [id]/page.tsx with real id
            ? renders TimesheetGrid.tsx (read-only if approved/submitted)
```

The grid lives at `/timesheets/new` or `/timesheets/{id}` � it is **not** rendered inline on the list page.
`start_new_timesheet()` clicking `new-timesheet-btn` triggers a Next.js Link navigation, NOT an in-page DOM change.

---

## 2. data-testid Verification � All Timesheet IDs

All selectors used in timesheet tests were traced to their exact source.

| data-testid | Pattern | Used In | Source File | Line | Status |
|---|---|---|---|---|---|
| `new-timesheet-btn` | static | `TimesheetPage.navigate()`, `start_new_timesheet()` | `timesheets/page.tsx` | 59 | ? Confirmed |
| `add-time-{yyyy-MM-dd}` | dynamic (date suffix) | `open_available_day_by_index()` | `TimesheetGrid.tsx` | 1956 | ? Confirmed |
| `add-project-{slot.id}` | dynamic (UUID suffix) | `add_project_by_index()` | `TimesheetGrid.tsx` | 2193 | ? Confirmed |
| `hour-input-{slot.id}` | dynamic (UUID suffix) | `log_hours_and_description()` | `TimesheetGrid.tsx` | 2120 | ? Confirmed |
| `description-input-{slot.id}` | dynamic (UUID suffix) | `log_hours_and_description()` | `TimesheetGrid.tsx` | 2152 | ? Confirmed |
| `done-day-btn` | static | `close_day_drawer()` | `TimesheetGrid.tsx` | 2205 | ? Confirmed |
| `save-draft-btn` | static | `save_as_draft()` | `TimesheetGrid.tsx` | 1559 | ? Confirmed |
| `auto-fill-btn` | static | `auto_fill()` | `TimesheetGrid.tsx` | 1548 | ? Confirmed |
| `submit-timesheet-btn` | static | `auto_fill()` (enabled check), `submit_timesheet()` | `TimesheetGrid.tsx` | 1579 | ? Confirmed |
| `approve-timesheet-btn` | static | `approve_first_pending_timesheet()` | `TimesheetGrid.tsx` | 1531 | ? Confirmed |
| `timesheet-row-{status}` | dynamic (status suffix) | `expect_timesheet_in_list()`, `open_first_draft_from_list()` | `TimesheetList.tsx` | 198 | ? Confirmed |
| `nav-link-timesheets` | static (generated) | `navigate_from_dashboard()` | `Sidebar.tsx` | 780 | ? Confirmed |

**No missing or stale IDs. All selectors are confirmed present in the frontend.**

---

## 3. ID Naming Quality Assessment

| ID | Assessment |
|---|---|
| `new-timesheet-btn` | ? Clear, consistent with button convention |
| `add-time-{date}` | ? Semantically correct � `add-time` maps to "Add time" label. Date suffix is ISO format (unambiguous) |
| `add-project-{slot.id}` | ? UUID suffix is unique per slot � correct for dynamic lists |
| `hour-input-{slot.id}` | ? Clear. Same UUID suffix as add-project � consistent pairing |
| `description-input-{slot.id}` | ? Clear. Consistent with hour-input pairing |
| `done-day-btn` | ?? Minor � "done-day" is slightly ambiguous. `close-day-drawer-btn` would be more self-documenting, but not a blocker |
| `save-draft-btn` | ? Clear action naming |
| `auto-fill-btn` | ? Clear |
| `submit-timesheet-btn` | ? Explicit entity + action |
| `approve-timesheet-btn` | ? Explicit entity + action |
| `timesheet-row-{status}` | ? Status-driven dynamic ID � enables `expect_timesheet_in_list("draft")` to work with any status string. Elegant pattern |
| `nav-link-{route}` | ? Auto-generated from href � consistent across all nav items |

**Overall: IDs are well-named and follow consistent conventions. One minor naming observation on `done-day-btn`.**

---

## 4. Flow Accuracy � Test vs Real User Journey

### TC-TS-NAV `test_nav_to_timesheets_from_dashboard` ? Accurate
- Starts at `/dashboard` ? clicks `nav-link-timesheets` ? asserts URL + `new-timesheet-btn`
- Correctly mirrors how a user would arrive at the list page

### TC-TS-01 `test_employee_draft_timesheet` ? Accurate (with one note)
**Test flow**:
1. `goto("/timesheets")` ? assert `new-timesheet-btn` visible
2. Click `new-timesheet-btn` ? navigates to `/timesheets/new` (Next.js Link)
3. Open day cell (`add-time-*`) ? add project (`add-project-*`) ? fill hours + description
4. Click `done-day-btn` ? click `save-draft-btn`
5. `wait_for_url("**/timesheets")` ? assert `timesheet-row-draft` visible

**Assessment**: Accurately reflects the real user journey. `start_new_timesheet()` triggers a full page navigation (Link href="/timesheets/new"), not an in-page state change � Playwright handles this transparently.

**Note on `save_as_draft()` assertion**: Uses `wait_for_url("**/timesheets")` instead of a toast assertion. This is correct � the toast is ephemeral and `router.push("/timesheets")` is the durable success signal from the server action.

### TC-TS-02 `test_employee_multi_draft_timesheet` ? Accurate
- Same pattern as TC-TS-01 but with 2 days � 2 projects
- `open_available_day_by_index(0)` is called again for day 2 � correct because after closing day 1's drawer, the next unlogged day becomes index 0 in the DOM ordering

### TC-TS-03 `test_employee_submit_timesheet` ? Accurate

**Why auto-fill is mandatory before submit** (confirmed in source):
- `TimesheetGrid.tsx:1579`: `disabled={isSubmitting || submitGate.blocked}`
- `submitGate.blocked` = true when any working day up to today has zero/underfilled hours
- Auto-fill resolves this by copying the seeded project split to all empty days

**`auto_fill()` assertion strategy**: Instead of matching the toast text (which varies based on whether a seed project exists), the method waits for `submit-timesheet-btn` to become **enabled** � a durable, deterministic signal that `submitGate.blocked` became false.

**`submit_timesheet()` assertion**: Uses `wait_for_url("**/timesheets")` � driven by `router.push("/timesheets")` in `TimesheetGrid.tsx:1008` after a successful submit PATCH.

### TC-TS-04 `test_manager_approves_timesheet` ?? Guarded (Correct)
- Permanently skip-guarded � manager approval via `approve-timesheet-btn` triggers `handleAction("approved")` which is irreversible in the current environment
- Correct design decision for a live shared environment

---

## 5. Critical Observation � `timesheet-row-{status}` is on the Status Cell Only

```tsx
// TimesheetList.tsx:198
<div data-testid={`timesheet-row-${row.original.status}`}>
  <StatusPill ...>
```

The `data-testid` is on the **status cell div**, not the table row (`<tr>`). The row click handler is on the row (`onRowClick={(ts) => router.push(...)}`).

**Impact on tests**: `expect_timesheet_in_list("draft")` correctly asserts the status pill is visible � it works as a list state assertion. `open_first_draft_from_list()` calls `.first.click()` on the status div � this clicks the status cell, not the row, so the `onRowClick` handler may NOT fire. This method exists in the page object but is not used by any active test currently (TC-TS-01/02 navigate back to the list and only assert visibility, they don't click back in). Not a current blocker, but worth noting.

---

## 6. Issues & Recommendations

### ISSUE-TS-01: `timesheet-row-{status}` click may not trigger row navigation ??
- **Problem**: The testid is on a child `<div>` inside the row, not the `<tr>` itself. Row navigation fires via `onRowClick` on the row. Clicking the status cell div may propagate to the row (depending on event bubbling) but is not guaranteed.
- **Risk**: Low today � `open_first_draft_from_list()` is not called by any active test.
- **Recommendation**: Add `data-testid="timesheet-row-link-{id}"` or `data-testid="timesheet-row-{status}-clickable"` to the actual row element in `TimesheetList.tsx` when this method is needed.

### ISSUE-TS-02: TC-TS-01 and TC-TS-03 share the same employee account ??
- **Problem**: Both tests create a new timesheet for the current period. The app may only allow one active (draft/submitted) timesheet per period. If TC-TS-01 creates a draft and TC-TS-03 runs next, `start_new_timesheet()` may open the existing draft rather than creating a new one.
- **Risk**: Medium � depends on app behavior. First observed run will confirm.
- **Recommendation**: Observe on first combined run. If conflict occurs, either add period-cleanup logic or accept that TC-TS-01 and TC-TS-02 leave state that TC-TS-03 builds on.

### ISSUE-TS-03: `done-day-btn` naming is slightly ambiguous (minor)
- **Problem**: `done-day-btn` reads like "done with the day" but technically closes the drawer/sheet panel.
- **Impact**: None functionally � ID works correctly.
- **Recommendation**: Consider `close-day-drawer-btn` in a future refactor for clarity. Not a blocker.

---

## 7. Summary

| Item | Status |
|---|---|
| All timesheet testids confirmed in frontend source | ? Yes |
| ID naming quality | ? Good � one minor observation (done-day-btn) |
| TC-TS-NAV flow (sidebar nav) | ? Accurate |
| TC-TS-01 flow (single draft) | ? Accurate |
| TC-TS-02 flow (multi-day draft) | ? Accurate |
| TC-TS-03 flow (auto-fill + submit) | ? Accurate |
| TC-TS-04 guard (manager approval) | ? Correct � irreversible action |
| `timesheet-row-*` click risk | ?? Potential issue � not blocking any active test |
| TC-TS-01 / TC-TS-03 period conflict risk | ?? Open � observe on first combined run |

### Active test execution order (file order)
```
test_nav_to_timesheets_from_dashboard    TC-TS-NAV  ACTIVE
test_employee_draft_timesheet            TC-TS-01   ACTIVE
test_employee_multi_draft_timesheet      TC-TS-02   ACTIVE
test_employee_submit_timesheet           TC-TS-03   ACTIVE
test_manager_approves_timesheet          TC-TS-04   SKIPPED (guarded)
```

---

*Document created: 2026-08-11*
