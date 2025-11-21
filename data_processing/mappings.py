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
    1. Automatically builds a categories dictionary from all_category list using dictionary comprehension.
    2. Each category name is mapped to its corresponding keyword set via globals().
    3. The function checks if any keyword from each category is present in the input data (case-insensitive).
    4. Returns the first matching category name. If no keywords match, returns DEFAULT_CATEGORY.

    Note:
    The dictionary comprehension {category: globals()[category] for category in all_category}
    dynamically creates the categories dict, eliminating manual mapping and ensuring all categories
    from all_category are automatically included.

    Example:
    If `FOOD = {"apple", "bread"}` and `GREENFOOD = {"spinach", "kale"}`, 
    calling `mappings("I bought some bread and spinach")` will return "FOOD".
    """
    # Automatically build categories dictionary from all_category list
    categories = {category: globals()[category] for category in all_category}

    for category, keywords in categories.items():
        if any(keyword in data.lower() for keyword in keywords):
            return category

    return DEFAULT_CATEGORY
