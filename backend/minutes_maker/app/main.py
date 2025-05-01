from fastapi import FastAPI

from .api.files_router import router as files_router
from .api.transcripts_router import router as tr_router
from .api.draft_router import router as draft_router
from .api.minutes_versions_router import router as mv_router
from .api.stt_router import router as stt_router
from .api.jobs_router import router as jobs_router
from .api.agent_router import router as agent_router
from .api.minutes_chat_router import router as mc_router   # ★ 追加
from .api.diff_router import router as diff_router   # ★ 追加
from common.security import fastapi_users, auth_backend  # :contentReference[oaicite:6]{index=6}
from common.schemas import UserRead, UserCreate  # :contentReference[oaicite:7]{index=7}
        #

app = FastAPI(title="NE Navi – Minutes Maker")


# ---- Auth routers ---------------------------------------------------
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserCreate),
    prefix="/users",
    tags=["auth"],
)

@app.get("/health")
def health():
    return {"status": "ok"}


# ---- API routers -----------------------------------------------------------
app.include_router(files_router)
app.include_router(jobs_router)
app.include_router(stt_router)
app.include_router(tr_router)
app.include_router(draft_router)
app.include_router(mv_router)
app.include_router(agent_router)
app.include_router(mc_router)                     # ★ 追加
app.include_router(diff_router)