from playwright.sync_api import Page, expect

class BasePage:
    def __init__(self, page: Page):
        self.page = page

    def dismiss_welcome_dialog_if_present(self):
        """Helper to dismiss the welcome dialog if it appears on first login."""
        get_started = self.page.get_by_test_id("get-started-btn")
        try:
            if get_started.is_visible(timeout=2000):
                get_started.click()
                expect(get_started).not_to_be_visible(timeout=3000)
        except Exception:
            pass # Timeout means it didn't appear, which is fine
