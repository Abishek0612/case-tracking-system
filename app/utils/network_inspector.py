import httpx
import asyncio
import logging
from typing import List, Dict, Optional
import json
import re
from urllib.parse import urljoin, parse_qs


class NetworkBasedClient:
    def __init__(self):
        self.base_url = "https://e-jagriti.gov.in"
        self.session = None
        
    async def initialize_session(self):
        if self.session:
            return
            
        self.session = httpx.AsyncClient(
            timeout=30,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Cache-Control": "max-age=0"
            }
        )
    
    async def get_states_via_form_inspection(self) -> List[Dict]:
        """Get states by analyzing the actual form submission endpoints"""
        await self.initialize_session()
        
        try:
            # First, get the main search page to establish session
            main_page = await self.session.get(f"{self.base_url}/advance-case-search")
            
            # Look for embedded JavaScript data or CSRF tokens
            page_content = main_page.text
            
            # Try to find state data in JavaScript variables
            js_patterns = [
                r'states\s*[:=]\s*(\[.*?\])',
                r'stateList\s*[:=]\s*(\[.*?\])',
                r'STATE_OPTIONS\s*[:=]\s*(\[.*?\])',
                r'var\s+states\s*=\s*(\[.*?\]);',
                r'const\s+states\s*=\s*(\[.*?\]);'
            ]
            
            for pattern in js_patterns:
                match = re.search(pattern, page_content, re.DOTALL | re.IGNORECASE)
                if match:
                    try:
                        states_json = match.group(1)
                        states_data = json.loads(states_json)
                        if isinstance(states_data, list) and states_data:
                            return self._parse_embedded_states(states_data)
                    except:
                        continue
            
            # Try common AJAX endpoints that might populate dropdowns
            ajax_endpoints = [
                "/advance-case-search/get-states",
                "/api/case-search/states", 
                "/advance-search/states",
                "/ajax/get-states",
                "/case-search/ajax/states",
                "/public/states",
                "/search/get-dropdown-data"
            ]
            
            for endpoint in ajax_endpoints:
                try:
                    url = f"{self.base_url}{endpoint}"
                    response = await self.session.get(url)
                    
                    if response.status_code == 200:
                        content_type = response.headers.get('content-type', '').lower()
                        
                        if 'json' in content_type:
                            data = response.json()
                            if isinstance(data, list) and data:
                                return self._parse_api_states(data)
                            elif isinstance(data, dict) and 'states' in data:
                                return self._parse_api_states(data['states'])
                        
                        # Try parsing as HTML with select options
                        if 'html' in content_type and '<select' in response.text:
                            from bs4 import BeautifulSoup
                            soup = BeautifulSoup(response.text, 'html.parser')
                            select = soup.find('select')
                            if select:
                                return self._parse_select_options(select)
                                
                except Exception as e:
                    logging.debug(f"AJAX endpoint {endpoint} failed: {e}")
                    continue
            
            # Try form POST to trigger state loading
            form_data = {
                "action": "get_states",
                "type": "DCDRC"
            }
            
            response = await self.session.post(
                f"{self.base_url}/advance-case-search",
                data=form_data
            )
            
            if response.status_code == 200 and 'select' in response.text.lower():
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                selects = soup.find_all('select')
                for select in selects:
                    options = select.find_all('option')
                    if len(options) > 10:  # Likely states dropdown
                        return self._parse_select_options(select)
            
            # If all else fails, use hardcoded Indian states (but with real IDs we can discover)
            return await self._discover_state_ids()
            
        except Exception as e:
            logging.error(f"Network inspection failed: {e}")
            raise
    
    def _parse_embedded_states(self, data: List) -> List[Dict]:
        """Parse states from JavaScript embedded data"""
        states = []
        for item in data:
            if isinstance(item, dict):
                state_id = item.get('id') or item.get('value') or item.get('code')
                state_name = item.get('name') or item.get('text') or item.get('label')
            elif isinstance(item, list) and len(item) >= 2:
                state_id, state_name = item[0], item[1]
            else:
                continue
                
            if state_id and state_name:
                states.append({
                    "id": str(state_id),
                    "name": state_name.upper(),
                    "display_name": state_name
                })
        
        return states
    
    def _parse_api_states(self, data: List) -> List[Dict]:
        """Parse states from API response"""
        return self._parse_embedded_states(data)
    
    def _parse_select_options(self, select_element) -> List[Dict]:
        """Parse states from HTML select options"""
        states = []
        for option in select_element.find_all('option'):
            value = option.get('value', '').strip()
            text = option.get_text(strip=True)
            
            if value and text and text.lower() not in ['select', 'choose', '--']:
                states.append({
                    "id": value,
                    "name": text.upper(), 
                    "display_name": text
                })
        
        return states
    
    async def _discover_state_ids(self) -> List[Dict]:
        """Discover state IDs by trying common patterns"""
        indian_states = [
            "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
            "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
            "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
            "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
            "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
            "Delhi", "Jammu and Kashmir", "Ladakh", "Chandigarh", "Dadra and Nagar Haveli",
            "Daman and Diu", "Lakshadweep", "Puducherry"
        ]
        
        states = []
        for i, state_name in enumerate(indian_states, 1):
            # Try different ID patterns commonly used in government systems
            possible_ids = [str(i), f"{i:02d}", f"ST{i:02d}", str(i).zfill(3)]
            
            for state_id in possible_ids:
                try:
                    # Test if this state ID works by trying to get commissions
                    test_url = f"{self.base_url}/advance-case-search"
                    test_data = {"state_code": state_id, "action": "get_commissions"}
                    
                    response = await self.session.post(test_url, data=test_data)
                    if response.status_code == 200 and len(response.text) > 1000:
                        # This state ID seems to work
                        states.append({
                            "id": state_id,
                            "name": state_name.upper(),
                            "display_name": state_name
                        })
                        break
                        
                except:
                    continue
        
        return states[:10]  # Return first 10 working states
    
    async def get_commissions(self, state_id: str) -> List[Dict]:
        """Get commissions for a state using form submission"""
        await self.initialize_session()
        
        try:
            form_data = {
                "state_code": state_id,
                "action": "get_commissions",
                "court_type": "DCDRC"
            }
            
            response = await self.session.post(
                f"{self.base_url}/advance-case-search",
                data=form_data
            )
            
            if response.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for commission dropdown
                selects = soup.find_all('select')
                for select in selects:
                    # Check if this looks like a commission dropdown
                    first_option = select.find('option')
                    if first_option and 'commission' in first_option.get_text().lower():
                        return self._parse_commission_options(select, state_id)
                
                # If no clear commission dropdown, try the largest select
                if selects:
                    largest_select = max(selects, key=lambda s: len(s.find_all('option')))
                    return self._parse_commission_options(largest_select, state_id)
            
            return []
            
        except Exception as e:
            logging.error(f"Failed to get commissions for state {state_id}: {e}")
            return []
    
    def _parse_commission_options(self, select_element, state_id: str) -> List[Dict]:
        """Parse commissions from HTML select options"""
        commissions = []
        for option in select_element.find_all('option'):
            value = option.get('value', '').strip()
            text = option.get_text(strip=True)
            
            if value and text and text.lower() not in ['select', 'choose', '--']:
                commissions.append({
                    "id": value,
                    "name": text,
                    "display_name": text,
                    "state_id": state_id
                })
        
        return commissions
    
    async def close(self):
        if self.session:
            await self.session.aclose()