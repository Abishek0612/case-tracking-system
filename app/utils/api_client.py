import logging
from typing import Dict, List
from app.utils.jagriti_scraper import JagritiClient


class JagritiAPIClient:
    def __init__(self):
        self.client = JagritiClient()
    
    async def get_states(self) -> List[Dict]:
        logging.info("Attempting to fetch states from real Jagriti portal...")
        return await self.client.get_states()
    
    async def get_commissions(self, state_id: str) -> List[Dict]:
        logging.info(f"Attempting to fetch commissions for state {state_id} from real portal...")
        return await self.client.get_commissions(state_id)
    
    async def search_cases(self, params: Dict) -> List[Dict]:
        logging.info("Attempting real case search on Jagriti portal...")
        return await self.client.search_cases(params)