import os
import requests
from dotenv import load_dotenv
from anthropic import Anthropic
from .vector_store import add_document, search, preload_from_mongo
from .db import save_news, get_news
from .threat_model import evaluate_threat
from .vector_store import add_document, store_full_doc
from .vector_store import add_document, search, store_full_doc, preload_from_local
# ✅ Pathway vector store
from .vector_store import add_document, search  

load_dotenv()

# Load API keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
PERPLEXITY_API_KEY = os.getenv("perplexity_api")
PERPLEXITY_API_URL = os.getenv("perplexity_url")  # e.g. https://api.perplexity.ai/chat/completions

anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)


def analyze_with_perplexity(stock: str, query: str, timeout: int = 90):
    """Query Perplexity API for anomaly-related stock info (short + source links)."""
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "sonar-reasoning-pro",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a financial anomaly detector. "
                    "State clearly if anomalies/problems exist or not. "
                    "Be concise, provide links to credible sources. "
                    "Return facts, not long explanations."
                ),
            },
            {"role": "user", "content": query},
        ]
    }

    try:
        response = requests.post(
            PERPLEXITY_API_URL,
            headers=headers,
            json=data,
            timeout=timeout
        )
        response.raise_for_status()
        result = response.json()
        analysis = result["choices"][0]["message"]["content"]

        # ✅ Store into Pathway memory
        add_document(stock, analysis)

        # ✅ Store full raw JSON locally
        try:
            from .vector_store import store_full_doc
            store_full_doc(stock, result)
        except Exception as e:
            print(f"⚠️ Failed to save local JSON doc: {e}")

        # ✅ Store into MongoDB
        try:
            from .db import save_news  # helper function we’ll define
            save_news(stock, analysis, result)
        except Exception as e:
            print(f"⚠️ Failed to save to MongoDB: {e}")

        return analysis

    except (requests.exceptions.Timeout, requests.exceptions.ReadTimeout):
        print("⚠️ Perplexity request timed out. Falling back to Claude.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Perplexity API request failed: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error with Perplexity: {e}")
        return None


def analyze_with_claude(stock: str, analysis: str = ""):
    """Claude refines analysis using Pathway context + Perplexity result."""
    # ✅ Retrieve relevant context from Pathway
    neighbors = search(stock, k=5)
    context = "\n".join(str(n) for n in neighbors)

    query = f"""
    Stock: {stock}
    Perplexity Analysis: {analysis}
    Pathway Context (memory): {context}

    Return exactly 5 bullet points. 
    Each bullet = one anomaly/problem (or state 'No anomaly found'). 
    Each must include a credible source link. 
    Do not add extra explanation outside the bullet list.
    """

    try:
        response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=400,
            temperature=0.2,
            system="You are an anomaly detector for stock news. Always return 5 bullet points with sources.",
            messages=[{"role": "user", "content": query}]
        )
        return response.content[0].text
    except Exception as e:
        print(f"❌ Claude API request failed: {e}")
        return "Error: Could not analyze query."


# backend/llm.py
import os
import requests
from dotenv import load_dotenv
from anthropic import Anthropic

# Pathway memory + helper functions
from .vector_store import add_document, search, preload_from_mongo

# Threat model that returns {"score": int, "reason": str}
from .threat_model import evaluate_threat

load_dotenv()

# Load API keys & URLs
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
PERPLEXITY_API_KEY = os.getenv("perplexity_api")
PERPLEXITY_API_URL = os.getenv("perplexity_url")  # e.g. https://api.perplexity.ai/chat/completions

anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)


def analyze_with_perplexity(stock: str, query: str, timeout: int = 90):
    """Query Perplexity API for anomaly-related stock info (short + source links)."""
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "sonar-reasoning-pro",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a financial anomaly detector. "
                    "State clearly if anomalies/problems exist or not. "
                    "Be concise, provide links to credible sources. "
                    "Return facts, not long explanations."
                ),
            },
            {"role": "user", "content": query},
        ]
    }

    try:
        response = requests.post(
            PERPLEXITY_API_URL,
            headers=headers,
            json=data,
            timeout=timeout
        )
        response.raise_for_status()
        result = response.json()

        # ✅ Extract short analysis text
        analysis = result["choices"][0]["message"]["content"]

        # ✅ Save full raw Perplexity response locally
        try:
            store_full_doc(stock, result)   # <- new function in vector_store.py
        except Exception as e:
            print(f"⚠️ Failed to save raw doc locally: {e}")

        # ✅ Store into Pathway memory + Mongo
        try:
            add_document(stock, analysis)
        except Exception as e:
            print(f"⚠️ Failed to add doc to Pathway/Mongo: {e}")

        return analysis

    except (requests.exceptions.Timeout, requests.exceptions.ReadTimeout):
        print("⚠️ Perplexity request timed out. Falling back to Claude.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Perplexity API request failed: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error with Perplexity: {e}")
        return None



def analyze_with_claude(stock: str, analysis: str = ""):
    """Claude refines analysis using Pathway context + Perplexity result."""
    # Retrieve relevant context from Pathway (safe if search fails)
    try:
        neighbors = search(stock, k=5)
    except Exception:
        neighbors = []

    context = "\n".join(str(n) for n in neighbors)

    query = f"""
Stock: {stock}
Perplexity Analysis: {analysis}
Pathway Context (memory): {context}

Return exactly 5 bullet points.
Each bullet = one anomaly/problem (or state 'No anomaly found').
Each must include a credible source link.
Do not add extra explanation outside the bullet list.
"""

    try:
        response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=400,
            temperature=0.2,
            system="You are an anomaly detector for stock news. Always return 5 bullet points with sources.",
            messages=[{"role": "user", "content": query}]
        )
        # response.content[0].text is the assistant output
        return response.content[0].text
    except Exception as e:
        print(f"❌ Claude API request failed: {e}")
        return "Error: Could not analyze query."


def analyze_stock(stock: str):
    """
    Main entry: Try Perplexity first → always refine with Claude + Pathway context,
    then compute threat score (0-10) with reason.
    Returns dict with keys: stock, perplexity_analysis, final_report, threat_score, threat_reason
    """
    query = f"latest news and anomalies about {stock}"

    # Try to preload recent documents into Pathway (optional; won't raise if missing)
    try:
        preload_from_mongo(stock, limit=20)
    except Exception:
        pass

    # Step 1: Try Perplexity
    analysis = analyze_with_perplexity(stock, query)

    # Step 2: Always refine with Claude (with or without Perplexity result)
    final_report = analyze_with_claude(stock, analysis or "")

    # Step 3: Threat scoring (returns {"score": int, "reason": str} or error structure)
    try:
        threat_result = evaluate_threat(stock, final_report)
        threat_score = threat_result.get("score")
        threat_reason = threat_result.get("reason")
    except Exception as e:
        threat_score = None
        threat_reason = f"Error computing threat: {e}"

    return {
        "stock": stock,
        "perplexity_analysis": analysis,
        "final_report": final_report,
        "threat_score": threat_score,
        "threat_reason": threat_reason,
    }

def ask_followup(stock: str, user_question: str, previous_report: dict = None):
    """
    Ask a follow-up question to Claude about a stock, using previous analysis + memory context.
    `previous_report` should ideally be the dict returned from analyze_stock(stock).
    """
    try:
        # Retrieve memory context
        neighbors = search(stock, k=5)
    except Exception:
        neighbors = []

    memory_context = "\n".join(str(n) for n in neighbors)

    # If previous report not passed, build a minimal one
    previous_report = previous_report or {}

    # Build the query prompt
    query = f"""
Stock: {stock}

Previous analysis:
- Perplexity: {previous_report.get("perplexity_analysis")}
- Final Report: {previous_report.get("final_report")}
- Threat Score: {previous_report.get("threat_score")}
- Threat Reason: {previous_report.get("threat_reason")}

Memory Context from Pathway:
{memory_context}

User Question: {user_question}

Answer clearly and concisely. 
If it's about market metrics (like all-time high), answer directly.
If it's anomaly-related, use the provided context and cite sources if possible.
"""

    try:
        response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=400,
            temperature=0.3,
            system="You are a financial assistant. Always answer clearly and concisely with context if available.",
            messages=[{"role": "user", "content": query}]
        )
        return response.content[0].text
    except Exception as e:
        print(f"❌ Claude follow-up failed: {e}")
        return "Error: Could not answer follow-up question."