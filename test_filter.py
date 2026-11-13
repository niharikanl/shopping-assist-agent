from tools import load_products, filter_by_requirements

products = load_products()

requirements = {
    "max_price": 70000,
    "min_ram": 32,
    "min_storage": 1024
}

results = filter_by_requirements(products, requirements)

if results:
    for product in results:
        print(product["name"], product["price"])
else:
    print("No matching products found.")