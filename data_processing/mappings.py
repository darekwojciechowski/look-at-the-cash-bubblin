from data_processing.category import (
    FOOD, GREENFOOD, TRANSPORTATION, CAR, LEASING, FUEL, REPAIRS, ALCOHOL, COFFEE, FASTFOOD,
    GROCERIES, CATERING, APARTMENT, BILLS, RENOVATION, CLOTHES, JEWELRY, ENTERTAINMENT,
    PCGAMES, BIKE, SPORT, PHARMACY, COSMETICS, TRAVEL, BOOKS, ANIMALS,
    INSURANCE, SUBSCRIPTIONS, INVESTMENTS, SELF_DEVELOPMENT, ELECTRONIC, SELF_CARE, KIDS, SHOPPING, MISC,
    all_category
)

# Default category for unmatched transactions
DEFAULT_CATEGORY = "MISC"

# Note: If two categories have overlapping keywords, the category listed first in the mappings dictionary will take precedence.
# Example: To debug, you can print a specific category's keywords using dict() or access them directly (e.g., print(FOOD)).


def mappings(data):
    """
    Categorizes input data based on predefined keywords for each category.

    Parameters:
    data (str): The input string to be categorized by matching keywords.

    Returns:
    str: The name of the matching category, or DEFAULT_CATEGORY if no match is found.

    How it works:
    1. A dictionary `categories` maps category names to sets of keywords.
    2. The function checks if any keyword from each category is present in the input `data`.
    3. It returns the first matching category name. If no keywords match, it returns DEFAULT_CATEGORY.

    Example:
    If `FOOD = {"apple", "bread"}` and `GREENFOOD = {"spinach", "kale"}`, 
    calling `mappings("I bought some bread and spinach")` will return "FOOD".
    """
    categories = {
        "FOOD": FOOD,
        "GREENFOOD": GREENFOOD,
        "TRANSPORTATION": TRANSPORTATION,
        "CAR": CAR,
        "LEASING": LEASING,
        "FUEL": FUEL,
        "REPAIRS": REPAIRS,
        "COFFEE": COFFEE,
        "FASTFOOD": FASTFOOD,
        "GROCERIES": GROCERIES,
        "CATERING": CATERING,
        "ALCOHOL": ALCOHOL,
        "APARTMENT": APARTMENT,
        "BILLS": BILLS,
        "RENOVATION": RENOVATION,
        "CLOTHES": CLOTHES,
        "JEWELRY": JEWELRY,
        "ENTERTAINMENT": ENTERTAINMENT,
        "PCGAMES": PCGAMES,
        "BIKE": BIKE,
        "SPORT": SPORT,
        "PHARMACY": PHARMACY,
        "COSMETICS": COSMETICS,
        "TRAVEL": TRAVEL,
        "BOOKS": BOOKS,
        "ANIMALS": ANIMALS,
        "INSURANCE": INSURANCE,
        "SUBSCRIPTIONS": SUBSCRIPTIONS,
        "INVESTMENTS": INVESTMENTS,
        "SELF_DEVELOPMENT": SELF_DEVELOPMENT,
        "ELECTRONIC": ELECTRONIC,
        "SELF_CARE": SELF_CARE,
        "KIDS": KIDS,
        "SHOPPING": SHOPPING,
        "MISC": MISC
    }

    for category, keywords in categories.items():
        if any(keyword in data.lower() for keyword in keywords):
            return category

    return DEFAULT_CATEGORY
