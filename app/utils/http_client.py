import httpx
import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
from urllib.parse import urljoin
import random

from app.core.config import settings
from app.core.exceptions import JagritiServiceException, SearchTimeoutException


class SessionManager:
    def __init__(self):
        self.session_cookies: Dict[str, str] = {}
        self.csrf_token: Optional[str] = None
        self.last_request_time: float = 0
        self.request_count: int = 0
        
    async def get_session_cookies(self, client: httpx.AsyncClient) -> Dict[str, str]:
        if not self.session_cookies:
            await self._initialize_session(client)
        return self.session_cookies
    
    async def _initialize_session(self, client: httpx.AsyncClient):
        """Initialize session by visiting the main page"""
        try:
            response = await client.get(settings.JAGRITI_BASE_URL)
            self.session_cookies.update(dict(response.cookies))
            
            if 'csrf' in response.text.lower():
                import re
                csrf_match = re.search(r'csrf["\']?\s*:\s*["\']([^"\']+)', response.text, re.IGNORECASE)
                if csrf_match:
                    self.csrf_token = csrf_match.group(1)
                    
        except Exception as e:
            logging.error(f"Session initialization failed: {e}")


class HTTPClient:
    def __init__(self):
        self.session_manager = SessionManager()
        self.timeout = httpx.Timeout(settings.JAGRITI_TIMEOUT)
        self.limits = httpx.Limits(
            max_keepalive_connections=20, 
            max_connections=100,
            keepalive_expiry=30
        )
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        ]
    
    async def _apply_rate_limiting(self):
        """Apply rate limiting to avoid being blocked"""
        current_time = time.time()
        if hasattr(self, '_last_request_time'):
            time_diff = current_time - self._last_request_time
            if time_diff < settings.REQUEST_DELAY:
                await asyncio.sleep(settings.REQUEST_DELAY - time_diff)
        self._last_request_time = current_time
    
    async def get(
        self, 
        url: str, 
        params: Optional[Dict] = None, 
        headers: Optional[Dict] = None,
        follow_redirects: bool = True
    ) -> httpx.Response:
        await self._apply_rate_limiting()
        
        default_headers = {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        
        if headers:
            default_headers.update(headers)
        
        for attempt in range(settings.JAGRITI_MAX_RETRIES):
            try:
                async with httpx.AsyncClient(
                    timeout=self.timeout,
                    limits=self.limits,
                    follow_redirects=follow_redirects
                ) as client:
                    cookies = await self.session_manager.get_session_cookies(client)
                    
                    response = await client.get(
                        url, 
                        params=params, 
                        headers=default_headers,
                        cookies=cookies
                    )
                    
                    if response.cookies:
                        self.session_manager.session_cookies.update(dict(response.cookies))
                    
                    response.raise_for_status()
                    return response
                    
            except httpx.TimeoutException:
                if attempt == settings.JAGRITI_MAX_RETRIES - 1:
                    raise SearchTimeoutException(f"Request timed out after {settings.JAGRITI_MAX_RETRIES} attempts")
                await asyncio.sleep(settings.JAGRITI_BACKOFF_FACTOR * (2 ** attempt))
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:  # Rate limited
                    await asyncio.sleep(60)  # Wait 1 minute
                    continue
                elif e.response.status_code in [403, 401]:
                    self.session_manager.session_cookies = {}
                    continue
                else:
                    raise JagritiServiceException(f"HTTP error {e.response.status_code}: {e.response.text}")
                    
            except Exception as e:
                if attempt == settings.JAGRITI_MAX_RETRIES - 1:
                    raise JagritiServiceException(f"Request failed: {str(e)}")
                await asyncio.sleep(settings.JAGRITI_BACKOFF_FACTOR * (2 ** attempt))
    
    async def post(
        self, 
        url: str, 
        data: Optional[Dict] = None, 
        json: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> httpx.Response:
        await self._apply_rate_limiting()
        
        default_headers = {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/x-www-form-urlencoded" if data else "application/json",
            "Origin": settings.JAGRITI_BASE_URL,
            "Referer": settings.JAGRITI_BASE_URL,
        }
        
        if headers:
            default_headers.update(headers)
        
        for attempt in range(settings.JAGRITI_MAX_RETRIES):
            try:
                async with httpx.AsyncClient(
                    timeout=self.timeout,
                    limits=self.limits,
                    follow_redirects=True
                ) as client:
                    cookies = await self.session_manager.get_session_cookies(client)
                    
                    if self.session_manager.csrf_token and data:
                        data = data.copy()
                        data['csrf_token'] = self.session_manager.csrf_token
                    
                    response = await client.post(
                        url, 
                        data=data,
                        json=json,
                        headers=default_headers,
                        cookies=cookies
                    )
                    
                    if response.cookies:
                        self.session_manager.session_cookies.update(dict(response.cookies))
                    
                    response.raise_for_status()
                    return response
                    
            except Exception as e:
                if attempt == settings.JAGRITI_MAX_RETRIES - 1:
                    raise JagritiServiceException(f"POST request failed: {str(e)}")
                await asyncio.sleep(settings.JAGRITI_BACKOFF_FACTOR * (2 ** attempt))