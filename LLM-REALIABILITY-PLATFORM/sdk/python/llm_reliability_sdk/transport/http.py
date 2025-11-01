 from __future__ import annotations

 from typing import Any, Dict, List, Optional

 import httpx


 class HTTPTransport:
     def __init__(self, api_url: str, api_key: Optional[str], timeout: float = 5.0) -> None:
         self.api_url = api_url.rstrip("/")
         self.api_key = api_key
         self.timeout = timeout
         self._client = httpx.AsyncClient(timeout=timeout)

     async def close(self) -> None:
         await self._client.aclose()

     async def send_capture(self, event: Dict[str, Any]) -> bool:
         headers = {"Content-Type": "application/json"}
         if self.api_key:
             headers["Authorization"] = f"Bearer {self.api_key}"
         resp = await self._client.post(f"{self.api_url}/api/v1/captures", json=event, headers=headers)
         return resp.status_code in (200, 201)

     async def send_batch(self, events: List[Dict[str, Any]]) -> bool:
         headers = {"Content-Type": "application/json"}
         if self.api_key:
             headers["Authorization"] = f"Bearer {self.api_key}"
         resp = await self._client.post(
             f"{self.api_url}/api/v1/captures/batch", json=events, headers=headers
         )
         return resp.status_code in (200, 201)


