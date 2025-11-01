 from __future__ import annotations

 import uvicorn

 from .adapters.api.app import create_app
 from .config import get_settings


 settings = get_settings()
 app = create_app(settings)


 if __name__ == "__main__":
     uvicorn.run("reliability_platform.main:app", host=settings.api.host, port=settings.api.port, reload=True)


