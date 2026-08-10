from playwright.sync_api import expect
from pages.base_page import BasePage

class LoginPage(BasePage):
    
    def navigate(self):
        self.page.goto("/login")
        
    def login(self, email: str, password: str):
        self.dismiss_welcome_dialog_if_present()
        
        # If the workspace has Google Auth enabled, the password fields are hidden 
        # behind a "Sign in with password" button. We need to click it if it exists.
        sign_in_with_password_btn = self.page.get_by_test_id("sign-in-with-password-btn")
        try:
            # Wait up to 2 seconds to see if the button appears
            expect(sign_in_with_password_btn).to_be_visible(timeout=2000)
            sign_in_with_password_btn.click()
        except AssertionError:
            pass # Button didn't appear, form must already be visible
            
        self.page.get_by_test_id("email-input").fill(email)
        self.page.get_by_test_id("password-input").fill(password)
        # Click the submit button
        self.page.get_by_test_id("sign-in-btn").click()
        
        # Ensure we land on the dashboard (meaning login succeeded)
        expect(self.page).to_have_url(self.page.url.split("/login")[0] + "/dashboard")
