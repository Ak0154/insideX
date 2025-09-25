import os
import requests
from dotenv import load_dotenv
from anthropic import Anthropic

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


def analyze_stock(stock: str):
    """Main entry: Try Perplexity first → always refine with Claude + Pathway context."""
    query = f"latest news and anomalies about {stock}"

    # Step 1: Try Perplexity
    analysis = analyze_with_perplexity(stock, query)

    # Step 2: Always refine with Claude (with or without Perplexity result)
    final_report = analyze_with_claude(stock, analysis or "")

    return {
        "stock": stock,
        "perplexity_analysis": analysis,
        "final_report": final_report,
    }
