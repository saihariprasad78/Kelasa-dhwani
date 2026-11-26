"""Turns what a worker says into profile fields.

This is a rule-based parser so the prototype runs without any API key.
It handles English, plus common Hindi and Kannada words, and it tolerates the
small spelling mistakes that speech recognition makes (for example "Hebal").
In the full version this step is done by an LLM; the output format stays the same.
"""
import re

NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
    "eight": 8, "nine": 9, "ten": 10, "twelve": 12, "fifteen": 15, "twenty": 20,
    # Hindi
    "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पांच": 5, "पाँच": 5, "छह": 6, "छः": 6,
    "सात": 7, "आठ": 8, "नौ": 9, "दस": 10,
    # Kannada
    "ಒಂದು": 1, "ಎರಡು": 2, "ಮೂರು": 3, "ನಾಲ್ಕು": 4, "ಐದು": 5, "ಆರು": 6,
    "ಏಳು": 7, "ಎಂಟು": 8, "ಒಂಬತ್ತು": 9, "ಹತ್ತು": 10,
}

TRADE_WORDS = {
    "electrician": ["electrician", "electric", "wiring", "bijli", "बिजली", "इलेक्ट्रीशियन",
                    "ವಿದ್ಯುತ್", "ಎಲೆಕ್ಟ್ರಿಷಿಯನ್"],
    "plumber": ["plumber", "plumbing", "pipe", "नल", "प्लंबर", "ಪ್ಲಂಬರ್"],
    "mason": ["mason", "masonry", "mistri", "मिस्त्री", "ಮೇಸ್ತ್ರಿ"],
    "painter": ["painter", "painting", "पेंटर", "ಪೇಂಟರ್"],
    "helper": ["helper", "labour", "labor", "मजदूर", "हेल्पर", "ಕೂಲಿ", "ಹೆಲ್ಪರ್"],
}

AREA_ALIASES = {
    "hebbal": ["hebbal", "hebbala", "hebal", "hebbaal", "ಹೆಬ್ಬಾಳ", "हेब्बल", "हेब्बाल"],
    "yelahanka": ["yelahanka", "yelahnka", "ಯಲಹಂಕ", "येलहंका"],
    "indiranagar": ["indiranagar", "indira nagar", "indranagar", "ಇಂದಿರಾನಗರ", "इंदिरानगर", "इंदिरा नगर"],
    "koramangala": ["koramangala", "koramangla", "koramanagala", "ಕೋರಮಂಗಲ", "कोरमंगला"],
    "whitefield": ["whitefield", "white field", "ವೈಟ್‌ಫೀಲ್ಡ್", "व्हाइटफील्ड", "वाइटफील्ड"],
    "jayanagar": ["jayanagar", "jaya nagar", "ಜಯನಗರ", "जयनगर"],
    "rajajinagar": ["rajajinagar", "rajaji nagar", "ರಾಜಾಜಿನಗರ", "राजाजीनगर"],
    "malleshwaram": ["malleshwaram", "malleswaram", "maleshwaram", "ಮಲ್ಲೇಶ್ವರಂ", "मल्लेश्वरम"],
    "yeshwanthpur": ["yeshwanthpur", "yeshwantpur", "yeshvantpur", "ಯಶವಂತಪುರ", "यशवंतपुर"],
    "btm layout": ["btm layout", "btm", "b t m", "ಬಿಟಿಎಂ", "बीटीएम"],
    "electronic city": ["electronic city", "electronics city", "ಎಲೆಕ್ಟ್ರಾನಿಕ್ ಸಿಟಿ", "इलेक्ट्रॉनिक सिटी"],
    "marathahalli": ["marathahalli", "marathalli", "marathahali", "ಮಾರತ್ತಹಳ್ಳಿ", "मराठाहल्ली"],
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

FUZZY_CUTOFF = 0.8


def _has(text, words, whole_word=False):
    for w in words:
        if w.isascii():
            pattern = r"\b" + re.escape(w) + (r"\b" if whole_word else "")
            if re.search(pattern, text):
                return True
        elif w in text:
            return True
    return False


def _ratio(a, b):
    """Similarity from 0 to 1 based on edit distance."""
    if a == b:
        return 1.0
    if not a or not b:
        return 0.0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return 1.0 - prev[-1] / max(len(a), len(b))


def _candidates(text):
    words = re.findall(r"[a-z]+", text)
    out = list(words)
    for a, b in zip(words, words[1:]):
        out += [a + " " + b, a + b]
    return out


def _fuzzy(text, options):
    """Best option whose spelling is close to something said. options: {key: [words]}."""
    best, best_score = None, FUZZY_CUTOFF
    for cand in _candidates(text):
        if len(cand) < 5:
            continue
        for key, words in options.items():
            for w in words:
                if w.isascii() and len(w) >= 5:
                    score = _ratio(cand, w)
                    if score >= best_score:
                        best, best_score = key, score
    return best


def _find_area(t):
    found = [(len(w), a) for a, words in AREA_ALIASES.items() for w in words if _has_one(t, w)]
    if found:
        return max(found)[1]
    return _fuzzy(t, AREA_ALIASES)


def _has_one(t, w):
    if w.isascii():
        return re.search(r"\b" + re.escape(w), t) is not None
    return w in t


def parse_voice_text(text):
    """Return trade, years, area, availability, wage_expected (None if not found)."""
    t = (text or "").lower()

    trade = next((name for name, words in TRADE_WORDS.items() if _has(t, words)), None)
    if trade is None:
        trade = _fuzzy(t, TRADE_WORDS)

    years = None
    units = r"(?:years?|yrs?|saal|साल|वर्ष|ವರ್ಷ)"
    m = re.search(r"(\d{1,2})\s*\+?\s*" + units, t)
    if m:
        years = int(m.group(1))
    else:
        words = "|".join(sorted(map(re.escape, NUMBER_WORDS), key=len, reverse=True))
        m = re.search(r"(?<![a-z])(" + words + r")\s*" + units, t)
        if m:
            years = NUMBER_WORDS[m.group(1)]

    area = _find_area(t)

    availability = "anytime"
    for day, words in DAY_WORDS.items():
        if _has(t, words, whole_word=True):
            availability = day
            break

    wage = None
    m = re.search(r"(?:₹|rs\.?|rupees?)\s*(\d{3,5})|(\d{3,5})\s*(?:₹|rs\b|rupees?|rupaye|रुपये|ರೂಪಾಯಿ)", t)
    if m:
        wage = int(m.group(1) or m.group(2))

    return {"trade": trade, "years": years, "area": area,
            "availability": availability, "wage_expected": wage}


def missing_fields(profile):
    return [f for f in ("trade", "area") if not profile.get(f)]
