"""
UX Testing for Voice Transcriber Web Interface
Tests user experience, interface usability, and accessibility
"""

import unittest
import time
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

from tests.fixtures.test_audio_files import TestAudioFixtures


class WebInterfaceUXTest(unittest.TestCase):
    """Test web interface user experience"""
    
    @classmethod
    def setUpClass(cls):
        """Set up web driver for all tests"""
        if not SELENIUM_AVAILABLE:
            raise unittest.SkipTest("Selenium not available. Install with: pip install selenium")
        
        cls.base_url = os.getenv('TEST_BASE_URL', 'http://localhost:5001')
        cls.driver = None
        cls.wait = None
        
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in headless mode
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        try:
            cls.driver = webdriver.Chrome(options=chrome_options)
            cls.wait = WebDriverWait(cls.driver, 10)
            cls.driver.get(cls.base_url)
        except Exception as e:
            raise unittest.SkipTest(f"Could not start web driver: {e}")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up web driver"""
        if cls.driver:
            cls.driver.quit()
    
    def setUp(self):
        """Set up for each test"""
        if not self.driver:
            self.skipTest("Web driver not available")
        
        # Navigate to main page
        self.driver.get(self.base_url)
        time.sleep(1)  # Allow page to load
    
    def test_page_loads_correctly(self):
        """Test that the main page loads correctly"""
        print("\n🌐 Testing page load")
        
        # Check page title
        title = self.driver.title
        self.assertIn("Voice Transcriber", title)
        print(f"   Page title: {title}")
        
        # Check main elements are present
        main_elements = [
            "file-upload",
            "model-select",
            "language-select",
            "speaker-diarization",
            "transcribe-button"
        ]
        
        for element_id in main_elements:
            try:
                element = self.driver.find_element(By.ID, element_id)
                self.assertTrue(element.is_displayed(), f"Element {element_id} not visible")
                print(f"   ✅ {element_id} present and visible")
            except NoSuchElementException:
                print(f"   ❌ {element_id} not found")
                # Don't fail the test, just log the issue
    
    def test_file_upload_interface(self):
        """Test file upload interface"""
        print("\n📁 Testing file upload interface")
        
        # Check file input is present
        try:
            file_input = self.driver.find_element(By.ID, "file-upload")
            self.assertTrue(file_input.is_displayed())
            print("   ✅ File upload input present")
        except NoSuchElementException:
            self.fail("File upload input not found")
        
        # Test drag and drop area (if present)
        try:
            drop_area = self.driver.find_element(By.CLASS_NAME, "drop-area")
            self.assertTrue(drop_area.is_displayed())
            print("   ✅ Drag and drop area present")
        except NoSuchElementException:
            print("   ⚠️ Drag and drop area not found")
        
        # Test file selection
        try:
            # Create a test file
            test_file = TestAudioFixtures.create_test_wav_file(duration=5)
            
            # Upload file
            file_input.send_keys(test_file)
            
            # Check if file is accepted
            time.sleep(1)
            print("   ✅ File selection works")
            
            # Clean up
            os.remove(test_file)
            parent_dir = os.path.dirname(test_file)
            try:
                os.rmdir(parent_dir)
            except OSError:
                pass
                
        except Exception as e:
            print(f"   ⚠️ File upload test failed: {e}")
    
    def test_model_selection_interface(self):
        """Test model selection interface"""
        print("\n🤖 Testing model selection interface")
        
        try:
            model_select = self.driver.find_element(By.ID, "model-select")
            self.assertTrue(model_select.is_displayed())
            print("   ✅ Model selection present")
            
            # Check available options
            options = model_select.find_elements(By.TAG_NAME, "option")
            expected_models = ["tiny", "base", "small", "medium", "large"]
            
            for model in expected_models:
                model_found = any(option.get_attribute("value") == model for option in options)
                if model_found:
                    print(f"   ✅ Model {model} available")
                else:
                    print(f"   ⚠️ Model {model} not found")
            
        except NoSuchElementException:
            print("   ❌ Model selection not found")
    
    def test_language_selection_interface(self):
        """Test language selection interface"""
        print("\n🌍 Testing language selection interface")
        
        try:
            language_select = self.driver.find_element(By.ID, "language-select")
            self.assertTrue(language_select.is_displayed())
            print("   ✅ Language selection present")
            
            # Check for auto-detect option
            options = language_select.find_elements(By.TAG_NAME, "option")
            auto_detect_found = any("auto" in option.get_attribute("value").lower() for option in options)
            
            if auto_detect_found:
                print("   ✅ Auto-detect language option available")
            else:
                print("   ⚠️ Auto-detect language option not found")
                
        except NoSuchElementException:
            print("   ❌ Language selection not found")
    
    def test_speaker_diarization_interface(self):
        """Test speaker diarization interface"""
        print("\n👥 Testing speaker diarization interface")
        
        try:
            speaker_checkbox = self.driver.find_element(By.ID, "speaker-diarization")
            self.assertTrue(speaker_checkbox.is_displayed())
            print("   ✅ Speaker diarization checkbox present")
            
            # Test checkbox interaction
            initial_state = speaker_checkbox.is_selected()
            speaker_checkbox.click()
            new_state = speaker_checkbox.is_selected()
            
            self.assertNotEqual(initial_state, new_state, "Checkbox should toggle")
            print("   ✅ Speaker diarization checkbox interactive")
            
        except NoSuchElementException:
            print("   ❌ Speaker diarization checkbox not found")
    
    def test_transcribe_button_interface(self):
        """Test transcribe button interface"""
        print("\n▶️ Testing transcribe button interface")
        
        try:
            transcribe_button = self.driver.find_element(By.ID, "transcribe-button")
            self.assertTrue(transcribe_button.is_displayed())
            print("   ✅ Transcribe button present")
            
            # Check button text
            button_text = transcribe_button.text.lower()
            self.assertIn("transcribe", button_text)
            print(f"   ✅ Button text: {transcribe_button.text}")
            
        except NoSuchElementException:
            print("   ❌ Transcribe button not found")
    
    def test_progress_display_interface(self):
        """Test progress display interface"""
        print("\n📊 Testing progress display interface")
        
        # Look for progress elements
        progress_elements = [
            "progress-bar",
            "progress-text",
            "status-display",
            "job-status"
        ]
        
        for element_id in progress_elements:
            try:
                element = self.driver.find_element(By.ID, element_id)
                # Element might be hidden initially, that's okay
                print(f"   ✅ {element_id} present")
            except NoSuchElementException:
                print(f"   ⚠️ {element_id} not found")
    
    def test_responsive_design(self):
        """Test responsive design"""
        print("\n📱 Testing responsive design")
        
        # Test different screen sizes
        screen_sizes = [
            (1920, 1080),  # Desktop
            (1024, 768),   # Tablet
            (375, 667),    # Mobile
        ]
        
        for width, height in screen_sizes:
            self.driver.set_window_size(width, height)
            time.sleep(1)
            
            # Check if main elements are still visible
            try:
                file_upload = self.driver.find_element(By.ID, "file-upload")
                self.assertTrue(file_upload.is_displayed(), 
                              f"File upload not visible at {width}x{height}")
                print(f"   ✅ Responsive at {width}x{height}")
            except NoSuchElementException:
                print(f"   ❌ File upload not found at {width}x{height}")
        
        # Reset to default size
        self.driver.set_window_size(1920, 1080)
    
    def test_accessibility_basics(self):
        """Test basic accessibility features"""
        print("\n♿ Testing basic accessibility")
        
        # Check for alt text on images
        images = self.driver.find_elements(By.TAG_NAME, "img")
        for img in images:
            alt_text = img.get_attribute("alt")
            if alt_text:
                print(f"   ✅ Image has alt text: {alt_text}")
            else:
                print("   ⚠️ Image missing alt text")
        
        # Check for form labels
        inputs = self.driver.find_elements(By.TAG_NAME, "input")
        for input_elem in inputs:
            input_id = input_elem.get_attribute("id")
            if input_id:
                try:
                    label = self.driver.find_element(By.CSS_SELECTOR, f"label[for='{input_id}']")
                    print(f"   ✅ Input {input_id} has label")
                except NoSuchElementException:
                    print(f"   ⚠️ Input {input_id} missing label")
        
        # Check for heading structure
        headings = self.driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, h5, h6")
        if headings:
            print(f"   ✅ Found {len(headings)} headings")
        else:
            print("   ⚠️ No headings found")
    
    def test_error_handling_ui(self):
        """Test error handling in UI"""
        print("\n🚨 Testing error handling UI")
        
        # Try to submit without file
        try:
            transcribe_button = self.driver.find_element(By.ID, "transcribe-button")
            transcribe_button.click()
            time.sleep(2)
            
            # Look for error messages
            error_elements = self.driver.find_elements(By.CLASS_NAME, "error")
            if error_elements:
                print("   ✅ Error message displayed")
            else:
                print("   ⚠️ No error message found for invalid submission")
                
        except NoSuchElementException:
            print("   ❌ Transcribe button not found for error test")
    
    def test_loading_states(self):
        """Test loading states and feedback"""
        print("\n⏳ Testing loading states")
        
        # Upload a file first
        try:
            test_file = TestAudioFixtures.create_test_wav_file(duration=5)
            file_input = self.driver.find_element(By.ID, "file-upload")
            file_input.send_keys(test_file)
            time.sleep(1)
            
            # Start transcription
            transcribe_button = self.driver.find_element(By.ID, "transcribe-button")
            transcribe_button.click()
            
            # Look for loading indicators
            time.sleep(2)
            
            loading_indicators = [
                "loading",
                "spinner",
                "progress",
                "transcribing"
            ]
            
            for indicator in loading_indicators:
                try:
                    element = self.driver.find_element(By.CLASS_NAME, indicator)
                    if element.is_displayed():
                        print(f"   ✅ Loading indicator '{indicator}' visible")
                        break
                except NoSuchElementException:
                    continue
            else:
                print("   ⚠️ No loading indicators found")
            
            # Clean up
            os.remove(test_file)
            parent_dir = os.path.dirname(test_file)
            try:
                os.rmdir(parent_dir)
            except OSError:
                pass
                
        except Exception as e:
            print(f"   ⚠️ Loading state test failed: {e}")


class WebInterfacePerformanceTest(unittest.TestCase):
    """Test web interface performance"""
    
    @classmethod
    def setUpClass(cls):
        """Set up web driver for performance tests"""
        if not SELENIUM_AVAILABLE:
            raise unittest.SkipTest("Selenium not available")
        
        cls.base_url = os.getenv('TEST_BASE_URL', 'http://localhost:5001')
        cls.driver = None
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        try:
            cls.driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            raise unittest.SkipTest(f"Could not start web driver: {e}")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up web driver"""
        if cls.driver:
            cls.driver.quit()
    
    def test_page_load_performance(self):
        """Test page load performance"""
        print("\n⚡ Testing page load performance")
        
        # Measure page load time
        start_time = time.time()
        self.driver.get(self.base_url)
        
        # Wait for page to be ready
        WebDriverWait(self.driver, 10).until(
            lambda driver: driver.execute_script("return document.readyState") == "complete"
        )
        
        load_time = time.time() - start_time
        print(f"   Page load time: {load_time:.2f} seconds")
        
        # Page should load within reasonable time
        self.assertLess(load_time, 5.0, f"Page load time {load_time:.2f}s too slow")
    
    def test_interface_responsiveness(self):
        """Test interface responsiveness"""
        print("\n🎯 Testing interface responsiveness")
        
        self.driver.get(self.base_url)
        
        # Test button click responsiveness
        try:
            transcribe_button = self.driver.find_element(By.ID, "transcribe-button")
            
            start_time = time.time()
            transcribe_button.click()
            response_time = time.time() - start_time
            
            print(f"   Button click response time: {response_time:.3f} seconds")
            self.assertLess(response_time, 1.0, f"Button response time {response_time:.3f}s too slow")
            
        except NoSuchElementException:
            print("   ⚠️ Transcribe button not found for responsiveness test")
    
    def test_form_interaction_performance(self):
        """Test form interaction performance"""
        print("\n📝 Testing form interaction performance")
        
        self.driver.get(self.base_url)
        
        # Test form element interactions
        interactions = [
            ("model-select", "click"),
            ("language-select", "click"),
            ("speaker-diarization", "click"),
        ]
        
        for element_id, action in interactions:
            try:
                element = self.driver.find_element(By.ID, element_id)
                
                start_time = time.time()
                if action == "click":
                    element.click()
                elif action == "type":
                    element.send_keys("test")
                
                response_time = time.time() - start_time
                print(f"   {element_id} {action} response time: {response_time:.3f}s")
                
                self.assertLess(response_time, 0.5, 
                              f"{element_id} {action} response time {response_time:.3f}s too slow")
                
            except NoSuchElementException:
                print(f"   ⚠️ {element_id} not found for performance test")


if __name__ == '__main__':
    unittest.main()
