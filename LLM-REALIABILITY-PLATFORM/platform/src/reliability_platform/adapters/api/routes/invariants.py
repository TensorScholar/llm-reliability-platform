 from __future__ import annotations

 from typing import Dict, List, Optional

 from fastapi import APIRouter, HTTPException
 from pydantic import BaseModel

 from ....domain.models.invariant import InvariantConfig, InvariantCategory, InvariantRegistry


 router = APIRouter()
 _registry = InvariantRegistry()


 class InvariantUpsert(BaseModel):
     id: str
     name: str
     description: str
     category: InvariantCategory | str = InvariantCategory.CUSTOM
     enabled: bool = True
     severity: str = "medium"
     config: dict = {}


 @router.get("/invariants")
 async def list_invariants() -> List[Dict[str, str]]:
     return [
         {
             "id": inv.metadata.id,
             "name": inv.metadata.name,
             "category": inv.metadata.category.value,
             "enabled": inv.config.enabled,
         }
         for inv in _registry.get_all()
     ]


 @router.post("/invariants")
 async def create_invariant(payload: InvariantUpsert):
     # Placeholder: real system would map to concrete invariant classes
     # Here we reject because dynamic creation isn't wired
     raise HTTPException(status_code=501, detail="Dynamic invariant creation not implemented")


 @router.put("/invariants/{invariant_id}")
 async def update_invariant(invariant_id: str, payload: InvariantUpsert):
     inv = _registry.get(invariant_id)
     if not inv:
         raise HTTPException(status_code=404, detail="Invariant not found")
     inv.config.enabled = payload.enabled  # type: ignore[misc]
     return {"status": "updated"}


 @router.delete("/invariants/{invariant_id}")
 async def delete_invariant(invariant_id: str):
     _registry.unregister(invariant_id)
     return {"status": "deleted"}


