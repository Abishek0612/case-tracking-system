import logging
from typing import List, Dict, Optional
from datetime import datetime

from app.core.exceptions import JagritiServiceException
from app.utils.api_client import JagritiAPIClient
from app.utils.browser_client import BrowserClient


class HybridJagritiService:
    def __init__(self):
        self.api_client = JagritiAPIClient()
        self.browser_client = BrowserClient()
        self.states_cache: Dict[str, Dict] = {}
        self.commissions_cache: Dict[str, List[Dict]] = {}
        self._initialized = False
        
    async def initialize(self):
        if self._initialized:
            return
        
        try:
            # Try API first (faster)
            logging.info("Attempting to get states via API...")
            try:
                states = await self.api_client.get_states()
                if states:
                    self.states_cache = {state['id']: state for state in states}
                    self._initialized = True
                    logging.info(f"Successfully got {len(states)} states via API")
                    return
            except Exception as e:
                logging.warning(f"API approach failed: {e}")
            
            # Fallback to browser (slower but more reliable)
            logging.info("Falling back to browser scraping...")
            states = self.browser_client.get_states()
            self.states_cache = {state['id']: state for state in states}
            self._initialized = True
            logging.info(f"Successfully got {len(states)} states via browser")
            
        except Exception as e:
            logging.error(f"Both API and browser approaches failed: {e}")
            raise JagritiServiceException(f"Could not initialize service: {str(e)}")
    
    async def get_states(self) -> List[Dict]:
        if not self._initialized:
            await self.initialize()
        return list(self.states_cache.values())
    
    async def get_commissions(self, state_id: str) -> List[Dict]:
        if not self._initialized:
            await self.initialize()
            
        cache_key = f"commissions_{state_id}"
        
        if cache_key not in self.commissions_cache:
            try:
                # Try API first
                commissions = await self.api_client.get_commissions(state_id)
                if not commissions:
                    # Fallback to browser
                    commissions = self.browser_client.get_commissions(state_id)
                
                self.commissions_cache[cache_key] = commissions
            except Exception as e:
                logging.error(f"Failed to get commissions for state {state_id}: {e}")
                self.commissions_cache[cache_key] = []
        
        return self.commissions_cache[cache_key]