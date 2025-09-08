import asyncio
import logging
from typing import Dict, List, Optional, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import json
import re
from app.core.config import settings


class JagritiBrowserClient:
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.authenticated = False
        
    async def __aenter__(self):
        await self.start_browser()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_browser()
    
    async def start_browser(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=settings.USE_HEADLESS_BROWSER,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        )
        self.page = await self.context.new_page()
        await self.page.set_default_timeout(settings.BROWSER_TIMEOUT)
        
    async def close_browser(self):
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
    
    async def authenticate(self, mobile: str = None, password: str = None) -> bool:
        try:
            mobile = mobile or settings.JAGRITI_MOBILE
            password = password or settings.JAGRITI_PASSWORD
            
            if not mobile or not password:
                logging.error("Mobile number and password required for authentication")
                return False
            
            logging.info("Navigating to Jagriti portal...")
            await self.page.goto(settings.JAGRITI_BASE_URL)
            
            await self.page.wait_for_timeout(3000)
            
            login_button_selectors = [
                'text="Login"',
                'text="Sign In"',
                'button:has-text("Login")',
                '[data-testid="login-button"]',
                '.login-btn',
                '#loginBtn'
            ]
            
            login_clicked = False
            for selector in login_button_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                    await self.page.click(selector)
                    login_clicked = True
                    logging.info(f"Clicked login button with selector: {selector}")
                    break
                except:
                    continue
            
            if not login_clicked:
                logging.warning("Login button not found, checking if already on login page")
            
            await self.page.wait_for_timeout(2000)
            
            mobile_input_selectors = [
                'input[name="mobile"]',
                'input[placeholder*="mobile"]',
                'input[placeholder*="Mobile"]',
                'input[type="tel"]',
                '#mobileNumber',
                '#mobile'
            ]
            
            mobile_filled = False
            for selector in mobile_input_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                    await self.page.fill(selector, mobile)
                    mobile_filled = True
                    logging.info(f"Filled mobile number with selector: {selector}")
                    break
                except:
                    continue
            
            if not mobile_filled:
                logging.error("Mobile input field not found")
                return False
            
            password_input_selectors = [
                'input[name="password"]',
                'input[type="password"]',
                '#password',
                'input[placeholder*="password"]',
                'input[placeholder*="Password"]'
            ]
            
            password_filled = False
            for selector in password_input_selectors:
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        await self.page.fill(selector, password)
                        password_filled = True
                        logging.info(f"Filled password with selector: {selector}")
                        break
                except:
                    continue
            
            if password_filled:
                submit_selectors = [
                    'button[type="submit"]',
                    'input[type="submit"]',
                    'button:has-text("Login")',
                    'button:has-text("Sign In")',
                    '.submit-btn',
                    '#submitBtn'
                ]
                
                for selector in submit_selectors:
                    try:
                        await self.page.click(selector)
                        logging.info("Clicked submit button")
                        break
                    except:
                        continue
                        
                await self.page.wait_for_timeout(3000)
                
                if await self.check_otp_required():
                    logging.info("OTP verification required - implement OTP handling")
                    return await self.handle_otp()
                
            else:
                otp_selectors = [
                    'button:has-text("Send OTP")',
                    'button:has-text("Get OTP")',
                    '.otp-btn',
                    '#sendOtp'
                ]
                
                for selector in otp_selectors:
                    try:
                        await self.page.click(selector)
                        logging.info("Clicked Send OTP button")
                        return await self.handle_otp()
                    except:
                        continue
            
            current_url = self.page.url
            if 'dashboard' in current_url or 'home' in current_url or current_url != settings.JAGRITI_BASE_URL:
                self.authenticated = True
                logging.info("Authentication successful")
                return True
                
            logging.error("Authentication failed")
            return False
            
        except Exception as e:
            logging.error(f"Authentication error: {e}")
            return False
    
    async def check_otp_required(self) -> bool:
        otp_indicators = [
            'text="Enter OTP"',
            'input[placeholder*="OTP"]',
            'input[placeholder*="otp"]',
            '.otp-input',
            '#otp'
        ]
        
        for selector in otp_indicators:
            try:
                await self.page.wait_for_selector(selector, timeout=2000)
                return True
            except:
                continue
        return False
    
    async def handle_otp(self) -> bool:
        try:
            logging.info("OTP handling - waiting for manual input or automation")
            
            await self.page.wait_for_timeout(5000)
            
            otp_input_selectors = [
                'input[placeholder*="OTP"]',
                'input[placeholder*="otp"]',
                'input[name="otp"]',
                '.otp-input',
                '#otp'
            ]
            
            otp_input_found = False
            for selector in otp_input_selectors:
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        otp_input_found = True
                        logging.info(f"OTP input found: {selector}")
                        
                        logging.info("Please enter OTP manually in the browser or implement OTP service integration")
                        
                        for attempt in range(30):
                            await self.page.wait_for_timeout(2000)
                            value = await element.get_attribute('value')
                            if value and len(value) >= 4:
                                submit_selectors = [
                                    'button[type="submit"]',
                                    'button:has-text("Verify")',
                                    'button:has-text("Submit")',
                                    '.verify-btn'
                                ]
                                
                                for submit_selector in submit_selectors:
                                    try:
                                        await self.page.click(submit_selector)
                                        break
                                    except:
                                        continue
                                
                                await self.page.wait_for_timeout(3000)
                                current_url = self.page.url
                                if 'dashboard' in current_url or 'home' in current_url:
                                    self.authenticated = True
                                    return True
                        break
                except:
                    continue
            
            if not otp_input_found:
                logging.error("OTP input field not found")
                return False
                
            return False
            
        except Exception as e:
            logging.error(f"OTP handling error: {e}")
            return False
    
    async def navigate_to_advance_search(self) -> bool:
        try:
            if not self.authenticated:
                logging.error("Not authenticated")
                return False
            
            search_links = [
                'text="Advance Search"',
                'text="Advanced Search"', 
                'a[href*="advance-search"]',
                'a[href*="advanced-search"]',
                '.advance-search',
                '#advanceSearch'
            ]
            
            for selector in search_links:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                    await self.page.click(selector)
                    logging.info(f"Clicked advance search with selector: {selector}")
                    await self.page.wait_for_timeout(3000)
                    return True
                except:
                    continue
            
            await self.page.goto(f"{settings.JAGRITI_BASE_URL}/advance-case-search")
            await self.page.wait_for_timeout(3000)
            return True
            
        except Exception as e:
            logging.error(f"Navigate to advance search error: {e}")
            return False
    
    async def extract_states(self) -> List[Dict]:
        try:
            await self.navigate_to_advance_search()
            
            state_selectors = [
                'select[name="state"]',
                'select#state',
                '.state-select',
                'select:has(option:text("Karnataka"))'
            ]
            
            for selector in state_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=10000)
                    options = await self.page.query_selector_all(f"{selector} option")
                    
                    states = []
                    for option in options:
                        value = await option.get_attribute('value')
                        text = await option.text_content()
                        
                        if value and text and value != '' and text.strip():
                            states.append({
                                'id': value.strip(),
                                'name': text.strip().upper(),
                                'display_name': text.strip()
                            })
                    
                    if states:
                        logging.info(f"Extracted {len(states)} states")
                        return states
                        
                except Exception as e:
                    logging.debug(f"State selector {selector} failed: {e}")
                    continue
            
            logging.error("Could not extract states")
            return []
            
        except Exception as e:
            logging.error(f"Extract states error: {e}")
            return []
    
    async def extract_commissions(self, state_id: str) -> List[Dict]:
        try:
            await self.navigate_to_advance_search()
            
            state_select = await self.page.query_selector('select[name="state"], select#state, .state-select')
            if state_select:
                await state_select.select_option(state_id)
                await self.page.wait_for_timeout(2000)
            
            commission_selectors = [
                'select[name="commission"]',
                'select#commission',
                '.commission-select'
            ]
            
            for selector in commission_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=10000)
                    options = await self.page.query_selector_all(f"{selector} option")
                    
                    commissions = []
                    for option in options:
                        value = await option.get_attribute('value')
                        text = await option.text_content()
                        
                        if value and text and value != '' and text.strip():
                            commissions.append({
                                'id': value.strip(),
                                'name': text.strip(),
                                'display_name': text.strip(),
                                'state_id': state_id
                            })
                    
                    if commissions:
                        logging.info(f"Extracted {len(commissions)} commissions for state {state_id}")
                        return commissions
                        
                except Exception as e:
                    logging.debug(f"Commission selector {selector} failed: {e}")
                    continue
            
            return []
            
        except Exception as e:
            logging.error(f"Extract commissions error: {e}")
            return []
    
    async def search_cases(self, search_params: Dict) -> List[Dict]:
        try:
            await self.navigate_to_advance_search()
            
            state_select = await self.page.query_selector('select[name="state"], select#state')
            if state_select:
                await state_select.select_option(search_params.get('state_id', ''))
                await self.page.wait_for_timeout(1000)
            
            commission_select = await self.page.query_selector('select[name="commission"], select#commission')
            if commission_select:
                await commission_select.select_option(search_params.get('commission_id', ''))
                await self.page.wait_for_timeout(1000)
            
            search_type = search_params.get('search_type', 'complainant')
            search_value = search_params.get('search_value', '')
            
            field_mapping = {
                'case_number': ['input[name="caseNumber"]', 'input#caseNumber'],
                'complainant': ['input[name="complainant"]', 'input#complainant'],
                'respondent': ['input[name="respondent"]', 'input#respondent'],
                'complainant_advocate': ['input[name="complainantAdvocate"]', 'input#complainantAdvocate'],
                'respondent_advocate': ['input[name="respondentAdvocate"]', 'input#respondentAdvocate'],
                'judge': ['input[name="judgeName"]', 'input#judgeName'],
                'industry_type': ['select[name="industryType"]', 'select#industryType']
            }
            
            input_selectors = field_mapping.get(search_type, ['input[name="complainant"]'])
            
            for selector in input_selectors:
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        if 'select' in selector:
                            await element.select_option(search_value)
                        else:
                            await element.fill(search_value)
                        break
                except:
                    continue
            
            search_button_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Search")',
                '.search-btn',
                '#searchBtn'
            ]
            
            for selector in search_button_selectors:
                try:
                    await self.page.click(selector)
                    break
                except:
                    continue
            
            await self.page.wait_for_timeout(5000)
            
            table_selector = 'table, .table, .results-table, #resultsTable'
            await self.page.wait_for_selector(table_selector, timeout=15000)
            
            cases = await self.page.evaluate('''
                () => {
                    const cases = [];
                    const tables = document.querySelectorAll('table');
                    
                    for (const table of tables) {
                        const rows = table.querySelectorAll('tbody tr, tr:not(:first-child)');
                        
                        for (const row of rows) {
                            const cells = row.querySelectorAll('td, th');
                            if (cells.length >= 6) {
                                const caseData = {
                                    case_number: cells[0]?.textContent?.trim() || '',
                                    case_stage: cells[1]?.textContent?.trim() || '',
                                    filing_date: cells[2]?.textContent?.trim() || '',
                                    complainant: cells[3]?.textContent?.trim() || '',
                                    complainant_advocate: cells[4]?.textContent?.trim() || '',
                                    respondent: cells[5]?.textContent?.trim() || '',
                                    respondent_advocate: cells[6]?.textContent?.trim() || '',
                                    document_link: ''
                                };
                                
                                const linkElement = cells[cells.length - 1]?.querySelector('a');
                                if (linkElement) {
                                    caseData.document_link = linkElement.href;
                                }
                                
                                if (caseData.case_number) {
                                    cases.push(caseData);
                                }
                            }
                        }
                        
                        if (cases.length > 0) break;
                    }
                    
                    return cases;
                }
            ''')
            
            logging.info(f"Extracted {len(cases)} cases from search results")
            return cases
            
        except Exception as e:
            logging.error(f"Search cases error: {e}")
            return []