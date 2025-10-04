from fastapi import FastAPI
from pydantic import BaseModel
from .llm import analyze_stock 
from .llm import analyze_stock, ask_followup  # ✅ centralized workflow

app = FastAPI()

class QueryRequest(BaseModel):
    stock: str

class FollowupRequest(BaseModel):
    stock: str
    question: str
    previous_report: dict | None = None


@app.post("/analyze")
def analyze(req: QueryRequest):
    """API endpoint: analyze a stock for anomalies/problems."""
    result = analyze_stock(req.stock)
    return result
@app.post("/followup")
def followup(req: FollowupRequest):
    """Ask follow-up questions after the initial analysis."""
    answer = ask_followup(req.stock, req.question, req.previous_report)
    return {
        "stock": req.stock,
        "question": req.question,
        "answer": answer,
    }