from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.db.base import Base
from app.db.session import engine
from app.api.routes import router as api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables if they do not exist at startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Dispose of engine connection pool on shutdown
    await engine.dispose()

app = FastAPI(title="Ticket Router Agent", lifespan=lifespan)

app.include_router(api_router)
