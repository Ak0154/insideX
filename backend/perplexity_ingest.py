import requests
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API")      # use uppercase in .env
PERPLEXITY_API_URL = os.getenv("PERPLEXITY_URL")

def search_perplexity(query: str) -> str:
    """
    Send a query to Perplexity API and return the analysis text.
    Also saves the response to a markdown file in /documents.
    """
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "sonar-reasoning-pro",
        "messages": [
            {
                "role": "system",
                "content": """You are a financial analyst AI assistant specialized in stock market analysis with a focus on anomaly detection...
                (system prompt truncated for clarity, keep full in your code)
                """
            },
            {"role": "user", "content": query}
        ]
    }

    try:
        response = requests.post(PERPLEXITY_API_URL, headers=headers, json=data, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ Perplexity API request failed: {e}")
        return None

    result = response.json()

    if "choices" not in result or not result["choices"]:
        print("❌ Invalid response from Perplexity API")
        return None

    response_text = result["choices"][0]["message"]["content"]
    print("✅ Response Generated from Perplexity")

    save_response_to_markdown(query, response_text)
    return response_text


def save_response_to_markdown(query: str, response_text: str):
    """
    Save Perplexity response into /documents as a Markdown file.
    """
    documents_folder = "documents"
    os.makedirs(documents_folder, exist_ok=True)

    safe_query = "".join(c for c in query if c.isalnum() or c in (" ", "-", "_")).rstrip()
    safe_query = safe_query.replace(" ", "_")
    if len(safe_query) > 50:
        safe_query = safe_query[:50]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{safe_query}_{timestamp}.md"
    filepath = os.path.join(documents_folder, filename)

    markdown_content = f"""# Stock Analysis Report

*Query:* {query}  
*Generated:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

{response_text}

---

This analysis was generated using AI and should not be considered as financial advice.
"""

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        print(f"📁 Saved analysis to: {filepath}")
    except Exception as e:
        print(f"❌ Error saving file: {e}")
        return None  # Explicitly return None on error


if __name__ == "__main__":
    query = input("Enter your stock analysis query: ")
    search_perplexity(query)
