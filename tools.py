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

        # Filter by category
        if category and product["category"].lower() != category.lower():
            continue

        # Filter by maximum budget
        if max_budget is not None and product["price"] > max_budget:
            continue

        # Filter by minimum rating
        if min_rating is not None and product["rating"] < min_rating:
            continue

        # Filter unavailable products
        if in_stock_only and not product["in_stock"]:
            continue

        results.append(product)

    return sorted(
        results,
        key=lambda product: product["rating"],
        reverse=True
    )


def compare_products(products):
    """Compare products based on price and rating."""

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
    """
    Filter products by maximum price and minimum specifications.
    Supports values such as 16GB RAM and 512GB SSD.
    """

    results = []

    for product in products:
        specifications = product.get("specifications", {})
        matches = True

        for key, required_value in requirements.items():

            # Purpose is recommendation context, not a specification.
            if key == "purpose":
                continue

            # Check the maximum product price.
            if key == "max_price":
                price = product.get("price")

                try:
                    if price is None or float(price) > float(required_value):
                        matches = False
                        break
                except (TypeError, ValueError):
                    matches = False
                    break

                continue

            # Map requirement names to catalog specification keys.
            spec_key = {
                "min_ram": "ram",
                "min_ram_gb": "ram",
                "ram_gb": "ram",
                "min_storage": "storage",
                "min_storage_gb": "storage",
                "storage_gb": "storage"
            }.get(key, key)

            actual_value = specifications.get(spec_key)

            if actual_value is None:
                matches = False
                break

            # Numeric requirements represent minimum values.
            if isinstance(required_value, (int, float)):

                if spec_key == "storage":
                    storage_match = re.search(
                        r"(\d+(?:\.\d+)?)\s*(TB|GB)",
                        str(actual_value),
                        re.IGNORECASE
                    )

                    if not storage_match:
                        matches = False
                        break

                    storage_number = float(storage_match.group(1))
                    storage_unit = storage_match.group(2).upper()

                    # Convert TB to GB for a consistent comparison.
                    actual_number = (
                        storage_number * 1024
                        if storage_unit == "TB"
                        else storage_number
                    )

                else:
                    number_match = re.search(
                        r"\d+(?:\.\d+)?",
                        str(actual_value)
                    )

                    if not number_match:
                        matches = False
                        break

                    actual_number = float(number_match.group())

                if actual_number < float(required_value):
                    matches = False
                    break

            # Text requirements must match the catalog value.
            else:
                if str(required_value).lower() not in str(actual_value).lower():
                    matches = False
                    break

        if matches:
            results.append(product)

    return results