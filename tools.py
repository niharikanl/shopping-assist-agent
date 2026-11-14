import re
import json
from pathlib import Path


# Locate the product database
DATA_FILE = Path(__file__).parent / "data" / "products.json"


def load_products():
    """Load products from the JSON database."""
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def search_products(
    category=None,
    max_budget=None,
    min_rating=None,
    in_stock_only=True
):
    """Search products using the user's requirements."""

    products = load_products()
    results = []

    for product in products:

        if category and product["category"].lower() != category.lower():
            continue

        if max_budget is not None and product["price"] > max_budget:
            continue

        if min_rating is not None and product["rating"] < min_rating:
            continue

        if in_stock_only and not product["in_stock"]:
            continue

        results.append(product)

    return sorted(
        results,
        key=lambda product: product["rating"],
        reverse=True
    )


def compare_products(products):
    """Prepare product details for comparison."""

    if len(products) < 2:
        return "At least two products are required for comparison."

    comparison = []

    for product in products:
        comparison.append({
            "name": product["name"],
            "price": product["price"],
            "rating": product["rating"],
            "specifications": product["specifications"]
        })

    return comparison


def filter_by_requirements(products, requirements):
    """Filter products using budget, category and minimum specifications."""

    results = []

    # Support different argument names returned by Gemini.
    aliases = {
        "price_max": "max_price",
        "budget": "max_price",
        "ram_min": "min_ram",
        "ram_gb": "min_ram",
        "min_ram_gb": "min_ram",
        "storage_min": "min_storage",
        "storage_gb": "min_storage",
        "min_storage_gb": "min_storage"
    }

    normalized = {}

    for key, value in requirements.items():
        normalized[aliases.get(key, key)] = value

    for product in products:
        specs = product.get("specifications", {})
        matches = True

        # Category is stored at the product's top level.
        category = normalized.get("category")
        if category:
            if product.get("category", "").lower() != str(category).lower():
                continue

        # Check maximum price.
        max_price = normalized.get("max_price")
        if max_price is not None:
            if product.get("price", float("inf")) > float(max_price):
                continue

        # Check minimum RAM.
        min_ram = normalized.get("min_ram")
        if min_ram is not None:
            import re
            ram_match = re.search(r"\d+", str(specs.get("ram", "")))

            if not ram_match or int(ram_match.group()) < float(min_ram):
                continue

        # Check minimum storage.
        min_storage = normalized.get("min_storage")
        if min_storage is not None:
            import re
            storage_match = re.search(
                r"(\d+(?:\.\d+)?)\s*(TB|GB)",
                str(specs.get("storage", "")),
                re.IGNORECASE
            )

            if not storage_match:
                continue

            amount = float(storage_match.group(1))
            unit = storage_match.group(2).upper()

            storage_gb = amount * 1024 if unit == "TB" else amount

            if storage_gb < float(min_storage):
                continue

        # Check other text-based requirements.
        for key, value in normalized.items():
            if key in ("category", "max_price", "min_ram", "min_storage", "purpose"):
                continue

            actual = specs.get(key)

            if actual is None or str(value).lower() not in str(actual).lower():
                matches = False
                break

        if matches:
            results.append(product)

    return results