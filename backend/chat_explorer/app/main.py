from fastapi import FastAPI

from backend.common.settings import get_settings
from .api.router import router as api_router

app = FastAPI(title="NE Navi – Chat Log Explorer")
app.include_router(api_router)


@app.get("/health")
def health():
    settings = get_settings()
    return {"status": "ok", "db": str(settings.database_url)}