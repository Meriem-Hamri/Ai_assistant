from app.cleaning.ocr_cleaner import clean


tests = [
    "Le salaire mensuel brut est fixé à 9 5o0 dirhams marocains.",
    "Une prime pouvant atteindre 2 ooo dirhams.",
    "Une prime pouvant atteindre 2ooo dirhams.",
    "Le document contient le mot Bonjour.",
    "Le document contient une information importante.",
]


for text in tests:
    print("AVANT :", text)
    print("APRÈS :", clean(text))
    print("-" * 60)