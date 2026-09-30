# Punto de entrada de la API del Hub: crea la app de FastAPI (los routers y /health llegan en la T03).
from fastapi import FastAPI

app = FastAPI(title="CloudOps Client Hub")
