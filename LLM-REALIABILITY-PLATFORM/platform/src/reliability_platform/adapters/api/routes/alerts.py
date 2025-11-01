 from __future__ import annotations

 from typing import List

 from fastapi import APIRouter


 router = APIRouter()


 @router.get("/alerts")
 async def list_alerts() -> List[dict]:
     # Placeholder: wire to alert store later
     return []


