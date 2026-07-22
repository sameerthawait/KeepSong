import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import logger
from app.routers import auth, patients, admin

sentry_dsn = settings.SENTRY_DSN or "https://8dd45f6ffaaa356eb3138bbbdc917bff@o4511669258813440.ingest.us.sentry.io/4511774397693952"

sentry_sdk.init(
    dsn=sentry_dsn,
    send_default_pii=True,
    integrations=[FastApiIntegration()],
    traces_sample_rate=1.0,
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set CORS origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include Routers
app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(admin.router)

@app.get("/health")
def health_check():
    return {"status": "healthy"}
