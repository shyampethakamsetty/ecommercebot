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

# Website category structure extracted from DOM
WEBSITE_CATEGORIES = {
    "computers": {
        "path": "/computers",
        "subcategories": {
            "desktops": "/desktops",
            "notebooks": "/notebooks", 
            "laptops": "/notebooks",
            "software": "/software"
        }
    },
    "electronics": {
        "path": "/electronics", 
        "subcategories": {
            "camera": "/camera-photo",
            "photo": "/camera-photo",
            "cellphone": "/cell-phones",
            "phone": "/cell-phones",
            "mobile": "/cell-phones",
            "others": "/others"
        }
    },
    "apparel": {
        "path": "/apparel",
        "subcategories": {
            "shoes": "/shoes",
            "clothing": "/clothing", 
            "accessories": "/accessories"
        }
    },
    "books": {"path": "/books"},
    "jewelry": {"path": "/jewelry"},
    "digital-downloads": {"path": "/digital-downloads"},
    "gift-cards": {"path": "/gift-cards"}
}

def get_enhanced_llm_prompt(user_query: str) -> str:
    """Generate enhanced LLM prompt for intelligent parsing"""
    return f"""
You are an intelligent e-commerce assistant. Parse the user query and extract structured information.

Available categories: {json.dumps(WEBSITE_CATEGORIES)}

User Query: "{user_query}"

Extract the following information and respond in EXACT JSON format:

{{
    "intent": "search|add_to_cart|checkout",
    "category": "exact_category_path_from_list_or_empty",
    "subcategory": "exact_subcategory_path_or_empty", 
    "filters": {{
        "min_price": null_or_number,
        "max_price": null_or_number,
        "query": "original_or_cleaned_search_terms"
    }},
    "action": "search|add_to_cart|checkout",
    "safe": true_if_checkout_or_purchase_intent
}}

PRICE FILTER RULES:
- "under X", "below X", "less than X" → min_price: null, max_price: X
- "over X", "above X", "more than X" → min_price: X, max_price: null  
- "between X and Y", "from X to Y" → min_price: X, max_price: Y

CATEGORY MAPPING:
Map user terms to exact paths from the categories list. For example:
- "books" → "/books"
- "cellphone", "phone", "mobile" → "/cell-phones" 
- "laptop", "notebook" → "/notebooks"
- "desktop", "computer" → "/desktops"

INTENT RULES:
- "search", "find", "show", "get" → intent: "search", action: "search"
- "add to cart", "add cart" → intent: "add_to_cart", action: "add_to_cart"  
- "buy", "purchase", "checkout" → intent: "checkout", action: "checkout", safe: true

Examples:
"search for books under 20 dollars" → {{"intent": "search", "category": "/books", "filters": {{"min_price": null, "max_price": 20, "query": "books"}}, "action": "search"}}
"find cellphone over 800" → {{"intent": "search", "category": "/cell-phones", "filters": {{"min_price": 800, "max_price": null, "query": "cellphone"}}, "action": "search"}}
"laptops between 500 and 1000" → {{"intent": "search", "category": "/notebooks", "filters": {{"min_price": 500, "max_price": 1000, "query": "laptops"}}, "action": "search"}}
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
    prompt = get_enhanced_llm_prompt(user_text)
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
    # Enhanced rule-based fallback using website category structure
    text = user_text.lower()
    
    result = {
        "intent": "search",
        "category": "",
        "subcategory": "",
        "filters": {
            "max_price": None,
            "min_price": None,
            "query": user_text
        },
        "action": "search",
        "safe": False
    }
    
    # Intent recognition
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

    # Category mapping using website structure
    category_keywords = {
        # Electronics
        "phone": ("/electronics", "/cell-phones"),
        "mobile": ("/electronics", "/cell-phones"),
        "smartphone": ("/electronics", "/cell-phones"),
        "cellphone": ("/electronics", "/cell-phones"),
        "camera": ("/electronics", "/camera-photo"),
        "photo": ("/electronics", "/camera-photo"),
        
        # Computers
        "laptop": ("/computers", "/notebooks"),
        "notebook": ("/computers", "/notebooks"),
        "desktop": ("/computers", "/desktops"),
        "computer": ("/computers", ""),
        "software": ("/computers", "/software"),
        
        # Apparel
        "shoes": ("/apparel", "/shoes"),
        "clothing": ("/apparel", "/clothing"),
        "clothes": ("/apparel", "/clothing"),
        "accessories": ("/apparel", "/accessories"),
        
        # Direct categories
        "book": ("/books", ""),
        "jewelry": ("/jewelry", ""),
        "jewellery": ("/jewelry", ""),
        "gift card": ("/gift-cards", ""),
        "digital": ("/digital-downloads", ""),
    }
    
    for keyword, (category, subcategory) in category_keywords.items():
        if keyword in text:
            result["category"] = category
            result["subcategory"] = subcategory
            break
    
    # Price extraction with enhanced logic for three filter types
    import re
    
    # Extract prices for different filter types
    min_price = None
    max_price = None
    
    # BELOW filter: "under X", "below X", "less than X"
    below_match = re.search(r'(?:under|below|less than|max)\s*\$?(\d+)', text)
    if below_match:
        max_price = int(below_match.group(1))
    
    # ABOVE filter: "over X", "above X", "more than X", "minimum X"  
    above_match = re.search(r'(?:over|above|more than|minimum|min)\s*\$?(\d+)', text)
    if above_match and not below_match:  # Don't override if we already found a below filter
        min_price = int(above_match.group(1))
    
    # BETWEEN filter: "between X and Y", "from X to Y", "X to Y"
    between_match = re.search(r'(?:between|from)\s*\$?(\d+)(?:\s*(?:and|to)\s*\$?(\d+))', text)
    if between_match:
        min_price = int(between_match.group(1))
        max_price = int(between_match.group(2))
    
    # Range with dash: "X-Y", "$X-$Y"
    range_match = re.search(r'\$?(\d+)\s*-\s*\$?(\d+)', text)
    if range_match and not between_match:
        min_price = int(range_match.group(1))
        max_price = int(range_match.group(2))
    
    result["filters"] = {
        "max_price": max_price,
        "min_price": min_price,
        "query": user_text
    }

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