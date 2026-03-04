from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import os

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <h1>Sistema Restaurante 🍽️</h1>
    <p>Servidor funcionando correctamente.</p>
    """

@app.get("/cocina", response_class=HTMLResponse)
def cocina():
    return """
    <h1>Vista Cocina 👩‍🍳</h1>
    <p>Aquí llegarán los pedidos.</p>
    """