"""
lexicon — the shared, hand-authored gloss<->Ukrainian vocabulary used by
both directions of rule-based translation: ml/nlp/gloss_to_text.py (Phase 12,
gloss -> text) and ml/nlp/text_to_gloss.py (Phase 14, text -> gloss). Defined
once so the two directions can never silently drift apart -- a word this
project can compose into text is also a word it can parse back out of text.

Coverage is intentionally hand-authored, not scraped or guessed: no public
annotated УЖМ dataset exists yet (Phase 8), so there's no real gloss
vocabulary to build a lexicon from -- every entry here is written and
grammatically checked by hand, not automatically derived. ~50 words across
7 pronouns x 15 verbs x 24 nouns (matched by the case each verb genuinely
governs) lets compose_sentence() build hundreds of distinct, grammatically
real sentences, not just single-word output. See PROJECT_STATUS.md.

Ukrainian present tense doesn't distinguish grammatical gender (він/вона
"хоче", identical) -- so "Він"/"Вона" share one "3sg" conjugation slot
rather than needing separate verb forms each.

Case coverage is deliberately asymmetric and this is a grammar decision,
not an oversight: "genitive_partitive" (some of a substance -- "хочу
води") only makes idiomatic sense for mass/substance nouns (water, tea,
coffee, ...), so only those get that case filled in. Count nouns (book,
phone, house, ...) only get "accusative" -- pairing one with a
genitive_partitive-governing verb correctly raises UnsupportedPatternError
(ml/nlp/gloss_to_text.py) rather than composing an odd-sounding sentence.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PronounEntry:
    lemma: str  # capitalized surface form, e.g. "Я"
    person_key: str  # selects the matching VerbEntry.conjugation entry


@dataclass(frozen=True)
class VerbEntry:
    conjugation: dict[str, str]  # person_key -> conjugated surface form
    governs_case: str  # which NounEntry.cases key a direct object takes


@dataclass(frozen=True)
class NounEntry:
    cases: dict[str, str]  # case name -> surface form


@dataclass(frozen=True)
class StandaloneEntry:
    text: str  # lowercase surface form; gloss_to_text capitalizes it


PRONOUNS: dict[str, PronounEntry] = {
    "I": PronounEntry("Я", "1sg"),
    "YOU": PronounEntry("Ти", "2sg"),
    "HE": PronounEntry("Він", "3sg"),
    "SHE": PronounEntry("Вона", "3sg"),
    "WE": PronounEntry("Ми", "1pl"),
    "YOU_PL": PronounEntry("Ви", "2pl"),
    "THEY": PronounEntry("Вони", "3pl"),
}

VERBS: dict[str, VerbEntry] = {
    "WANT": VerbEntry(
        conjugation={
            "1sg": "хочу", "2sg": "хочеш", "3sg": "хоче",
            "1pl": "хочемо", "2pl": "хочете", "3pl": "хочуть",
        },
        governs_case="genitive_partitive",
    ),
    "LIKE": VerbEntry(
        conjugation={
            "1sg": "люблю", "2sg": "любиш", "3sg": "любить",
            "1pl": "любимо", "2pl": "любите", "3pl": "люблять",
        },
        governs_case="accusative",
    ),
    "HAVE": VerbEntry(
        conjugation={
            "1sg": "маю", "2sg": "маєш", "3sg": "має",
            "1pl": "маємо", "2pl": "маєте", "3pl": "мають",
        },
        governs_case="accusative",
    ),
    "KNOW": VerbEntry(
        conjugation={
            "1sg": "знаю", "2sg": "знаєш", "3sg": "знає",
            "1pl": "знаємо", "2pl": "знаєте", "3pl": "знають",
        },
        governs_case="accusative",
    ),
    "UNDERSTAND": VerbEntry(
        conjugation={
            "1sg": "розумію", "2sg": "розумієш", "3sg": "розуміє",
            "1pl": "розуміємо", "2pl": "розумієте", "3pl": "розуміють",
        },
        governs_case="accusative",
    ),
    "SEE": VerbEntry(
        conjugation={
            "1sg": "бачу", "2sg": "бачиш", "3sg": "бачить",
            "1pl": "бачимо", "2pl": "бачите", "3pl": "бачать",
        },
        governs_case="accusative",
    ),
    "READ": VerbEntry(
        conjugation={
            "1sg": "читаю", "2sg": "читаєш", "3sg": "читає",
            "1pl": "читаємо", "2pl": "читаєте", "3pl": "читають",
        },
        governs_case="accusative",
    ),
    "WRITE": VerbEntry(
        conjugation={
            "1sg": "пишу", "2sg": "пишеш", "3sg": "пише",
            "1pl": "пишемо", "2pl": "пишете", "3pl": "пишуть",
        },
        governs_case="accusative",
    ),
    "EAT": VerbEntry(
        conjugation={
            "1sg": "їм", "2sg": "їси", "3sg": "їсть",
            "1pl": "їмо", "2pl": "їсте", "3pl": "їдять",
        },
        governs_case="accusative",
    ),
    "DRINK": VerbEntry(
        conjugation={
            "1sg": "п'ю", "2sg": "п'єш", "3sg": "п'є",
            "1pl": "п'ємо", "2pl": "п'єте", "3pl": "п'ють",
        },
        governs_case="genitive_partitive",
    ),
    # The remaining verbs are only ever used without a direct object
    # (the [PRONOUN, VERB] pattern, e.g. "Я йду." -- see gloss_to_text.py) --
    # governs_case is still filled in with the case each would genuinely
    # take if it ever gained an object (none of the current NOUNS pair with
    # them), not a placeholder.
    "GO": VerbEntry(
        conjugation={
            "1sg": "іду", "2sg": "ідеш", "3sg": "іде",
            "1pl": "ідемо", "2pl": "ідете", "3pl": "ідуть",
        },
        governs_case="accusative",
    ),
    "WORK": VerbEntry(
        conjugation={
            "1sg": "працюю", "2sg": "працюєш", "3sg": "працює",
            "1pl": "працюємо", "2pl": "працюєте", "3pl": "працюють",
        },
        governs_case="accusative",
    ),
    "LIVE": VerbEntry(
        conjugation={
            "1sg": "живу", "2sg": "живеш", "3sg": "живе",
            "1pl": "живемо", "2pl": "живете", "3pl": "живуть",
        },
        governs_case="accusative",
    ),
    "SLEEP": VerbEntry(
        conjugation={
            "1sg": "сплю", "2sg": "спиш", "3sg": "спить",
            "1pl": "спимо", "2pl": "спите", "3pl": "сплять",
        },
        governs_case="accusative",
    ),
    "SPEAK": VerbEntry(
        conjugation={
            "1sg": "говорю", "2sg": "говориш", "3sg": "говорить",
            "1pl": "говоримо", "2pl": "говорите", "3pl": "говорять",
        },
        governs_case="accusative",
    ),
}

NOUNS: dict[str, NounEntry] = {
    # Mass/substance nouns -- genuinely take both "some of X" (genitive
    # partitive, pairs with WANT/DRINK) and a definite object (accusative,
    # pairs with LIKE/HAVE/KNOW/...).
    "WATER": NounEntry({"nominative": "вода", "genitive_partitive": "води", "accusative": "воду"}),
    "BREAD": NounEntry({"nominative": "хліб", "genitive_partitive": "хліба", "accusative": "хліб"}),
    "TEA": NounEntry({"nominative": "чай", "genitive_partitive": "чаю", "accusative": "чай"}),
    "COFFEE": NounEntry({"nominative": "кава", "genitive_partitive": "кави", "accusative": "каву"}),
    "MILK": NounEntry({"nominative": "молоко", "genitive_partitive": "молока", "accusative": "молоко"}),
    "JUICE": NounEntry({"nominative": "сік", "genitive_partitive": "соку", "accusative": "сік"}),
    "SOUP": NounEntry({"nominative": "суп", "genitive_partitive": "супу", "accusative": "суп"}),
    "MEAT": NounEntry({"nominative": "м'ясо", "genitive_partitive": "м'яса", "accusative": "м'ясо"}),
    "SUGAR": NounEntry({"nominative": "цукор", "genitive_partitive": "цукру", "accusative": "цукор"}),
    # Count nouns -- only accusative: "хочу книги" is not idiomatic partitive
    # the way "хочу води" is, so WANT/DRINK + a count noun correctly raises
    # UnsupportedPatternError rather than composing a dubious sentence.
    "BOOK": NounEntry({"nominative": "книга", "accusative": "книгу"}),
    "LETTER": NounEntry({"nominative": "лист", "accusative": "лист"}),
    "PHONE": NounEntry({"nominative": "телефон", "accusative": "телефон"}),
    "HOUSE": NounEntry({"nominative": "будинок", "accusative": "будинок"}),
    "CAR": NounEntry({"nominative": "машина", "accusative": "машину"}),
    "WORK_N": NounEntry({"nominative": "робота", "accusative": "роботу"}),
    "SCHOOL": NounEntry({"nominative": "школа", "accusative": "школу"}),
    "CITY": NounEntry({"nominative": "місто", "accusative": "місто"}),
    # Animate: accusative singular equals genitive singular, not nominative
    # (a real Ukrainian rule -- "бачу друга", not "*бачу друг").
    "FRIEND": NounEntry({"nominative": "друг", "accusative": "друга"}),
    "NAME": NounEntry({"nominative": "ім'я", "accusative": "ім'я"}),
    "TIME": NounEntry({"nominative": "час", "accusative": "час"}),
    "DAY": NounEntry({"nominative": "день", "accusative": "день"}),
    "COUNTRY": NounEntry({"nominative": "країна", "accusative": "країну"}),
    "FAMILY": NounEntry({"nominative": "сім'я", "accusative": "сім'ю"}),
    "MONEY": NounEntry({"nominative": "гроші", "accusative": "гроші"}),
}

# ml/datasets/synthetic.py's DEMO_GLOSSES, mapped to their real meaning,
# plus a few more common standalone words/phrases.
STANDALONE: dict[str, StandaloneEntry] = {
    "PRIVIT": StandaloneEntry("привіт"),
    "DYAKUYU": StandaloneEntry("дякую"),
    "TAK": StandaloneEntry("так"),
    "NI": StandaloneEntry("ні"),
    "BUD_LASKA": StandaloneEntry("будь ласка"),
    "DOBRANICH": StandaloneEntry("добраніч"),
    "VYBACHTE": StandaloneEntry("вибачте"),
    "DO_POBACHENNYA": StandaloneEntry("до побачення"),
}

NEGATION_GLOSS = "NOT"  # e.g. ["I", "NOT", "WANT", "WATER"] <-> "Я не хочу води."
NEGATION_PARTICLE = "не"
