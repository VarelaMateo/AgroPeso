import asyncio
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
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


# Railway define estas variables en sus servidores: así se sabe que es producción sin configurar nada
EN_PRODUCCION = any(os.getenv(v) for v in ("RAILWAY_ENVIRONMENT_NAME", "RAILWAY_ENVIRONMENT"))
# /docs y /openapi.json describen toda la API: en producción se ocultan salvo DOCS_HABILITADOS=true
DOCS = os.getenv("DOCS_HABILITADOS", "false" if EN_PRODUCCION else "true").lower() == "true"

app = FastAPI(
    title="AgroPeso",
    lifespan=lifespan,
    docs_url="/docs" if DOCS else None,
    redoc_url="/redoc" if DOCS else None,
    openapi_url="/openapi.json" if DOCS else None,
)

origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5500").split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,  # el token viaja en el header Authorization, no en cookies
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["Content-Disposition"],  # para que el navegador lea el nombre del backup
)


@app.middleware("http")
async def cabeceras_de_seguridad(request: Request, call_next):
    respuesta = await call_next(request)
    respuesta.headers.setdefault("X-Content-Type-Options", "nosniff")
    respuesta.headers.setdefault("X-Frame-Options", "DENY")
    respuesta.headers.setdefault("Referrer-Policy", "no-referrer")
    # Las respuestas tienen datos privados (tokens, pesadas, el backup): que no queden en cachés
    respuesta.headers.setdefault("Cache-Control", "no-store")
    if EN_PRODUCCION:
        respuesta.headers.setdefault("Strict-Transport-Security", "max-age=31536000")
    return respuesta

app.include_router(ticket_router.router)
app.include_router(supplier_router.router)
app.include_router(product_router.router)
app.include_router(user_router.router)
app.include_router(auth_router.router)
app.include_router(backup_router.router)
app.include_router(factura_router.router)
