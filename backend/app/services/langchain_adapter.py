import os, json, re
from typing import Dict, Any
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", None)

# Try to import LangChain/OpenAI
try:
    from langchain import OpenAI
    from langchain.prompts import PromptTemplate
    from langchain.schema import LLMResult
    LANGCHAIN_AVAILABLE = True
except Exception:
    LANGCHAIN_AVAILABLE = False

PROMPT_TEMPLATE = """You are a helpful assistant that extracts a structured JSON object
from a user's shopping automation request. Return ONLY valid JSON with these fields:
- intent: one of ["search", "checkout", "add_to_cart", "monitor"]
- category: product category or empty string (e.g., "jewelry", "phones")
- filters: a JSON object of optional filters, e.g. {"max_price": 100}
- action: the workflow action to run (e.g., "search", "checkout")
- safe: boolean whether the action requires confirmation (true for checkout)

Examples:
User: "get me all jewelery under 100 dollars"
Output:
{"intent":"search","category":"jewelry","filters":{"max_price":100},"action":"search","safe":false}

User: "checkout phones under 500 dollars"
Output:
{"intent":"checkout","category":"phones","filters":{"max_price":500},"action":"checkout","safe":true}

Now parse the user input and produce the JSON. Only output the JSON object. If a field is unknown, use empty string or empty object or false as appropriate.
User: {user_text}
"""

def _clean_json_like(text: str) -> str:
    # Find first { and last } to extract JSON-ish substring
    s = text.strip()
    i = s.find('{')
    j = s.rfind('}')
    if i != -1 and j != -1 and j > i:
        return s[i:j+1]
    # fallback: try to find lines that look like key: value and build minimal JSON
    return s

def parse_with_openai(user_text: str) -> Dict[str, Any]:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not set")
    if not LANGCHAIN_AVAILABLE:
        raise RuntimeError("langchain package not available")
    prompt = PROMPT_TEMPLATE.format(user_text=user_text)
    llm = OpenAI(openai_api_key=OPENAI_API_KEY, temperature=0)
    resp = llm(prompt)
    text = resp.strip()
    json_text = _clean_json_like(text)
    try:
        return json.loads(json_text)
    except Exception:
        # try to be forgiving: replace single quotes with double quotes
        try:
            return json.loads(json_text.replace("'", '"'))
        except Exception as e:
            raise ValueError(f"Failed to parse LLM output as JSON: {e}\
Output was:\
{text}") from e

def parse_with_fallback(user_text: str) -> Dict[str, Any]:
    # Simple rule-based fallback (kept from previous implementation)
    text = user_text.lower()
    result = {
        "intent": "search",
        "category": "",
        "filters": {},
        "action": "search",
        "safe": False
    }
    if any(w in text for w in ["checkout", "buy", "purchase", "order"]):
        result["intent"] = "checkout"
        result["action"] = "checkout"
        result["safe"] = True
    elif any(w in text for w in ["add to cart", "addtocart", "add cart", "add"]):
        result["intent"] = "add_to_cart"
        result["action"] = "add_to_cart"
    elif any(w in text for w in ["monitor", "watch", "track"]):
        result["intent"] = "monitor"
        result["action"] = "monitor"
    else:
        result["intent"] = "search"
        result["action"] = "search"

    categories = {
        "jewel": "jewelry",
        "jewellery": "jewelry",
        "jewelry": "jewelry",
        "phone": "phones",
        "phones": "phones",
        "mobile": "phones",
        "smartphone": "phones",
        "book": "books",
        "laptop": "laptops",
        "headphone": "audio",
        "headphones": "audio",
    }
    for k,v in categories.items():
        if k in text:
            result["category"] = v
            break

    import re
    m = re.search(r"under\s+\$?(\d+)", text)
    if not m:
        m = re.search(r"<\s*\$?(\d+)", text)
    if m:
        try:
            result["filters"]["max_price"] = int(m.group(1))
        except:
            pass
    else:
        m = re.search(r"(\d+)\s*(dollar|usd|rs|₹)", text)
        if m:
            try:
                result["filters"]["max_price"] = int(m.group(1))
            except:
                pass

    return result

def parse_with_fallback_only(user_text: str) -> Dict[str, Any]:
    return parse_with_fallback(user_text)

def parse(user_text: str, prefer_llm: bool = True) -> Dict[str, Any]:
    """Main entrypoint: try LLM parsing if available, fall back to rules otherwise."""
    if prefer_llm and LANGCHAIN_AVAILABLE and OPENAI_API_KEY:
        try:
            return parse_with_openai(user_text)
        except Exception as e:
            # log or ignore - fall back to rules
            # print('LLM parse failed:', e)
            return parse_with_fallback(user_text)
    else:
        return parse_with_fallback(user_text)