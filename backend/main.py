import asyncio
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import models
from routers import ticket_router, supplier_router, product_router, user_router, auth_router, backup_router, factura_router
from utils.backup_automatico import respaldo_diario

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Respaldo silencioso: al arrancar y después cada hora, si falta el backup del día, se genera
    tarea = asyncio.create_task(respaldo_diario())
    yield
    tarea.cancel()


app = FastAPI(title="AgroPeso", lifespan=lifespan)

origins = [ o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5500").split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],  # para que el navegador lea el nombre del backup
)

app.include_router(ticket_router.router)
app.include_router(supplier_router.router)
app.include_router(product_router.router)
app.include_router(user_router.router)
app.include_router(auth_router.router)
app.include_router(backup_router.router)
app.include_router(factura_router.router)
