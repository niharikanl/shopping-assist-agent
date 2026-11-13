import os
import json
import time
from pathlib import Path
from google import genai
from tools import search_products, filter_by_requirements


def load_api_key():
    """Load Gemini API key from .env file."""

    env_path = Path(__file__).parent / ".env"

    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("GEMINI_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")

    return os.getenv("GEMINI_API_KEY")


def find_matching_products(requirements: dict):
    """Find products matching the customer's specifications."""

    print("TOOL CALLED WITH:", requirements)

    products = search_products(in_stock_only=False)

    matches = filter_by_requirements(products, requirements)

    print("MATCHING PRODUCTS:", [p.get("name") for p in matches])

    return matches


def get_gemini_response(user_query, conversation_history=None):
    """Generate recommendations using Gemini and previous conversation context."""

    api_key = load_api_key()

    if not api_key:
        return "Error: Gemini API key not found. Check your .env file."

    try:
        client = genai.Client(api_key=api_key)

        # Convert previous messages into readable conversation context.
        history_text = ""

        if conversation_history:
            history_text = "\nPREVIOUS CONVERSATION:\n"

            for message in conversation_history:
                role = message.get("role", "user").upper()
                content = message.get("content", "")
                history_text += f"\n{role}: {content}\n"

        prompt = f"""
You are a helpful AI Shopping Assistant.

You help customers search, compare and select products from the
available product catalog.

{history_text}

LATEST CUSTOMER MESSAGE:
{user_query}

IMPORTANT CONVERSATION RULES:
1. Use the previous conversation when answering follow-up questions.
2. Understand references such as "the first laptop", "the cheaper one",
   "both products", and "the one you recommended".
3. Do not ask the customer to repeat product names already mentioned
   in the conversation.
4. For calculations, use the prices and specifications already provided
   in the conversation or retrieved from the catalog.
5. If the customer asks a follow-up about previously discussed products,
   answer using the available conversation context.
6. Do not invent product details.

PRODUCT SEARCH RULES:
1. When the customer requests products matching specifications,
   you MUST call find_matching_products.
2. Use the tool results as the source of truth for product matches.
3. Recommend only products satisfying every stated requirement.
4. Never claim that no matching products exist without checking the tool.
5. If no products match, clearly explain that.
6. Mention prices and relevant specifications accurately.
7. Do not invent performance, compatibility, durability, battery life,
   or software capabilities.
8. If a detail is missing, say:
   "This information is not available in our catalog."
9. Do not recommend unsuitable alternatives when the customer explicitly
   asks for exact matches only.

COMPARISON RULES:
1. Compare only products that are present in the catalog or previous
   conversation.
2. Compare price, processor, RAM, storage and display when available.
3. Do not assume one processor is faster than another without
   sufficient evidence.
4. Calculate price differences accurately.
5. Give a recommendation based only on supported catalog information.

Respond clearly and naturally.
12. When comparing two or more products, present the
    comparison in a clear Markdown table.
13. Include product name, price, processor, RAM,
    storage, display, and rating when available.
14. After the table, explain the key differences
    and calculate the price difference accurately.
15. Use only information returned by the product tool.
"""

        for attempt in range(3):

            try:
                print("\nConnecting to Gemini...")

                chat = client.chats.create(
                    model="gemini-3.5-flash-lite",
                    config={
                        "tools": [find_matching_products]
                    }
                )

                response = chat.send_message(prompt)

                if response.text:
                    return response.text

                return "Gemini returned an empty response. Please try again."

            except Exception as e:

                error = str(e)

                if "503" in error or "UNAVAILABLE" in error:

                    if attempt < 2:
                        wait_time = 2 ** (attempt + 1)

                        print(
                            f"\nGemini server is busy. "
                            f"Retrying in {wait_time} seconds..."
                        )

                        time.sleep(wait_time)

                    else:
                        return (
                            "Gemini is temporarily unavailable after "
                            "3 attempts. Please try again later."
                        )

                else:
                    return f"Gemini API Error: {e}"

    except Exception as e:
        return f"Application Error: {e}"


if __name__ == "__main__":

    print("=" * 45)
    print("       AI SHOPPING ASSISTANT")
    print("=" * 45)

    query = input("\nWhat are you looking for? ")

    if query.strip():

        answer = get_gemini_response(query)

        print("\n" + "=" * 45)
        print("SHOPPING ASSISTANT:")
        print("=" * 45)

        print(answer)

    else:
        print("Please enter a valid shopping request.")