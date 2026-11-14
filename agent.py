import os
import re
import time
from pathlib import Path

from google import genai
from tools import search_products, filter_by_requirements


# --------------------------------------------------
# 1. LOAD GEMINI API KEY
# --------------------------------------------------

def load_api_key():
    """Load the API key from the project's .env file."""

    env_path = Path(__file__).parent / ".env"

    if env_path.exists():
        for line in env_path.read_text(
            encoding="utf-8"
        ).splitlines():

            if line.startswith("GEMINI_API_KEY="):
                return (
                    line.split("=", 1)[1]
                    .strip()
                    .strip('"')
                    .strip("'")
                )

    return os.getenv("GEMINI_API_KEY")


# --------------------------------------------------
# 2. EXTRACT REQUIREMENTS FROM USER MESSAGE
# --------------------------------------------------

def extract_requirements(user_query):
    """Extract product category, budget, RAM and storage."""

    query = user_query.lower()

    requirements = {
        "category": None,
        "max_budget": None,
        "min_ram_gb": None,
        "min_storage_gb": None
    }

    # Detect product category.
    if any(word in query for word in [
        "laptop", "notebook"
    ]):
        requirements["category"] = "laptop"

    elif any(word in query for word in [
        "smartphone", "mobile", "phone"
    ]):
        requirements["category"] = "smartphone"

    elif any(word in query for word in [
        "headphone", "headphones", "earbuds",
        "earphones"
    ]):
        requirements["category"] = "headphones"

    # Extract budget.
    budget_match = re.search(
        r"(?:under|below|less than|within|maximum|max)"
        r"\s*(?:₹|rs\.?|inr)?\s*([\d,]+)",
        query
    )

    if budget_match:
        requirements["max_budget"] = float(
            budget_match.group(1).replace(",", "")
        )

    # Extract RAM.
    ram_match = re.search(
        r"(\d+)\s*gb\s*ram",
        query
    )

    if ram_match:
        requirements["min_ram_gb"] = int(
            ram_match.group(1)
        )

    # Extract storage.
    storage_match = re.search(
        r"(\d+(?:\.\d+)?)\s*(tb|gb)\s*"
        r"(?:ssd|storage)?",
        query
    )

    if storage_match:
        amount = float(storage_match.group(1))
        unit = storage_match.group(2)

        if unit == "tb":
            amount *= 1024

        requirements["min_storage_gb"] = int(amount)

    return requirements


# --------------------------------------------------
# 3. REMEMBER PREVIOUS REQUIREMENTS
# --------------------------------------------------

def get_active_requirements(
    user_query,
    conversation_history=None
):
    """Recover previous requirements and update new ones."""

    current = extract_requirements(user_query)

    history = conversation_history or []

    previous = {
        "category": None,
        "max_budget": None,
        "min_ram_gb": None,
        "min_storage_gb": None
    }

    # Find the latest previous user request
    # containing product requirements.
    for message in reversed(history):

        if message.get("role") != "user":
            continue

        extracted = extract_requirements(
            message.get("content", "")
        )

        if any(value is not None for value in extracted.values()):
            previous = extracted
            break

    # Update only the requirements mentioned
    # in the latest message.
    for key, value in current.items():

        if value is not None:
            previous[key] = value

    return previous


# --------------------------------------------------
# 4. PRODUCT SEARCH TOOL
# --------------------------------------------------

def find_matching_products(
    category: str,
    max_budget: float | None = None,
    min_ram_gb: int | None = None,
    min_storage_gb: int | None = None,
    purpose: str | None = None
):
    """
    Search the product catalogue using user requirements.

    Supported categories:
    laptop, smartphone, headphones
    """

    if category not in [
        "laptop",
        "smartphone",
        "headphones"
    ]:
        return []

    requirements = {
        "min_ram_gb": min_ram_gb,
        "min_storage_gb": min_storage_gb
    }

    requirements = {
        key: value
        for key, value in requirements.items()
        if value is not None
    }

    print("\nTOOL CALLED WITH:")

    print({
        "category": category,
        "max_budget": max_budget,
        "min_ram_gb": min_ram_gb,
        "min_storage_gb": min_storage_gb,
        "purpose": purpose
    })

    # Search by category and budget.
    products = search_products(
        category=category,
        max_budget=max_budget,
        in_stock_only=False
    )

    # Apply RAM and storage requirements.
    matches = filter_by_requirements(
        products,
        requirements
    )

    print(
        "MATCHING PRODUCTS:",
        [product["name"] for product in matches]
    )

    return matches


# --------------------------------------------------
# 5. GEMINI AI RESPONSE
# --------------------------------------------------

def get_gemini_response(
    user_query,
    conversation_history=None
):
    """Generate responses using Gemini and product-search tool."""

    api_key = load_api_key()

    if not api_key:
        return (
            "Gemini API key not found. "
            "Please check your .env file."
        )

    try:

        client = genai.Client(api_key=api_key)

        history = conversation_history or []

        # Recover previous requirements.
        active_requirements = get_active_requirements(
            user_query,
            history
        )

        # Prepare previous conversation.
        history_text = ""

        for message in history:

            role = message.get("role", "user").upper()

            content = message.get("content", "")

            history_text += (
                f"\n{role}: {content}\n"
            )

        prompt = f"""
You are Shopping Assist AI, an intelligent shopping assistant.

Your job is to help customers search, compare and select
products from our product catalogue.

PREVIOUS CONVERSATION:
{history_text}

ACTIVE CUSTOMER REQUIREMENTS:
{active_requirements}

LATEST CUSTOMER MESSAGE:
{user_query}


PRODUCT SEARCH RULES:

1. When the customer asks to find or recommend products,
   you MUST call find_matching_products.

2. Use only these exact categories:
   laptop, smartphone, headphones.

3. Extract the maximum budget in INR.

4. Extract minimum RAM in GB.
   Example: 8GB RAM means 8.

5. Extract minimum storage in GB.
   Example: 128GB means 128.
   Example: 1TB means 1024.

6. Use the active requirements when the customer gives
   a follow-up request.

7. Recommend only products returned by the tool.

8. Never invent product specifications or prices.

9. If no products match, clearly say that no exact matches
   were found.

10. If the customer requests exact matches only,
    do not recommend alternatives.

11. Do not claim a product matches unless all stated
    requirements are satisfied.


COMPARISON RULES:

1. Compare only products from the catalogue or conversation.

2. Use a Markdown table for comparisons.

3. Include price, processor, RAM, storage, display
   and rating when available.

4. Calculate price differences accurately.

5. Clearly mention unavailable information.

6. Do not assume processor performance without evidence.

7. When asked which product is better, explain the choice
   using the customer's requirements.


CONVERSATION RULES:

1. Understand follow-up questions using conversation history.

2. Recognize references such as:
   "the first laptop", "the cheaper one", and "both products".

3. Do not ask the customer to repeat known requirements.

4. If a follow-up requires a new product search,
   call the product-search tool again.

5. Keep answers clear, accurate and useful.

Your recommendations must be based on catalogue data.
"""

        # Retry temporarily unavailable Gemini requests.
        for attempt in range(3):

            try:

                print("\nConnecting to Gemini...")

                chat = client.chats.create(
                    model="gemini-3.5-flash-lite",
                    config={
                        "tools": [
                            find_matching_products
                        ]
                    }
                )

                response = chat.send_message(prompt)

                if response.text:
                    return response.text

                return (
                    "Gemini returned an empty response. "
                    "Please try again."
                )

            except Exception as e:

                error = str(e)

                if (
                    "503" in error
                    or "UNAVAILABLE" in error
                ):

                    if attempt < 2:

                        wait_time = 2 ** (attempt + 1)

                        print(
                            f"Gemini is busy. "
                            f"Retrying in {wait_time} seconds..."
                        )

                        time.sleep(wait_time)

                    else:

                        return (
                            "Gemini is temporarily unavailable "
                            "after 3 attempts. Please try again later."
                        )

                else:

                    return f"Gemini API Error: {e}"

    except Exception as e:

        return f"Application Error: {e}"


# --------------------------------------------------
# 6. RUN AGENT DIRECTLY FROM TERMINAL
# --------------------------------------------------

if __name__ == "__main__":

    print("=" * 45)
    print("          SHOPPING ASSIST AI")
    print("=" * 45)

    query = input(
        "\nWhat are you looking for? "
    )

    if query.strip():

        answer = get_gemini_response(query)

        print("\nSHOPPING ASSISTANT:")
        print("=" * 45)

        print(answer)

    else:

        print("Please enter a valid shopping request.")