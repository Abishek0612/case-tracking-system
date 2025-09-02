import httpx
import asyncio
from typing import List, Dict, Optional, Tuple
from bs4 import BeautifulSoup
import json
import logging
from urllib.parse import urljoin

from app.core.config import settings
from app.core.exceptions import JagritiServiceException
from app.schemas.case import CaseResponse, SearchType
from app.utils.http_client import HTTPClient


class JagritiService:
    def __init__(self):
        self.base_url = settings.JAGRITI_BASE_URL
        self.http_client = HTTPClient()
        self.session_cookies = None
        self.states_mapping = {}
        self.commissions_mapping = {}
        
    async def initialize(self):
        await self._load_mappings()
    
    async def _load_mappings(self):
        try:
            states_data = await self._fetch_states()
            self.states_mapping = {
                state['display_name'].upper(): state['id'] 
                for state in states_data
            }
            
            for state in states_data:
                commissions_data = await self._fetch_commissions(state['id'])
                self.commissions_mapping[state['id']] = {
                    comm['display_name']: comm['id']
                    for comm in commissions_data
                }
        except Exception as e:
            logging.error(f"Failed to load mappings: {e}")
            raise JagritiServiceException(f"Initialization failed: {str(e)}")
    
    async def _fetch_states(self) -> List[Dict]:
        url = f"{self.base_url}/api/states"
        try:
            response = await self.http_client.get(url)
            return self._parse_states_response(response)
        except Exception as e:
            logging.error(f"Failed to fetch states: {e}")
            return self._get_fallback_states()
    
    async def _fetch_commissions(self, state_id: str) -> List[Dict]:
        url = f"{self.base_url}/api/commissions"
        params = {"state_id": state_id}
        try:
            response = await self.http_client.get(url, params=params)
            return self._parse_commissions_response(response, state_id)
        except Exception as e:
            logging.error(f"Failed to fetch commissions for state {state_id}: {e}")
            return []
    
    def _parse_states_response(self, response: httpx.Response) -> List[Dict]:
        soup = BeautifulSoup(response.text, 'html.parser')
        states = []
        
        select_element = soup.find('select', {'name': 'state'})
        if select_element:
            for option in select_element.find_all('option'):
                if option.get('value'):
                    states.append({
                        'id': option.get('value'),
                        'name': option.get('value'),
                        'display_name': option.text.strip()
                    })
        
        return states
    
    def _parse_commissions_response(self, response: httpx.Response, state_id: str) -> List[Dict]:
        soup = BeautifulSoup(response.text, 'html.parser')
        commissions = []
        
        select_element = soup.find('select', {'name': 'commission'})
        if select_element:
            for option in select_element.find_all('option'):
                if option.get('value'):
                    commissions.append({
                        'id': option.get('value'),
                        'name': option.get('value'),
                        'display_name': option.text.strip(),
                        'state_id': state_id
                    })
        
        return commissions
    
    def _get_fallback_states(self) -> List[Dict]:
        return [
            {'id': '29', 'name': 'KARNATAKA', 'display_name': 'Karnataka'},
            {'id': '19', 'name': 'MAHARASHTRA', 'display_name': 'Maharashtra'},
            {'id': '7', 'name': 'DELHI', 'display_name': 'Delhi'},
            {'id': '32', 'name': 'TAMIL NADU', 'display_name': 'Tamil Nadu'},
            {'id': '28', 'name': 'ANDHRA PRADESH', 'display_name': 'Andhra Pradesh'},
        ]
    
    async def search_cases(
        self, 
        search_type: SearchType, 
        state: str, 
        commission: str, 
        search_value: str
    ) -> List[CaseResponse]:
        try:
            state_id = self._get_state_id(state)
            commission_id = self._get_commission_id(state_id, commission)
            
            search_params = self._build_search_params(
                search_type, state_id, commission_id, search_value
            )
            
            cases_data = await self._perform_search(search_params)
            return self._parse_cases_response(cases_data)
            
        except Exception as e:
            logging.error(f"Case search failed: {e}")
            raise JagritiServiceException(f"Search failed: {str(e)}")
    
    def _get_state_id(self, state_name: str) -> str:
        state_key = state_name.upper().strip()
        if state_key not in self.states_mapping:
            raise JagritiServiceException(f"State '{state_name}' not found")
        return self.states_mapping[state_key]
    
    def _get_commission_id(self, state_id: str, commission_name: str) -> str:
        if state_id not in self.commissions_mapping:
            raise JagritiServiceException(f"No commissions found for state")
        
        commission_map = self.commissions_mapping[state_id]
        if commission_name not in commission_map:
            available = list(commission_map.keys())
            raise JagritiServiceException(
                f"Commission '{commission_name}' not found. Available: {available}"
            )
        
        return commission_map[commission_name]
    
    def _build_search_params(
        self, 
        search_type: SearchType, 
        state_id: str, 
        commission_id: str, 
        search_value: str
    ) -> Dict:
        base_params = {
            'state_code': state_id,
            'dist_code': commission_id,
            'court_code': 'DCDRC',
            'case_type': 'Daily Order',
            'date_type': 'case_filing_date',
            'from_date': '01/01/2020',
            'to_date': '31/12/2025',
        }
        
        search_field_mapping = {
            SearchType.CASE_NUMBER: 'case_no',
            SearchType.COMPLAINANT: 'pet_name',
            SearchType.RESPONDENT: 'res_name',
            SearchType.COMPLAINANT_ADVOCATE: 'pet_adv',
            SearchType.RESPONDENT_ADVOCATE: 'res_adv',
            SearchType.INDUSTRY_TYPE: 'business_cat',
            SearchType.JUDGE: 'judge_name',
        }
        
        base_params[search_field_mapping[search_type]] = search_value
        return base_params
    
    async def _perform_search(self, params: Dict) -> httpx.Response:
        search_url = f"{self.base_url}/advance-case-search-result"
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = await self.http_client.post(
            search_url, 
            data=params, 
            headers=headers
        )
        
        return response
    
    def _parse_cases_response(self, response: httpx.Response) -> List[CaseResponse]:
        soup = BeautifulSoup(response.text, 'html.parser')
        cases = []
        
        results_table = soup.find('table', class_='table')
        if not results_table:
            return cases
        
        rows = results_table.find('tbody').find_all('tr') if results_table.find('tbody') else []
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 7:
                case = CaseResponse(
                    case_number=cells[0].get_text(strip=True),
                    case_stage=cells[1].get_text(strip=True),
                    filing_date=self._format_date(cells[2].get_text(strip=True)),
                    complainant=cells[3].get_text(strip=True),
                    complainant_advocate=cells[4].get_text(strip=True) or None,
                    respondent=cells[5].get_text(strip=True),
                    respondent_advocate=cells[6].get_text(strip=True) or None,
                    document_link=self._extract_document_link(cells[0])
                )
                cases.append(case)
        
        return cases
    
    def _format_date(self, date_str: str) -> str:
        try:
            from datetime import datetime
            dt = datetime.strptime(date_str, '%d/%m/%Y')
            return dt.strftime('%Y-%m-%d')
        except:
            return date_str
    
    def _extract_document_link(self, cell) -> Optional[str]:
        link = cell.find('a')
        if link and link.get('href'):
            return urljoin(self.base_url, link.get('href'))
        return None
    
    async def get_states(self) -> List[Dict]:
        return [
            {'id': state_id, 'name': state_name, 'display_name': state_name.title()}
            for state_name, state_id in self.states_mapping.items()
        ]
    
    async def get_commissions(self, state_id: str) -> List[Dict]:
        if state_id not in self.commissions_mapping:
            return []
        
        return [
            {
                'id': comm_id, 
                'name': comm_name, 
                'display_name': comm_name,
                'state_id': state_id
            }
            for comm_name, comm_id in self.commissions_mapping[state_id].items()
        ]