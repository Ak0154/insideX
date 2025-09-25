from fastapi import FastAPI
from pydantic import BaseModel
from .llm import analyze_stock   # ✅ centralized workflow

app = FastAPI()

class QueryRequest(BaseModel):
    stock: str


@app.post("/analyze")
def analyze(req: QueryRequest):
    """API endpoint: analyze a stock for anomalies/problems."""
    result = analyze_stock(req.stock)
    return result
