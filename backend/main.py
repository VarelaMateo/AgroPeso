from fastapi import FastAPI
import models
from routers.ticket_router import router as ticket_router

app = FastAPI(title="AgroPeso")
app.include_router(ticket_router)

