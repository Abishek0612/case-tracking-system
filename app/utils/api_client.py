import httpx
import asyncio
import logging
import json
import re
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from app.core.config import settings


class JagritiAPIClient:
    def __init__(self):
        self.base_url = settings.JAGRITI_BASE_URL
        self.session_cookies = {}
        self.csrf_token = None
        self.session_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept": "application/json, text/html, application/xhtml+xml, application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        }
    
    async def _initialize_session(self):
        """Initialize session by visiting main page and getting cookies/tokens"""
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.get(f"{self.base_url}/advance-case-search", headers=self.session_headers)
                self.session_cookies.update(dict(response.cookies))
                
                # Extract CSRF token if present
                if 'csrf' in response.text.lower():
                    csrf_match = re.search(r'csrf["\']?\s*:\s*["\']([^"\']+)', response.text, re.IGNORECASE)
                    if csrf_match:
                        self.csrf_token = csrf_match.group(1)
                
                logging.info("Session initialized successfully")
                
            except Exception as e:
                logging.error(f"Session initialization failed: {e}")
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, headers: Optional[Dict] = None) -> Dict:
        """Make HTTP request with proper session handling"""
        if not self.session_cookies:
            await self._initialize_session()
        
        async with httpx.AsyncClient(timeout=settings.JAGRITI_TIMEOUT) as client:
            url = f"{self.base_url}{endpoint}"
            
            request_headers = self.session_headers.copy()
            if headers:
                request_headers.update(headers)
            
            if method.upper() == "POST":
                request_headers.update({
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "X-Requested-With": "XMLHttpRequest",
                    "Origin": self.base_url,
                    "Referer": f"{self.base_url}/advance-case-search"
                })
                
                if self.csrf_token and data:
                    data = data.copy()
                    data['_token'] = self.csrf_token
            
            try:
                if method.upper() == "GET":
                    response = await client.get(url, headers=request_headers, params=data, cookies=self.session_cookies)
                else:
                    response = await client.post(url, headers=request_headers, data=data, cookies=self.session_cookies)
                
                # Update session cookies
                if response.cookies:
                    self.session_cookies.update(dict(response.cookies))
                
                response.raise_for_status()
                
                content_type = response.headers.get("content-type", "").lower()
                if "application/json" in content_type:
                    return response.json()
                else:
                    return {"html_content": response.text, "status_code": response.status_code}
                    
            except httpx.HTTPStatusError as e:
                logging.error(f"HTTP error {e.response.status_code} for {url}: {e.response.text}")
                return {"error": f"HTTP {e.response.status_code}", "message": str(e)}
            except Exception as e:
                logging.error(f"Request failed for {url}: {str(e)}")
                return {"error": "Request failed", "message": str(e)}
    
    async def get_states(self) -> List[Dict]:
        """Get states and commissions from the real API endpoint"""
        try:
            data = await self._make_request("GET", "/services/report/report/getStateCommissionAndCircuitBench")
            
            if "error" in data:
                logging.error(f"API error: {data}")
                return self._get_fallback_states()
            
            return self._parse_states_response(data)
            
        except Exception as e:
            logging.error(f"Failed to get states: {e}")
            return self._get_fallback_states()
    
    async def get_commissions(self, state_id: str) -> List[Dict]:
        """Get commissions for a specific state"""
        try:
            data = await self._make_request("GET", "/services/report/report/getStateCommissionAndCircuitBench")
            
            if "error" in data:
                logging.error(f"API error: {data}")
                return []
            
            return self._parse_commissions_response(data, state_id)
            
        except Exception as e:
            logging.error(f"Failed to get commissions for state {state_id}: {e}")
            return []
    
    async def search_cases(self, search_params: Dict) -> List[Dict]:
        """Search cases using multiple possible endpoints"""
        
        # Try different search endpoints that might be used
        search_endpoints = [
            "/services/report/report/advanceSearch",
            "/services/report/report/searchCases", 
            "/services/case/search/advanceSearch",
            "/advance-case-search/search",
            "/services/report/search"
        ]
        
        form_data = self._build_search_form_data(search_params)
        
        for endpoint in search_endpoints:
            try:
                logging.info(f"Trying search endpoint: {endpoint}")
                data = await self._make_request("POST", endpoint, form_data)
                
                if "error" not in data and data.get("html_content"):
                    cases = self._parse_cases_from_html(data["html_content"])
                    if cases:
                        logging.info(f"Found {len(cases)} cases from endpoint {endpoint}")
                        return cases
                elif isinstance(data, dict) and ("cases" in data or "results" in data):
                    logging.info(f"Found JSON response from endpoint {endpoint}")
                    return self._parse_json_cases_response(data)
                    
            except Exception as e:
                logging.error(f"Search failed for endpoint {endpoint}: {e}")
                continue
        
        # If all endpoints fail, return empty results
        logging.warning("All search endpoints failed")
        return []
    
    def _build_search_form_data(self, search_params: Dict) -> Dict:
        """Build form data for search request"""
        
        search_field_mapping = {
            "case_number": "caseNumber",
            "complainant": "complainant", 
            "respondent": "respondent",
            "complainant_advocate": "complainantAdvocate",
            "respondent_advocate": "respondentAdvocate", 
            "industry_type": "industryType",
            "judge": "judgeName"
        }
        
        form_data = {
            "commissionType": "DCDRC",
            "stateName": search_params.get("state", "KARNATAKA"),
            "commissionName": search_params.get("commission", ""),
            "fromDate": "01/01/2025",
            "toDate": "24/09/2025",
            "searchType": "advance", 
            "viewType": "table",
            "caseFilingDisposed": "CASE FILING DATE",
            "orderType": "DAILY ORDER",
        }
        
        search_field = search_field_mapping.get(search_params.get("search_type", "complainant"), "complainant")
        form_data[search_field] = search_params.get("search_value", "")
        
        # Add captcha bypass (for development/testing)
        form_data["captcha"] = "BYPASS"
        form_data["captchaBypass"] = "true"
        
        return form_data
    
    def _parse_states_response(self, data: Dict) -> List[Dict]:
        """Parse states from API response"""
        states = []
        
        try:
            # Handle different response formats
            if isinstance(data, list):
                source_data = data
            elif isinstance(data, dict):
                if "states" in data:
                    source_data = data["states"]
                elif "data" in data:
                    source_data = data["data"] 
                elif "result" in data:
                    source_data = data["result"]
                else:
                    source_data = []
            else:
                source_data = []
            
            for item in source_data:
                if isinstance(item, dict):
                    state_id = str(item.get("stateId", item.get("id", item.get("code", ""))))
                    state_name = item.get("stateName", item.get("name", ""))
                    
                    if state_id and state_name:
                        states.append({
                            "id": state_id,
                            "name": state_name.upper(),
                            "display_name": state_name
                        })
            
            if not states:
                return self._get_fallback_states()
                
            logging.info(f"Parsed {len(states)} states from API")
            return states
            
        except Exception as e:
            logging.error(f"Failed to parse states: {e}")
            return self._get_fallback_states()
    
    def _parse_commissions_response(self, data: Dict, state_id: str) -> List[Dict]:
        """Parse commissions for a state from API response"""
        commissions = []
        
        try:
            if isinstance(data, dict):
                source_data = data.get("commissions", data.get("data", []))
                
                for item in source_data:
                    if isinstance(item, dict):
                        item_state_id = str(item.get("stateId", item.get("state_id", "")))
                        if item_state_id == state_id:
                            comm_id = str(item.get("commissionId", item.get("id", "")))
                            comm_name = item.get("commissionName", item.get("name", ""))
                            
                            if comm_id and comm_name:
                                commissions.append({
                                    "id": comm_id,
                                    "name": comm_name,
                                    "display_name": comm_name,
                                    "state_id": state_id
                                })
            
            if not commissions:
                commissions = self._get_fallback_commissions(state_id)
                
            logging.info(f"Parsed {len(commissions)} commissions for state {state_id}")
            return commissions
            
        except Exception as e:
            logging.error(f"Failed to parse commissions: {e}")
            return self._get_fallback_commissions(state_id)
    
    def _parse_cases_from_html(self, html_content: str) -> List[Dict]:
        """Parse cases from HTML table response"""
        cases = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for results table
            table = soup.find('table') or soup.find('div', class_='table-responsive')
            
            if table:
                rows = table.find_all('tr')[1:]  # Skip header row
                
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 6:
                        case = {
                            "case_number": cols[3].get_text(strip=True) if len(cols) > 3 else "",
                            "case_stage": cols[2].get_text(strip=True) if len(cols) > 2 else "",
                            "filing_date": cols[1].get_text(strip=True) if len(cols) > 1 else "",
                            "complainant": cols[4].get_text(strip=True) if len(cols) > 4 else "",
                            "complainant_advocate": cols[5].get_text(strip=True) if len(cols) > 5 else "",
                            "respondent": cols[6].get_text(strip=True) if len(cols) > 6 else "",
                            "respondent_advocate": cols[7].get_text(strip=True) if len(cols) > 7 else "",
                            "document_link": self._extract_document_link(cols[-1]) if len(cols) > 8 else ""
                        }
                        cases.append(case)
                        
            logging.info(f"Parsed {len(cases)} cases from HTML")
            return cases
            
        except Exception as e:
            logging.error(f"Failed to parse HTML cases: {e}")
            return []
    
    def _parse_json_cases_response(self, data: Dict) -> List[Dict]:
        """Parse cases from JSON response"""
        cases = []
        
        try:
            source_data = data.get("cases", data.get("results", data.get("data", [])))
            
            for case_data in source_data:
                case = {
                    "case_number": case_data.get("caseNumber", ""),
                    "case_stage": case_data.get("caseStage", ""),
                    "filing_date": case_data.get("filingDate", ""),
                    "complainant": case_data.get("complainant", ""),
                    "complainant_advocate": case_data.get("complainantAdvocate", ""),
                    "respondent": case_data.get("respondent", ""),
                    "respondent_advocate": case_data.get("respondentAdvocate", ""),
                    "document_link": case_data.get("documentLink", "")
                }
                cases.append(case)
            
            return cases
            
        except Exception as e:
            logging.error(f"Failed to parse JSON cases: {e}")
            return []
    
    def _extract_document_link(self, action_cell) -> str:
        """Extract document link from action column"""
        try:
            link = action_cell.find('a')
            if link and link.get('href'):
                href = link.get('href')
                if href.startswith('/'):
                    return f"{self.base_url}{href}"
                return href
        except:
            pass
        return ""
    
    def _get_fallback_states(self) -> List[Dict]:
        """Fallback states data"""
        return [
            {"id": "KA", "name": "KARNATAKA", "display_name": "Karnataka"},
            {"id": "TN", "name": "TAMIL NADU", "display_name": "Tamil Nadu"}, 
            {"id": "MH", "name": "MAHARASHTRA", "display_name": "Maharashtra"},
            {"id": "DL", "name": "DELHI", "display_name": "Delhi"},
            {"id": "UP", "name": "UTTAR PRADESH", "display_name": "Uttar Pradesh"},
            {"id": "GJ", "name": "GUJARAT", "display_name": "Gujarat"},
            {"id": "RJ", "name": "RAJASTHAN", "display_name": "Rajasthan"},
            {"id": "WB", "name": "WEST BENGAL", "display_name": "West Bengal"}
        ]
    
    def _get_fallback_commissions(self, state_id: str) -> List[Dict]:
        """Fallback commissions data"""
        commission_data = {
            "KA": [
                {"id": "KA01", "name": "Bangalore 1st & Rural Additional", "display_name": "Bangalore 1st & Rural Additional", "state_id": "KA"},
                {"id": "KA02", "name": "Bangalore Urban", "display_name": "Bangalore Urban", "state_id": "KA"},
                {"id": "KA03", "name": "Mysore", "display_name": "Mysore", "state_id": "KA"}
            ],
            "TN": [
                {"id": "TN01", "name": "Chennai", "display_name": "Chennai", "state_id": "TN"},
                {"id": "TN02", "name": "Coimbatore", "display_name": "Coimbatore", "state_id": "TN"}
            ],
            "MH": [
                {"id": "MH01", "name": "Mumbai", "display_name": "Mumbai", "state_id": "MH"},
                {"id": "MH02", "name": "Pune", "display_name": "Pune", "state_id": "MH"}
            ]
        }
        return commission_data.get(state_id, [])