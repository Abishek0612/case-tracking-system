import httpx
import asyncio
import logging
from typing import List, Dict, Optional
import json

class JagritiAPIClient:
    def __init__(self):
        self.base_url = "https://e-jagriti.gov.in"
        self.session_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "Origin": "https://e-jagriti.gov.in",
            "Referer": "https://e-jagriti.gov.in/advance-case-search"
        }
        
    async def get_states(self) -> List[Dict]:
        """Try to get states from API endpoints"""
        
        api_endpoints = [
            "/api/states",
            "/api/master/states", 
            "/api/v1/states",
            "/api/public/states",
            "/api/master/state-list",
            "/api/dropdown/states",
            "/services/states",
            "/rest/states"
        ]
        
        async with httpx.AsyncClient(timeout=30) as client:
            for endpoint in api_endpoints:
                try:
                    url = f"{self.base_url}{endpoint}"
                    logging.info(f"Trying API endpoint: {url}")
                    
                    response = await client.get(url, headers=self.session_headers)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if isinstance(data, list) and data:
                            logging.info(f"Found states data at {endpoint}")
                            return self._normalize_states(data)
                        elif isinstance(data, dict) and 'data' in data:
                            logging.info(f"Found states data at {endpoint}")
                            return self._normalize_states(data['data'])
                            
                except Exception as e:
                    logging.debug(f"API endpoint {endpoint} failed: {e}")
                    continue
        
        # Try GraphQL endpoint
        try:
            graphql_url = f"{self.base_url}/graphql"
            query = {
                "query": """
                {
                    states {
                        id
                        name
                        displayName
                    }
                }
                """
            }
            
            response = await client.post(graphql_url, json=query, headers=self.session_headers)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and 'states' in data['data']:
                    return self._normalize_states(data['data']['states'])
        except:
            pass
            
        raise Exception("Could not find states API endpoint")
    
    async def get_commissions(self, state_id: str) -> List[Dict]:
        """Try to get commissions from API endpoints"""
        
        api_endpoints = [
            f"/api/commissions?state_id={state_id}",
            f"/api/master/commissions/{state_id}",
            f"/api/v1/commissions?stateId={state_id}",
            f"/api/public/commissions?state={state_id}",
            f"/api/dropdown/commissions?state_code={state_id}"
        ]
        
        async with httpx.AsyncClient(timeout=30) as client:
            for endpoint in api_endpoints:
                try:
                    url = f"{self.base_url}{endpoint}"
                    logging.info(f"Trying commissions API: {url}")
                    
                    response = await client.get(url, headers=self.session_headers)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if isinstance(data, list) and data:
                            return self._normalize_commissions(data, state_id)
                        elif isinstance(data, dict) and 'data' in data:
                            return self._normalize_commissions(data['data'], state_id)
                            
                except Exception as e:
                    logging.debug(f"Commissions API {endpoint} failed: {e}")
                    continue
        
        return []
    
    def _normalize_states(self, data: List[Dict]) -> List[Dict]:
        """Normalize state data from different API formats"""
        states = []
        for item in data:
            state_id = item.get('id') or item.get('stateId') or item.get('state_id') or item.get('code')
            state_name = item.get('name') or item.get('stateName') or item.get('state_name') or item.get('text')
            display_name = item.get('displayName') or item.get('display_name') or state_name
            
            if state_id and state_name:
                states.append({
                    "id": str(state_id),
                    "name": state_name.upper(),
                    "display_name": display_name
                })
        
        return states
    
    def _normalize_commissions(self, data: List[Dict], state_id: str) -> List[Dict]:
        """Normalize commission data from different API formats"""
        commissions = []
        for item in data:
            comm_id = item.get('id') or item.get('commissionId') or item.get('commission_id') or item.get('code')
            comm_name = item.get('name') or item.get('commissionName') or item.get('commission_name') or item.get('text')
            
            if comm_id and comm_name:
                commissions.append({
                    "id": str(comm_id),
                    "name": comm_name,
                    "display_name": comm_name,
                    "state_id": state_id
                })
        
        return commissions