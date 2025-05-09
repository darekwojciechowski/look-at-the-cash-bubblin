import logging
import csv
from enum import Enum
import pandas as pd
import csv


class CATEGORY(Enum):
    TRANSPORTATION = '🚊 Transportation'
    CAR = '🚗 Car'
    EATING_OUT = "🦞 Eating Out"
    FOOD = "🥦 Food"
    CLOTHES = "👘 Clothes"
    TRAVEL = '🗺️ Travel'
    SHOPPING = "🛒 Shopping"
    APARTMENT = "🏯 Apartment"
    SELF_DEVELOPMENT = "🚀 Self Development"
    ANIMALS = "🐺 Animals"
    ENTERTAINMENT = "🎥 Entertainment"
    INVESTMENTS = "💸 Investments"
    CARE = '🛀🏾 Care'
    SELF_DESTRUCTION = '☠ Self Destruction'
    MISC = "Misc"


class IMPORTANCE(Enum):
    SHOULDNT_HAVE = "Shouldn't Have"
    NICE_TO_HAVE = "Nice to Have"
    HAVE_TO_HAVE = "Have to Have"
    ESSENTIAL = "Essential"


class Expense:
    def __init__(self, month, year, item, price):
        self.month = month
        self.year = year
        self.item = item
        self.price = price
        self.category, self.importance = self._determine_category_and_importance()

    def _determine_category_and_importance(self):
        item = self.item.lower()
        if "apartment" in item or "bills" in item or "renovation" in item:
            return CATEGORY.APARTMENT, IMPORTANCE.ESSENTIAL
        if "food" in item or "greenfood" in item:
            return CATEGORY.FOOD, IMPORTANCE.ESSENTIAL
        if "fuel" in item or "repairs" in item or "car" in item or "leasing" in item:
            return CATEGORY.CAR, IMPORTANCE.HAVE_TO_HAVE
        if "transportation" in item:
            return CATEGORY.TRANSPORTATION, IMPORTANCE.HAVE_TO_HAVE
        if "groceries" in item or "coffee" in item or "catering" in item:
            return CATEGORY.EATING_OUT, IMPORTANCE.NICE_TO_HAVE
        if "animals" in item:
            return CATEGORY.ANIMALS, IMPORTANCE.HAVE_TO_HAVE
        if "self_development" in item or "book" in item:
            return CATEGORY.SELF_DEVELOPMENT, IMPORTANCE.NICE_TO_HAVE
        if "clothes" in item or "jewelry" in item:
            return CATEGORY.CLOTHES, IMPORTANCE.NICE_TO_HAVE
        if "entertainment" in item or "subscriptions" in item or "pcgames" in item:
            return CATEGORY.ENTERTAINMENT, IMPORTANCE.NICE_TO_HAVE
        if "shopping" in item or "electronic" in item:
            return CATEGORY.SHOPPING, IMPORTANCE.NICE_TO_HAVE
        if "investment" in item:
            return CATEGORY.INVESTMENTS, IMPORTANCE.NICE_TO_HAVE
        if "pharmacy" in item or "cosmetics" in item or "insurance" in item or "sport" in item or "bike" in item:
            return CATEGORY.CARE, IMPORTANCE.NICE_TO_HAVE
        if "travel" in item:
            return CATEGORY.TRAVEL, IMPORTANCE.NICE_TO_HAVE
        if "alcohol" in item or "fastfood" in item:
            return CATEGORY.SELF_DESTRUCTION, IMPORTANCE.SHOULDNT_HAVE
        return CATEGORY.MISC, IMPORTANCE.NICE_TO_HAVE

    def __repr__(self) -> str:
        return f"{self.month},{self.year},{self.item},{self.category.value},{self.price},{self.importance.value}"
