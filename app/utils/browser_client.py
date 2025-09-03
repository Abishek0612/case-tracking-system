from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging
from typing import List, Dict
import time


class BrowserClient:
    def __init__(self):
        self.driver = None
        
    def initialize(self):
        if self.driver:
            return
            
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        logging.info("Browser client initialized")
        
    def get_states(self) -> List[Dict]:
        self.initialize()
        
        logging.info("Navigating to e-jagriti portal...")
        
        try:
            self.driver.get("https://e-jagriti.gov.in/advance-case-search")
            
            wait = WebDriverWait(self.driver, 60)
            
            logging.info("Waiting for dynamic content to load...")
            
            # Wait for the page to be in a ready state
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            
            # Wait for any loading indicators to disappear
            time.sleep(5)
            
            # Try waiting for common loading patterns
            possible_loading_selectors = [
                ".loading", ".spinner", "#loading", "[data-loading]", 
                ".loader", "#loader", ".progress"
            ]
            
            for selector in possible_loading_selectors:
                try:
                    WebDriverWait(self.driver, 3).until_not(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    logging.info(f"Waited for loading element to disappear: {selector}")
                except TimeoutException:
                    pass
            
            # Wait longer for dynamic content
            logging.info("Waiting additional time for JavaScript to render forms...")
            time.sleep(15)
            
            # Execute JavaScript to check for form elements
            select_count = self.driver.execute_script("return document.querySelectorAll('select').length")
            logging.info(f"JavaScript reports {select_count} select elements")
            
            if select_count == 0:
                # Try triggering any onclick events or form initialization
                logging.info("Attempting to trigger form initialization...")
                
                # Click on common elements that might trigger form loading
                clickable_selectors = [
                    "button", "a[href*='search']", "[onclick]", ".btn", 
                    ".button", "[data-toggle]", "[data-target]"
                ]
                
                for selector in clickable_selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements[:3]:  # Try first 3 elements
                            try:
                                if element.is_displayed() and element.is_enabled():
                                    self.driver.execute_script("arguments[0].click();", element)
                                    time.sleep(2)
                                    new_count = self.driver.execute_script("return document.querySelectorAll('select').length")
                                    if new_count > 0:
                                        logging.info(f"Form elements appeared after clicking element")
                                        break
                            except:
                                continue
                        if new_count > 0:
                            break
                    except:
                        continue
            
            # Final check for select elements
            time.sleep(5)
            select_elements = self.driver.find_elements(By.TAG_NAME, "select")
            
            if not select_elements:
                # Try alternative approach - look for React/Vue components
                logging.info("Looking for alternative form patterns...")
                
                # Check for input elements that might be custom dropdowns
                input_elements = self.driver.find_elements(By.CSS_SELECTOR, "input, div[role='combobox'], div[role='listbox']")
                logging.info(f"Found {len(input_elements)} potential form inputs")
                
                # Look for dropdown indicators in the page
                dropdown_indicators = self.driver.find_elements(By.CSS_SELECTOR, "[class*='dropdown'], [class*='select'], [data-value]")
                logging.info(f"Found {len(dropdown_indicators)} dropdown-like elements")
                
                if not dropdown_indicators:
                    # Save current state for debugging
                    current_source = self.driver.page_source
                    with open("debug_final_source.html", "w", encoding="utf-8") as f:
                        f.write(current_source)
                    
                    # Try visiting the main portal first
                    logging.info("Trying alternative navigation through main portal...")
                    self.driver.get("https://e-jagriti.gov.in")
                    time.sleep(10)
                    
                    # Look for advance search link
                    links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='search'], a[href*='advance']")
                    for link in links:
                        if 'search' in link.get_attribute('href').lower():
                            link.click()
                            time.sleep(10)
                            break
                    
                    # Check again for select elements
                    select_elements = self.driver.find_elements(By.TAG_NAME, "select")
            
            if not select_elements:
                raise Exception("No form elements found after all attempts - portal may require authentication or have anti-bot measures")
            
            logging.info(f"Found {len(select_elements)} select elements")
            
            # Find the state dropdown
            state_dropdown = None
            for select in select_elements:
                try:
                    options = Select(select).options
                    if len(options) > 10:  # Likely the state dropdown
                        # Check if options look like states
                        option_texts = [opt.text.lower() for opt in options[:10]]
                        if any('state' in txt or len(txt.split()) <= 3 for txt in option_texts):
                            state_dropdown = select
                            break
                except:
                    continue
            
            if not state_dropdown:
                state_dropdown = select_elements[0]  # Use first select as fallback
            
            # Extract states
            select_obj = Select(state_dropdown)
            options = select_obj.options
            
            states = []
            for option in options:
                value = option.get_attribute("value")
                text = option.text.strip()
                
                if value and value != "" and text and text.lower() not in ['select', 'choose', '--']:
                    states.append({
                        "id": value,
                        "name": text.upper(),
                        "display_name": text
                    })
            
            logging.info(f"Successfully extracted {len(states)} states")
            return states
            
        except Exception as e:
            logging.error(f"Failed to get states: {e}")
            self.driver.save_screenshot("final_debug_screenshot.png")
            raise
    
    def get_commissions(self, state_id: str) -> List[Dict]:
        return []  # Implement after states work
    
    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None