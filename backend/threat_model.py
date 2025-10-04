# backend/threat_model.py
from .vector_store import search
from anthropic import Anthropic
import os
import re

anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def evaluate_threat(stock: str, anomalies: str):
    """
    Given Claude’s anomalies, retrieve past events and output a numeric threat score 0-10.
    Returns {score: int, reason: str}
    """
    # Step 1: Retrieve past related events from Pathway
    retrieved = search(anomalies, k=5)
    context = "\n".join([f"- {r[1]}" for r in retrieved])

    # Step 2: Ask Claude for threat score
    prompt = f"""
    Stock: {stock}
    Current anomalies:
    {anomalies}

    Past related events:
    {context}

    Based on these, assign a THREAT LEVEL SCORE from 0 (no threat) to 10 (very high threat).
    Provide output in this format only:
    Score: X
    Reason: <short one-line explanation>
    """

    try:
        response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=150,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )

        text = response.content[0].text.strip()

        # Parse out the score
        match = re.search(r"Score:\s*(\d+)", text)
        score = int(match.group(1)) if match else None

        # Extract reason
        reason_match = re.search(r"Reason:\s*(.*)", text)
        reason = reason_match.group(1).strip() if reason_match else "No reason provided."

        return {"score": score, "reason": reason}

    except Exception as e:
        return {"score": None, "reason": f"Error scoring threat: {e}"}
