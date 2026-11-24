"""Turns what a worker says into profile fields.

This is a simple rule-based parser so the prototype runs without any API key.
In the full version this step is done by an LLM; the output format stays the same.
"""
import re

from matching import AREAS

NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
    "eight": 8, "nine": 9, "ten": 10, "twelve": 12, "fifteen": 15, "twenty": 20,
}

TRADE_WORDS = {
    "electrician": ["electrician", "electric", "wiring", "bijli", "बिजली", "ವಿದ್ಯುತ್"],
    "plumber": ["plumber", "plumbing", "pipe", "नल", "ಪ್ಲಂಬರ್"],
    "mason": ["mason", "masonry", "mistri", "मिस्त्री", "ಮೇಸ್ತ್ರಿ"],
    "painter": ["painter", "painting", "पेंटर", "ಪೇಂಟರ್"],
    "helper": ["helper", "labour", "labor", "मजदूर", "ಕೂಲಿ"],
}

DAY_WORDS = {
    "tomorrow": ["tomorrow", "kal", "कल", "ನಾಳೆ"],
    "today": ["today", "aaj", "आज", "ಇಂದು"],
}

LEARNING_TIPS = {
    "electrician": "Learn to read a basic circuit diagram, and always switch off the main supply before you start work.",
    "plumber": "Learn to pressure-test pipe joints before the wall is closed.",
    "mason": "Practise checking level and plumb with a spirit level and a plumb bob.",
    "painter": "Learn surface preparation. Sanding and primer decide how long paint lasts.",
    "helper": "Learn basic site safety: helmet, gloves and safe lifting.",
}


def _has(text, words, whole_word=False):
    for w in words:
        if w.isascii():
            pattern = r"\b" + re.escape(w) + (r"\b" if whole_word else "")
            if re.search(pattern, text):
                return True
        elif w in text:
            return True
    return False


def parse_voice_text(text):
    """Return trade, years, area, availability, wage_expected (None if not found)."""
    t = (text or "").lower()

    trade = next((name for name, words in TRADE_WORDS.items() if _has(t, words)), None)

    years = None
    m = re.search(r"(\d{1,2})\s*\+?\s*(?:years?|yrs?|saal|साल|वर्ष|ವರ್ಷ)", t)
    if m:
        years = int(m.group(1))
    else:
        m = re.search(r"\b(" + "|".join(NUMBER_WORDS) + r")\s+(?:years?|yrs?)", t)
        if m:
            years = NUMBER_WORDS[m.group(1)]

    area = next((a for a in sorted(AREAS, key=len, reverse=True) if a in t), None)

    availability = "anytime"
    for day, words in DAY_WORDS.items():
        if _has(t, words, whole_word=True):
            availability = day
            break

    wage = None
    m = re.search(r"(?:₹|rs\.?|rupees?)\s*(\d{3,5})|(\d{3,5})\s*(?:₹|rs\b|rupees?|rupaye)", t)
    if m:
        wage = int(m.group(1) or m.group(2))

    return {"trade": trade, "years": years, "area": area,
            "availability": availability, "wage_expected": wage}


def missing_fields(profile):
    return [f for f in ("trade", "area") if not profile.get(f)]
