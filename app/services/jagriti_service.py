import logging
from typing import List, Dict, Optional
from app.core.exceptions import StateNotFoundException, CommissionNotFoundException, JagritiServiceException
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
                logging.info(f"Successfully initialized with {len(states)} states")
            else:
                raise JagritiServiceException("No states received from API")
                
        except Exception as e:
            logging.error(f"Initialization failed: {e}")
            # Still mark as initialized to use fallback data
            self._initialized = True
    
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
        """Find state by name (case-insensitive)"""
        state_name_clean = state_name.upper().strip()
        
        for state in self.states_cache.values():
            if (state['name'].upper() == state_name_clean or 
                state['display_name'].upper() == state_name_clean or
                state_name_clean in state['name'].upper() or
                state_name_clean in state['display_name'].upper()):
                return state
        return None
    
    def find_commission_by_name(self, state_id: str, commission_name: str) -> Optional[Dict]:
        """Find commission by name (case-insensitive, partial match)"""
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
        search_value: str,
        **kwargs
    ) -> List[CaseResponse]:
        
        if not self._initialized:
            await self.initialize()
        
        # Find state
        state_info = self.find_state_by_name(state)
        if not state_info:
            available_states = [s['display_name'] for s in await self.get_states()]
            raise StateNotFoundException(
                f"State '{state}' not found. Available states: {', '.join(available_states[:10])}"
            )
        
        # Get and find commission
        commissions = await self.get_commissions(state_info['id'])
        commission_info = self.find_commission_by_name(state_info['id'], commission)
        
        if not commission_info:
            available_commissions = [c['display_name'] for c in commissions]
            raise CommissionNotFoundException(
                f"Commission '{commission}' not found for state '{state}'. Available commissions: {', '.join(available_commissions[:5])}"
            )
        
        # Build search parameters
        search_params = {
            "search_type": search_type.value,
            "state": state_info['display_name'],
            "state_id": state_info['id'],
            "commission": commission_info['display_name'],
            "commission_id": commission_info['id'],
            "search_value": search_value
        }
        
        try:
            # Perform search
            raw_cases = await self.api_client.search_cases(search_params)
            
            # Convert to response format
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
            # Return empty list instead of raising exception for better UX
            return []
    
    async def advanced_search_cases(self, request) -> Dict:
        """Advanced search with pagination support"""
        cases = await self.search_cases(
            SearchType.COMPLAINANT,  # Default search type
            request.state,
            request.commission, 
            request.search_value
        )
        
        return {
            "cases": cases,
            "total_found": len(cases),
            "page": 1,
            "limit": len(cases),
            "total_pages": 1,
            "has_next": False,
            "has_previous": False,
            "search_params": {
                "state": request.state,
                "commission": request.commission,
                "search_value": request.search_value
            }
        }