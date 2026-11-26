from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.config import settings
from shared.schemas import HealthResponse, now_wib_iso

from app.assets.router import router as assets_router
from app.catalog.router import router as catalog_router
from app.core.errors import install_error_handlers
from app.core.events import events_router
from app.core.outbox import relay_lifespan
from app.procurement.router import router as procurement_router
from app.stock.router import router as stock_router

# Impor ini mendaftarkan handler event dan port tiap slice.
from app.assets import events as _assets_events  # noqa: F401
from app.catalog import events as _catalog_events  # noqa: F401
from app.procurement import events as _procurement_events  # noqa: F401
from app.stock import events as _stock_events  # noqa: F401

app = FastAPI(title="TelcoNusa SCM API", version="1.0.0", lifespan=relay_lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
install_error_handlers(app)

app.include_router(events_router)
app.include_router(stock_router)
app.include_router(procurement_router)
app.include_router(assets_router)
app.include_router(catalog_router)


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(service="scm-api", transport=settings.EVENT_TRANSPORT, timestamp=now_wib_iso())
