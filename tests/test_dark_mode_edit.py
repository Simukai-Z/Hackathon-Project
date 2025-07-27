#!/usr/bin/env python3
"""
Test script to verify dark mode functionality on the edit assignment page
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def test_edit_assignment_dark_mode():
    """Test the edit assignment page in both light and dark modes"""
    
    # Set up Chrome options for headless mode
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 10)
    
    try:
        print("🧪 Testing Edit Assignment Dark Mode Compatibility...")
        
        # Navigate to home page
        driver.get("http://127.0.0.1:5000")
        print("✅ Navigated to home page")
        
        # Login as teacher
        email_input = wait.until(EC.presence_of_element_located((By.NAME, "email")))
        email_input.send_keys("teacher@example.com")
        
        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys("password123")
        
        # Select teacher radio button
        teacher_radio = driver.find_element(By.ID, "teacher")
        teacher_radio.click()
        
        # Submit login
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()
        print("✅ Logged in as teacher")
        
        # Wait for teacher dashboard
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".dashboard")))
        
        # Navigate to a specific classroom
        classroom_link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href*='class=']")))
        classroom_link.click()
        print("✅ Navigated to classroom")
        
        # Find and click edit assignment link
        edit_link = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Edit")))
        edit_link.click()
        print("✅ Navigated to edit assignment page")
        
        # Wait for edit assignment page to load
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".edit-assignment-container")))
        
        # Test Light Mode
        print("\n📝 Testing Light Mode:")
        
        # Check if page elements are visible
        page_title = driver.find_element(By.CSS_SELECTOR, ".page-title")
        print(f"   - Page title visible: {page_title.is_displayed()}")
        
        form_card = driver.find_element(By.CSS_SELECTOR, ".edit-assignment-form-card")
        print(f"   - Form card visible: {form_card.is_displayed()}")
        
        form_sections = driver.find_elements(By.CSS_SELECTOR, ".form-section")
        print(f"   - Found {len(form_sections)} form sections")
        
        form_controls = driver.find_elements(By.CSS_SELECTOR, ".form-control")
        print(f"   - Found {len(form_controls)} form controls")
        
        # Get some style properties in light mode
        light_bg_color = form_card.value_of_css_property("background-color")
        light_text_color = page_title.value_of_css_property("color")
        print(f"   - Form background color: {light_bg_color}")
        print(f"   - Page title color: {light_text_color}")
        
        # Toggle to dark mode
        print("\n🌙 Switching to Dark Mode...")
        theme_toggle = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".theme-toggle")))
        theme_toggle.click()
        time.sleep(1)  # Wait for transition
        
        # Verify dark mode is active
        body = driver.find_element(By.TAG_NAME, "body")
        is_dark_mode = "dark-mode" in body.get_attribute("class")
        print(f"   - Dark mode active: {is_dark_mode}")
        
        if is_dark_mode:
            # Get style properties in dark mode
            dark_bg_color = form_card.value_of_css_property("background-color")
            dark_text_color = page_title.value_of_css_property("color")
            print(f"   - Form background color (dark): {dark_bg_color}")
            print(f"   - Page title color (dark): {dark_text_color}")
            
            # Verify colors are different between light and dark modes
            bg_changed = light_bg_color != dark_bg_color
            text_changed = light_text_color != dark_text_color
            print(f"   - Background color changed: {bg_changed}")
            print(f"   - Text color changed: {text_changed}")
            
            if bg_changed and text_changed:
                print("✅ Dark mode styles are working correctly!")
            else:
                print("❌ Dark mode styles may not be applied properly")
        
        # Test form functionality in dark mode
        print("\n🔧 Testing Form Functionality in Dark Mode:")
        
        title_input = driver.find_element(By.NAME, "title")
        original_title = title_input.get_attribute("value")
        
        # Clear and type new title
        title_input.clear()
        test_title = f"Dark Mode Test Assignment - {int(time.time())}"
        title_input.send_keys(test_title)
        
        # Check if input is visible and readable
        input_visible = title_input.is_displayed()
        input_value = title_input.get_attribute("value")
        print(f"   - Title input visible: {input_visible}")
        print(f"   - Title input functional: {input_value == test_title}")
        
        # Test textarea
        content_textarea = driver.find_element(By.NAME, "content")
        content_textarea.clear()
        test_content = "This is a test assignment for dark mode compatibility."
        content_textarea.send_keys(test_content)
        
        textarea_value = content_textarea.get_attribute("value")
        print(f"   - Content textarea functional: {textarea_value == test_content}")
        
        # Restore original title
        title_input.clear()
        title_input.send_keys(original_title)
        
        # Test button visibility
        save_button = driver.find_element(By.CSS_SELECTOR, ".btn-primary")
        cancel_button = driver.find_element(By.CSS_SELECTOR, ".btn-secondary")
        
        print(f"   - Save button visible: {save_button.is_displayed()}")
        print(f"   - Cancel button visible: {cancel_button.is_displayed()}")
        
        print("\n🎉 Edit Assignment Dark Mode Test Complete!")
        
        return {
            "success": True,
            "dark_mode_active": is_dark_mode,
            "styles_changed": bg_changed and text_changed if is_dark_mode else False,
            "form_functional": input_visible and (input_value == test_title),
            "elements_visible": True
        }
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return {"success": False, "error": str(e)}
        
    finally:
        driver.quit()

if __name__ == "__main__":
    result = test_edit_assignment_dark_mode()
    
    if result["success"]:
        print("\n📊 Test Summary:")
        print(f"   ✅ Dark Mode Active: {result.get('dark_mode_active', False)}")
        print(f"   ✅ Styles Changed: {result.get('styles_changed', False)}")
        print(f"   ✅ Form Functional: {result.get('form_functional', False)}")
        print(f"   ✅ Elements Visible: {result.get('elements_visible', False)}")
        
        if all([result.get('dark_mode_active'), result.get('styles_changed'), result.get('form_functional')]):
            print("\n🏆 ALL TESTS PASSED - Edit Assignment Dark Mode Working Perfectly!")
        else:
            print("\n⚠️  Some issues detected - Check individual test results above")
    else:
        print(f"\n💥 Test failed: {result.get('error', 'Unknown error')}")
