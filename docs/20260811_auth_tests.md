# Auth Tests — Focused Analysis
**Date**: 2026-08-11
**Scope**: `tests/test_auth.py`, `pages/login_page.py`, `pages/dashboard_page.py`, `pages/base_page.py`
**App Under Test**: `src/app/(auth)/login/LoginForm.tsx`, `src/components/layout/SidebarUserMenu.tsx`

---

## 1. How Auth Session Setup Works

> **You do NOT run auth tests first.** Auth state is built automatically on first use.

The `admin_state`, `employee_state`, and `manager_state` fixtures are `scope=session`. They trigger the first time any test requests `admin_page`, `employee_page`, or `manager_page` — regardless of whether `test_auth.py` was collected at all.

```
pytest tests/test_timesheet.py          # test_auth.py never runs
  +-- employee_page fixture requested
        +-- employee_state fixture fires (scope=session, first use)
              +-- login happens silently in the background
```

`test_auth.py` tests are specifically for **verifying the auth mechanism**, not for seeding it.

---

## 2. data-testid Verification — All Auth IDs

Every selector used in the auth flow was traced to its source file. All IDs are confirmed present.

| data-testid | Used In | Source File | Line | Status |
|---|---|---|---|---|
| `sign-in-heading` | `test_auth.py` (post-logout assert) | `LoginForm.tsx` | 154 | ? Confirmed |
| `sign-in-with-password-btn` | `LoginPage.login()` | `LoginForm.tsx` | 208 | ? Confirmed |
| `email-input` | `LoginPage.login()` | `LoginForm.tsx` | 250 | ? Confirmed |
| `password-input` | `LoginPage.login()` | `LoginForm.tsx` | 277 | ? Confirmed |
| `sign-in-btn` | `LoginPage.login()` | `LoginForm.tsx` | 304 | ? Confirmed |
| `user-menu-btn` | `DashboardPage.verify_is_loaded()`, `logout()` | `SidebarUserMenu.tsx` | 244 | ? Confirmed |
| `logout-menu-item` | `DashboardPage.logout()` | `SidebarUserMenu.tsx` | 282 | ? Confirmed |
| `get-started-btn` | `BasePage.dismiss_welcome_dialog_if_present()` | `onboarding-provider.tsx` | 71 | ? Confirmed |

**No missing or stale IDs in the active auth flows.**

---

## 3. Login Page Behaviour — Important Detail

The login page has two rendering modes controlled by `googleEnabled` (a workspace config flag):

```
googleEnabled = true  ?  Shows Google button + "Sign in with password" toggle
googleEnabled = false ?  Shows password form directly
```

`LoginPage.login()` correctly handles both:
```python
# Tries to find sign-in-with-password-btn (2s timeout)
# If it appears ? click it to reveal the password form
# If it doesn't appear ? password form is already visible
# Then fills email-input, password-input, clicks sign-in-btn
```

The `sign-in-with-password-btn` only renders when `googleEnabled && !showPasswordLogin`. This conditional is correctly handled with a try/except in the page object — no change needed.

---

## 4. Current Auth Tests — Flow Completeness

### TC-AUTH-01 `test_raw_login_and_logout_flow` ? Complete
**Persona**: Employee (raw credentials, no pre-auth)
**Steps covered**:
1. `goto("/login")` — page loads
2. Handle Google toggle if present (`sign-in-with-password-btn`)
3. Fill `email-input`, `password-input`, click `sign-in-btn`
4. Assert redirect to `/dashboard` (URL check in `LoginPage.login()`)
5. Assert `user-menu-btn` visible (`DashboardPage.verify_is_loaded()`)
6. Click `user-menu-btn` ? click `logout-menu-item`
7. Assert URL matches `r".*/login"` + `sign-in-heading` visible

**Assessment**: Steps match the real user flow end-to-end. No gaps.

---

### TC-AUTH-02 `test_admin_pre_authenticated` ? Complete
### TC-AUTH-03 `test_employee_pre_authenticated` ? Complete
### TC-AUTH-04 `test_manager_pre_authenticated` ? Complete

**Steps covered** (identical for all three):
1. Fixture injects stored auth state (storage_state from `.auth/*.json`)
2. `goto("/dashboard")` — no login redirect occurs
3. Assert URL matches `r".*/dashboard"` + `user-menu-btn` visible

**Assessment**: These are session-validity smoke tests. They confirm that the session fixture works and that the app does not redirect an authenticated user back to login. Complete as designed.

---

## 5. Flow Gaps — What is Missing

The following auth-adjacent flows exist in the app but are **not covered** by any test:

### GAP-AUTH-A: Wrong password / invalid credentials ?? Missing
- **What the app does**: Displays an error message in the `authError` state — rendered as a styled div with `AlertCircle` icon (no `data-testid` on the error div currently).
- **User impact**: Core negative path for login; a regression here would go undetected.
- **Blocker**: The auth error `<div>` has **no `data-testid`**. To test this properly, a `data-testid="auth-error-msg"` is needed on the error container in `LoginForm.tsx`.
- **Suggested test**: `test_login_with_wrong_password` — fill wrong password, click sign-in, assert error div visible.

### GAP-AUTH-B: Unauthenticated access redirects to login ?? Missing
- **What the app does**: `middleware.ts` calls `updateSession()` (Supabase session refresher). Protected routes redirect unauthenticated users to `/login`.
- **User impact**: A misconfigured middleware would break the entire auth gate.
- **Suggested test**: `test_unauthenticated_redirect` — bare `page` fixture, `goto("/dashboard")`, assert URL is `/login`.
- **Blocker**: None. No new `data-testid` needed — URL assertion is sufficient.

### GAP-AUTH-C: Session persistence across page refresh ?? Low priority
- **What**: After login, reload the page — user should still be authenticated.
- **Suggested test**: `test_session_persists_on_reload` — use `employee_page`, `goto("/dashboard")`, `page.reload()`, assert still on `/dashboard`.
- **Blocker**: None.

---

## 6. Suggested New Tests (Prioritised)

| ID | Test Name | Priority | New IDs Needed |
|---|---|---|---|
| GAP-AUTH-B | `test_unauthenticated_redirect` | **High** — core security gate | None |
| GAP-AUTH-A | `test_login_with_wrong_password` | Medium | `auth-error-msg` on `LoginForm.tsx` error div |
| GAP-AUTH-C | `test_session_persists_on_reload` | Low | None |

---

## 7. Pages Outside Current Scope (Intentionally Not Tested)

| Route | Notes |
|---|---|
| `/forgot-password` | No `data-testid` on any element. Email field has no testid. Would require IDs before testing. |
| `/reset-password` | Requires email link click — not feasible in E2E without email inbox integration. |
| `/register` | Not applicable — users are invited, not self-registered. |
| `/activate` | Same as reset-password; requires email link. |

---

## 8. Summary

| Item | Status |
|---|---|
| All 4 current auth tests data-testid compliant | ? Yes |
| All IDs confirmed present in frontend source | ? Yes |
| Login page Google-toggle handling correct | ? Yes |
| Auth session auto-setup (no auth-first requirement) | ? Correct |
| Negative path (wrong password) covered | ? Gap — needs `auth-error-msg` testid |
| Unauthenticated redirect covered | ? Gap — no new ID needed |
| Session persistence on reload covered | ? Gap (low priority) |

---

*Document created: 2026-08-11*
