import re

# Ritter Manager – regelbasierte Spielsteuerung.
# Das Ziel ist nicht, "irgendetwas" zu erraten:
# Eindeutig -> Aktion, unklar -> Schweigen.

ACTIONS = {
    "Kampf": ["kampf", "kämpfen", "kaempfen", "angreifen", "gegner", "ritterkampf"],
    "Taverne": ["taverne"],
    "Abenteuer": ["abenteuer"],
    "Schmied": ["schmied", "schmiede", "schmieden"],
}

RANK_WORDS = [
    "rang", "rangliste", "ranglisten", "platz", "ranking",
    "liga", "rangänderung", "rangänderungen"
]

BLACKJACK_WORDS = [
    "black jack", "blackjack", "black-jack"
]

BUY_WORDS = [
    "kaufen", "kaufe", "kauf", "holen", "nimm", "nehmen", "besorgen"
]

YES_WORDS = ["ja", "jap", "jo", "okay", "ok", "yes"]
NO_WORDS = ["nein", "no", "nö", "nee"]

def normalize(text: str) -> str:
    text = text.lower().strip()
    text = text.replace("ß", "ss")
    text = re.sub(r"\s+", " ", text)
    return text

def is_fragment(text: str) -> bool:
    """Sehr kurze Eingaben ohne eindeutig erkennbare Aktion."""
    words = text.split()
    if len(words) == 0:
        return True
    if len(words) <= 2:
        # Eindeutige Ein-Wort-Aktionen dürfen trotzdem funktionieren.
        if any(re.search(rf"\b{re.escape(k)}\b", text) for vals in ACTIONS.values() for k in vals):
            return False
        if any(k in text for k in BLACKJACK_WORDS):
            return False
        return True
    return False

def rank_only(text: str) -> bool:
    return any(w in text for w in RANK_WORDS) and not any(
        re.search(rf"\b{re.escape(k)}\b", text)
        for vals in ACTIONS.values() for k in vals
    )

def blackjack(text: str) -> bool:
    return any(k in text for k in BLACKJACK_WORDS) or re.search(r"\bblack\s*jack\b", text) is not None

def detect_actions(text: str):
    found = []
    for action, words in ACTIONS.items():
        for word in words:
            if re.search(rf"\b{re.escape(word)}\b", text):
                found.append(action)
                break
    return found

def smith_action(text: str):
    # Laut Nebenhinweis: Schmiedkäufe zählen nicht als unnötig
    # und sollen gemacht werden, wenn es geht.
    # Wichtig: Die Website kennt den echten Goldbestand noch nicht.
    # Deshalb wird hier nur die Aktion "Schmied" ausgelöst.
    return "Schmied"

def decide(raw_text: str):
    text = normalize(raw_text)

    if not text:
        return {"speak": "", "action": None, "reason": "empty"}

    # Absolute Regel: reine Ranginformationen ignorieren.
    if rank_only(text):
        return {"speak": "", "action": None, "reason": "rank_only"}

    # Black Jack hat Vorrang, wenn es eindeutig genannt wird.
    if blackjack(text):
        return {
            "speak": "Black Jack: 10 Gold.",
            "action": "blackjack",
            "bet": 10,
            "reason": "blackjack"
        }

    actions = detect_actions(text)

    # Kauf-Fragen: immer Ja/Nein, damit keine Kauf-Loop entsteht.
    if any(w in text for w in BUY_WORDS):
        if any(w in text for w in NO_WORDS):
            return {"speak": "Nein.", "action": "buy_no", "reason": "explicit_no"}
        if any(w in text for w in YES_WORDS):
            return {"speak": "Ja.", "action": "buy_yes", "reason": "explicit_yes"}
        # Ohne konkrete Kaufanweisung keine Ausgabe.
        return {"speak": "", "action": None, "reason": "purchase_unclear"}

    # Eindeutige angebotene Aktion.
    if actions:
        # Bei mehreren angebotenen Aktionen wird genau EINE gewählt.
        # Priorität ist bewusst deterministisch.
        priority = ["Kampf", "Taverne", "Abenteuer", "Schmied"]
        chosen = next(a for a in priority if a in actions)
        return {"speak": chosen, "action": chosen.lower(), "reason": "clear_action"}

    # Zu kurz / unklar / Fragment -> schweigen.
    if is_fragment(text):
        return {"speak": "", "action": None, "reason": "unclear_or_short"}

    # "Was hast du gesagt?" -> nicht wiederholen; nur handeln, wenn aktuell
    # eine eindeutige Aktion erkennbar wäre. Hier ist keine vorhanden.
    if "was hast du gesagt" in text or "was hast du gesagt" == text:
        return {"speak": "", "action": None, "reason": "repeat_request_without_action"}

    return {"speak": "", "action": None, "reason": "no_safe_action"}