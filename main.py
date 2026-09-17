from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

import chat, admin

app = FastAPI(title="Chatbot SDK API")

# TODO: en producción, restringir a los dominios registrados de cada chatbot
# (ver sección de Seguridad en contexto.md). Por ahora, abierto para desarrollo.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api")
app.include_router(admin.router, prefix="/api/admin")


@app.get("/")
def health_check():
    return {"status": "ok"}


# Correr con: uvicorn main:app --reload --port 8000