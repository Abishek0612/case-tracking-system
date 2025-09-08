import logging
from typing import List, Dict, Optional
from app.core.exceptions import StateNotFoundException, CommissionNotFoundException
from app.schemas.case import CaseResponse, SearchType
from app.utils.api_client import JagritiAPIClient


class JagritiService:
    def __init__(self):
        self.api_client = JagritiAPIClient()
        self.states_cache: Dict[str, Dict] = {}
        self.commissions_cache: Dict[str, List[Dict]] = {}
        self._initialized = False
        
    async def initialize(self):
        if self._initialized:
            return
        
        try:
            states = await self.api_client.get_states()
            if states:
                self.states_cache = {state['id']: state for state in states}
                self._initialized = True
                logging.info(f"Initialized with {len(states)} states")
            else:
                raise Exception("No states received")
                
        except Exception as e:
            logging.error(f"Initialization failed: {e}")
            raise
    
    async def get_states(self) -> List[Dict]:
        if not self._initialized:
            await self.initialize()
        return list(self.states_cache.values())
    
    async def get_commissions(self, state_id: str) -> List[Dict]:
        if not self._initialized:
            await self.initialize()
            
        cache_key = f"commissions_{state_id}"
        
        if cache_key not in self.commissions_cache:
            commissions = await self.api_client.get_commissions(state_id)
            self.commissions_cache[cache_key] = commissions
        
        return self.commissions_cache[cache_key]
    
    def find_state_by_name(self, state_name: str) -> Optional[Dict]:
        state_name_clean = state_name.upper().strip()
        
        for state in self.states_cache.values():
            if (state['name'].upper() == state_name_clean or 
                state['display_name'].upper() == state_name_clean or
                state_name_clean in state['name'].upper() or
                state_name_clean in state['display_name'].upper()):
                return state
        return None
    
    def find_commission_by_name(self, state_id: str, commission_name: str) -> Optional[Dict]:
        cache_key = f"commissions_{state_id}"
        if cache_key not in self.commissions_cache:
            return None
        
        commission_name_clean = commission_name.lower().strip()
        
        for commission in self.commissions_cache[cache_key]:
            comm_name = commission['name'].lower()
            comm_display = commission['display_name'].lower()
            
            if (commission_name_clean == comm_name or 
                commission_name_clean == comm_display or
                commission_name_clean in comm_name or
                commission_name_clean in comm_display):
                return commission
        return None
    
    async def search_cases(
        self, 
        search_type: SearchType, 
        state: str, 
        commission: str, 
        search_value: str
    ) -> List[CaseResponse]:
        
        if not self._initialized:
            await self.initialize()
        
        state_info = self.find_state_by_name(state)
        if not state_info:
            available = [s['display_name'] for s in await self.get_states()]
            raise StateNotFoundException(f"State '{state}' not found. Available: {available[:5]}")
        
        commissions = await self.get_commissions(state_info['id'])
        commission_info = self.find_commission_by_name(state_info['id'], commission)
        
        if not commission_info:
            available = [c['display_name'] for c in commissions]
            raise CommissionNotFoundException(f"Commission '{commission}' not found. Available: {available[:3]}")
        
        search_params = {
            "search_type": search_type.value,
            "state": state_info['display_name'],
            "state_id": state_info['id'],
            "commission": commission_info['display_name'],
            "commission_id": commission_info['id'],
            "search_value": search_value
        }
        
        try:
            raw_cases = await self.api_client.search_cases(search_params)
            
            cases = []
            for case_data in raw_cases:
                case = CaseResponse(
                    case_number=case_data.get("case_number", ""),
                    case_stage=case_data.get("case_stage", ""),
                    filing_date=case_data.get("filing_date", ""),
                    complainant=case_data.get("complainant", ""),
                    complainant_advocate=case_data.get("complainant_advocate"),
                    respondent=case_data.get("respondent", ""),
                    respondent_advocate=case_data.get("respondent_advocate"),
                    document_link=case_data.get("document_link")
                )
                cases.append(case)
            
            logging.info(f"Search returned {len(cases)} cases for {search_type.value}: {search_value}")
            return cases
            
        except Exception as e:
            logging.error(f"Case search failed: {e}")
            return []