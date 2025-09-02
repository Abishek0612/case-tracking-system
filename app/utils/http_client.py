import httpx
import asyncio
import logging
from typing import Dict, Any, Optional

from app.core.config import settings


class HTTPClient:
    def __init__(self):
        self.timeout = httpx.Timeout(settings.JAGRITI_TIMEOUT)
        self.limits = httpx.Limits(max_keepalive_connections=20, max_connections=100)
    
    async def get(
        self, 
        url: str, 
        params: Optional[Dict] = None, 
        headers: Optional[Dict] = None
    ) -> httpx.Response:
        async with httpx.AsyncClient(
            timeout=self.timeout,
            limits=self.limits,
            follow_redirects=True
        ) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response
    
    async def post(
        self, 
        url: str, 
        data: Optional[Dict] = None, 
        json: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> httpx.Response:
        async with httpx.AsyncClient(
            timeout=self.timeout,
            limits=self.limits,
            follow_redirects=True
        ) as client:
            response = await client.post(url, data=data, json=json, headers=headers)
            response.raise_for_status()
            return response