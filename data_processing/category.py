"""
Category definitions for transaction classification.

Each public constant is a ``set[str]`` of lowercase keywords.  ``mappings()``
in ``mappings.py`` iterates ``all_category`` in order, tests each keyword
against the transaction description, and returns the first matching constant
name — ``"FOOD"``, ``"COFFEE"``, and so on.  ``MISC`` is an empty set used as the
catch-all fallback — ``mappings()`` returns ``"MISC"`` when nothing matches.

``REMOVE_ENTRY`` is special: rows categorized as ``REMOVE_ENTRY`` are dropped
by ``process_dataframe`` before export (refunds and reversals).

``all_category`` lists every constant name in matching priority order.  Add a
new constant here *and* to ``all_category`` to extend the taxonomy.

This file uses line-length = 120 characters for better horizontal readability.
Keywords are grouped on single lines to make scanning and editing easier.
See pyproject.toml [tool.ruff.lint.per-file-ignores] for E501 exception.
"""

# Master list of category names in matching priority order.
# ``mappings()`` iterates this list and returns the first matching name.
all_category = [
    "REMOVE_ENTRY",
    "FOOD", "GREENFOOD", "TRANSPORTATION", "CAR", "LEASING", "FUEL", "REPAIRS", "COFFEE", "FASTFOOD", "GROCERIES",
    "CATERING", "ALCOHOL", "APARTMENT", "BILLS", "RENOVATION", "CLOTHES", "JEWELRY", "ENTERTAINMENT", "PCGAMES",
    "BIKE", "SPORT", "PHARMACY", "COSMETICS", "TRAVEL", "BOOKS", "ANIMALS", "INSURANCE", "SUBSCRIPTIONS",
    "INVESTMENTS", "SELF_DEVELOPMENT", "ELECTRONIC", "SELF_CARE", "KIDS", "SHOPPING", "MISC",
]

# --- Special ---
# Rows matching REMOVE_ENTRY are dropped before export (refunds / reversals).
REMOVE_ENTRY: set[str] = {"zwrot", "refund"}

# --- Food & drink ---
# Supermarkets and grocery chains matched as food purchases.
FOOD = {"auchan", "kaufland", "aldi", "tesco",
        "dino", "carrefour", "intermarche", "intermarché", "netto", "biedronka", "lidl"}

# Health-food and specialty grocery stores (organic, herbal, yerba mate).
GREENFOOD = {"greenfood", "yerbamatestore", "yerbamate",
             "zielonytarg", "zielnik", "matcha", "zielonybazar"}

# --- Transport ---
# Public transit, taxis, and parking charges.
TRANSPORTATION = {"transportation", "koleo", "pkp", "mpk", "autobus",
                  "ztm", "ztp", "parking", "parkomat", "spp", "taxi", "uber"}

# Car brand names matched as car-related spending (service, parts, purchases).
CAR = {
    "bmw", "citroen", "dacia", "fiat", "ford", "hyundai", "kia", "opel", "honda", "skoda", "toyota", "renault",
    "nissan", "volvo", "volkswagen", "suzuki", "mazda", "mercedes", "ferrari", "peugeot", "romeo", "jaguar",
    "lamborghini", "aston", "bentley", "mclaren", "bugatti", "jeep", "corvette", "lexus", "subaru", "lancia",
    "cadillac", "koenigsegg", "maserati"
}

# Car leasing and subscription services.
LEASING = {"leasing", "car2lease", "carsmile"}

# Fuel stations and fuel-related keywords.
FUEL = {"fuel", "paliwo", "orlen", "lotos", "shell", "circle", "amic"}

# Auto repair shops and tyre retailers.
REPAIRS = {"repairs", "oponeo", "mechanic"}

# Coffee shops and cafés.
COFFEE = {"coffee", "kawiarnia", "kawa", "starbucks", "cafe", "café", "caffe"}

# Fast-food chains and quick-service restaurants.
FASTFOOD = {
    "fastfood", "subway", "doner", "kebab", "mcdonalds", "kfc", "döner", "yalla", "foodmax", "yammi", "zapiekarnia",
    "zapiekanki", "zahir", "fast food"
}

# Sit-down restaurants and food delivery; distinct from FASTFOOD.
GROCERIES = {
    "groceries", "restaurant", "restauracja", "restaurante", "pizza", "sushi", "sphinx", "fish", "seafood", "k-2",
    "phenix", "pankejk", "nolita", "epoka", "rozbrat", "ale gloria", "charlotte","anatewka", "manekin", "andrus", 
    "konspira", "weranda", "szajna", "piwnica świdnicka"
}

# Meal-prep / catering box subscriptions.
CATERING = {"catering", "lunching", "bodychief"}

# Alcohol purchases — feeds into SELF_DESTRUCTION category.
ALCOHOL = {"alcohol", "spirits", "whisky", "aperol", "guinness"}

# --- Housing ---
# Rent and apartment-related payments.
APARTMENT = {"apartment"}

# Utility bills (electricity, internet, etc.).
BILLS = {"bills", "internet", "pge"}

# Home improvement retailers and decoration shops.
RENOVATION = {"renovation", "ikea", "home", "leroy",
              "castorama", "homla", "jysk", "dekoria", "duka"}

# --- Lifestyle & shopping ---
# Clothing and footwear retailers.
CLOTHES = {
    "clothes", "reserved", "ccc", "cloppenburg", "zalando", "eobuwie", "adidas", "zara", "sizeer", "maxx", "distance",
    "ecco", "kazar", "ryłko", "wittchen", "vistula", "wolczanka", "calvin", "guess", "puma", "balance", "hilfiger",
    "fila", "levis", "wrangler", "4f", "bershka", "converse", "cropp", "espirit", "h&m", "cooper", "medicine",
    "ochnik", "pierre", "big star", "nike"
}

# Jewellery and accessory shops.
JEWELRY = {"jewelry", "apart", "kruk", "tous", "pandora"}

# Cinemas, theatres, ticket platforms, and aqua parks.
ENTERTAINMENT = {
    "entertainment", "cinema", "vod", "bilet", "muzeum", "teatr", "aquapark", "billiards", "darts"
}

# Digital games and gaming platforms.
PCGAMES = {"pc games", "cdprojektred",
           "rockstar", "steam", "xbox", "playstation"}

# Bicycle brands, bike shops, and cycling-related stores.
BIKE = {
    "loca", "rondo", "bianchi", "scott", "cannondale", "trek", "ghost", "merida", "felt", "orbea", "canyon",
    "superior", "kross", "b'twin", "specialized", "romet", "kellys", "giant", "mondraker", "bikesalon", "gravel",
    "cyklomania", "centrumrowerowe"
}

# Sports equipment and gym-related purchases.
SPORT = {"sport", "decathlon", "tenis", "babolat", "wilson", "climbing"}

# Pharmacies and health stores.
PHARMACY = {"pharmacy", "apteka", "melissa", "super - pharm"}

# Cosmetics and beauty retailers.
COSMETICS = {"cosmetics", "ksisters",
             "ecoflores", "rossmann", "douglas", "sephora"}

# --- Travel & education ---
# Airlines, travel agencies, and inter-city coaches.
TRAVEL = {"travel", "iaka", "rainbow", "coral",
          "ryanair", "wizz", "lufthansa", "airlines", "flixbus"}

# Bookshops and audio/e-book subscription services.
BOOKS = {"books", "audioteka", "storytel", "legimi"}

# Pet food, vet visits, and animal-related services.
ANIMALS = {"animals", "karma", "weterynarz", "dog"}

# --- Finance & care ---
# Insurance companies and policies.
INSURANCE = {"insurance", "pzu", "uniqa", "link4",
             "warta", "ufg", "generali", "allianz"}

# Streaming and digital subscription services.
SUBSCRIPTIONS = {
    "subscriptions", "netflix", "prime", "hbo", "hulu", "paramount", "canal", "cda", "disney", "tencent", "showtime",
    "youtube", "tidal", "spotify"
}

# Brokerage platforms and investment deposits.
INVESTMENTS = {
    "investments", "tfi", "bossa", "xtb", "etoro", "plus500", "brokers", "firstrade", "trading212", "exante", "degiro"
}

# Online courses, coding bootcamps, and e-learning platforms.
SELF_DEVELOPMENT = {"self development", "udemy",
                    "skillshare", "course", "eduweb", "coderslab"}

# Electronics and computer hardware retailers.
ELECTRONIC = {"electronic", "morele", "xkom",
              "komputronik", "apple", "euro.com"}

# Hairdressers, nail studios, and personal beauty services.
SELF_CARE = {"nails", "beauty"}

# Children's toys, clothing, and related spending.
KIDS = {"kids", "children", "toys"}

# General online marketplaces (e-commerce, second-hand).
SHOPPING = {"shopping", "allegro", "olx", "amazon", "empik"}

# --- Fallback ---
# Empty set — used as the catch-all when no other keyword matches.
# ``mappings()`` returns ``"MISC"`` for unrecognized transactions.
MISC: set[str] = set()
