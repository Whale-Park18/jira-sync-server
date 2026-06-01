from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routers import api, pages


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(pages.router)
app.include_router(api.router)
