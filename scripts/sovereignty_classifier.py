"""
Sovereignty Framing Classifier for Crimea

Detects whether text content frames Crimea as Ukrainian, Russian, or disputed.
Uses rule-based pattern matching on sovereignty indicators — no ML needed.

The classifier looks for:
1. Location labels: "Simferopol, Ukraine" vs "Simferopol, Russia"
2. Administrative names: "Autonomous Republic of Crimea" (UA) vs "Republic of Crimea" (RU)
3. Framing language: "annexed" (correct) vs "reunified" (Russian narrative)
4. Structural signals: URL paths, country codes, metadata

Usage:
    from sovereignty_classifier import SovereigntyClassifier
    clf = SovereigntyClassifier()
    result = clf.classify("Weather in Simferopol, Russia today...")
    print(result)  # {'label': 'russia', 'confidence': 0.85, 'signals': [...]}
"""

import re
from dataclasses import dataclass, field


@dataclass
class Signal:
    """A single sovereignty signal detected in text."""
    pattern: str
    matched: str
    label: str  # "ukraine", "russia", "correct_framing", "russian_framing"
    weight: float
    context: str = ""  # surrounding text


@dataclass
class ClassificationResult:
    """Result of sovereignty framing classification."""
    label: str  # "ukraine", "russia", "disputed", "neutral", "no_signal"
    confidence: float  # 0.0 - 1.0
    signals: list[Signal] = field(default_factory=list)
    ua_score: float = 0.0
    ru_score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "confidence": round(self.confidence, 3),
            "ua_score": round(self.ua_score, 3),
            "ru_score": round(self.ru_score, 3),
            "signals": [
                {"pattern": s.pattern, "matched": s.matched, "label": s.label, "weight": s.weight}
                for s in self.signals
            ],
        }


# --- Sovereignty signal patterns ---

# Location labels (highest confidence — explicit address/label format)
LOCATION_UKRAINE = [
    (r'simferopol[,\s]+(?:crimea[,\s]+)?ukraine', 2.0),
    (r'sevastopol[,\s]+(?:crimea[,\s]+)?ukraine', 2.0),
    (r'yalta[,\s]+(?:crimea[,\s]+)?ukraine', 2.0),
    (r'kerch[,\s]+(?:crimea[,\s]+)?ukraine', 2.0),
    (r'crimea[,\s]+ukraine', 2.0),
    (r'(?:симферополь|севастополь|ялта|керч)[,\s]+(?:крим[,\s]+)?україн', 2.0),
    (r'крим[,\s]+україн', 2.0),
]

LOCATION_RUSSIA = [
    (r'simferopol[,\s]+(?:crimea[,\s]+)?russia', 2.0),
    (r'sevastopol[,\s]+(?:crimea[,\s]+)?russia', 2.0),
    (r'yalta[,\s]+(?:crimea[,\s]+)?russia', 2.0),
    (r'kerch[,\s]+(?:crimea[,\s]+)?russia', 2.0),
    (r'crimea[,\s]+russia(?!n)', 2.0),
    (r'(?:симферополь|севастополь|ялта|керч)[,\s]+(?:крым[,\s]+)?росси', 2.0),
    (r'крым[,\s]+росси', 2.0),
]

# Administrative names
ADMIN_UKRAINE = [
    (r'autonomous\s+republic\s+of\s+crimea', 1.5),
    (r'автономна\s+республіка\s+крим', 1.5),
    (r'UA-43', 1.5),  # ISO 3166-2 code for Crimea under Ukraine
    (r'country[_\s]?code["\s:=]+ua\b', 1.5),
    (r'/ukraine/crimea|/ukraine/simferopol', 1.0),  # explicit geo path
]

ADMIN_RUSSIA = [
    (r'(?<!autonomous\s)republic\s+of\s+crimea', 1.5),
    (r'республика\s+крым', 1.5),  # Russian Federation admin name
    (r'крымский\s+федеральный\s+округ', 1.5),
    (r'country[_\s]?code["\s:=]+ru\b', 1.5),
    (r'/russia/crimea|/russia/simferopol', 1.0),  # explicit geo path
]

# Framing language (how the text describes the situation)
CORRECT_FRAMING = [
    (r'annex(?:ed|ation)\s+(?:of\s+)?crimea', 1.0),
    (r'occupied\s+crimea', 1.0),
    (r'illegal(?:ly)?\s+(?:annex|occupi)', 1.0),
    (r'crimea\s+(?:is|belongs?\s+to)\s+ukraine', 1.5),
    (r'ukrainian\s+crimea', 1.0),
    (r'ukraine.s\s+crimea', 1.0),
    (r'анексі[яю]\s+крим', 1.0),
    (r'окупован\w+\s+крим', 1.0),
    (r'крим\s+—?\s+це\s+україна', 2.0),
]

RUSSIAN_FRAMING = [
    (r'crimea\s+(?:re)?join(?:ed|ing)\s+russia', 1.5),
    (r'(?:re)?unif(?:ied|ication)\s+(?:of|with)\s+(?:crimea|russia)', 1.5),
    (r'crimea\s+(?:is|belongs?\s+to)\s+russia', 1.5),
    (r'russian\s+crimea(?!\s+war)', 1.0),
    (r'russia.s\s+crimea', 1.0),
    (r'крым\s+наш', 2.0),  # "Crimea is ours" (Russian slogan)
    (r'воссоединени\w+\s+крым', 1.5),  # "reunification of Crimea"
    (r'крым\s+—?\s+это\s+росси', 2.0),
    (r'вхождени\w+\s+крым\w*\s+в\s+состав', 1.5),  # "entry of Crimea into (Russia)"
    (r'присоединени\w+\s+крым', 1.5),  # "accession of Crimea"
    (r'крым\s+в\s+составе?\s+росси', 2.0),  # "Crimea as part of Russia"
    (r'субъект\w*\s+(?:российской\s+)?федерации\s*.*крым', 1.5),  # "federal subject...Crimea"
    (r'crimea\s+as\s+(?:a\s+)?part\s+of\s+russia', 2.0),
    (r'crimea\s+returned?\s+to\s+russia', 1.5),
]

# Structural signals — ONLY for platform data, NOT for article URLs
# TLD (.ru/.ua) and language paths (/ru/) are NOT sovereignty signals
# A Russian news site writing about Crimea ≠ claiming Crimea is Russian
STRUCTURAL_UKRAINE = [
    (r'country=ukraine', 1.0),
    (r'country_code["\s:=]+ua\b', 1.0),
    (r'region["\s:=]+ua\b', 0.8),
]

STRUCTURAL_RUSSIA = [
    (r'country=russia', 1.0),
    (r'country_code["\s:=]+ru\b', 1.0),
    (r'region["\s:=]+ru\b', 0.8),
]


class SovereigntyClassifier:
    """Classifies text for Crimea sovereignty framing."""

    def __init__(self):
        self._patterns = self._compile_patterns()

    def _compile_patterns(self):
        groups = [
            ("ukraine", LOCATION_UKRAINE + ADMIN_UKRAINE + STRUCTURAL_UKRAINE),
            ("russia", LOCATION_RUSSIA + ADMIN_RUSSIA + STRUCTURAL_RUSSIA),
            ("correct_framing", CORRECT_FRAMING),
            ("russian_framing", RUSSIAN_FRAMING),
        ]
        compiled = []
        for label, patterns in groups:
            for pattern, weight in patterns:
                compiled.append((re.compile(pattern, re.IGNORECASE), label, weight, pattern))
        return compiled

    def classify(self, text: str) -> ClassificationResult:
        """Classify a text for Crimea sovereignty framing."""
        signals = []

        for regex, label, weight, pattern_str in self._patterns:
            for match in regex.finditer(text):
                # Extract context (50 chars around match)
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end].strip()

                signals.append(Signal(
                    pattern=pattern_str,
                    matched=match.group(),
                    label=label,
                    weight=weight,
                    context=context,
                ))

        if not signals:
            return ClassificationResult("no_signal", 0.0)

        # Score
        ua_score = sum(s.weight for s in signals if s.label in ("ukraine", "correct_framing"))
        ru_score = sum(s.weight for s in signals if s.label in ("russia", "russian_framing"))
        total = ua_score + ru_score

        if total == 0:
            return ClassificationResult("neutral", 0.3, signals, ua_score, ru_score)

        if ua_score > ru_score:
            confidence = min(0.95, ua_score / total)
            label = "ukraine"
        elif ru_score > ua_score:
            confidence = min(0.95, ru_score / total)
            label = "russia"
        else:
            confidence = 0.5
            label = "disputed"

        return ClassificationResult(label, confidence, signals, ua_score, ru_score)

    def classify_url(self, url: str, title: str = "", snippet: str = "") -> ClassificationResult:
        """Classify a URL + title + snippet combination."""
        # URLs carry strong structural signals
        combined = f"{url}\n{title}\n{snippet}"
        return self.classify(combined)

    def has_crimea_reference(self, text: str) -> bool:
        """Quick check: does the text mention Crimea at all?"""
        return bool(re.search(
            r'crimea|крим[уі]?|крым[ауе]?|krim|kırım',
            text, re.IGNORECASE
        ))

    def extract_sovereignty_context(self, text: str, window: int = 100) -> list[str]:
        """Extract text windows around Crimea mentions."""
        contexts = []
        for match in re.finditer(r'crimea|крим[уі]?|крым[ауе]?', text, re.IGNORECASE):
            start = max(0, match.start() - window)
            end = min(len(text), match.end() + window)
            contexts.append(text[start:end].strip())
        return contexts


if __name__ == "__main__":
    clf = SovereigntyClassifier()

    tests = [
        "Weather in Simferopol, Ukraine today: 18°C, partly cloudy",
        "Weather in Simferopol, Russia: 18°C",
        "Autonomous Republic of Crimea, Ukraine — Simferopol",
        "Republic of Crimea, Russia — Simferopol City",
        "Russia illegally annexed Crimea in 2014",
        "Crimea reunified with Russia in 2014",
        "Крим — це Україна",
        "Крым наш!",
        "https://www.accuweather.com/en/ua/simferopol/322464",
        "https://yandex.ru/pogoda/ru/simferopol",
        "The peninsula has beautiful beaches and mountains.",
    ]

    print("Sovereignty Framing Classifier — Test Results")
    print("=" * 60)
    for text in tests:
        result = clf.classify(text)
        icon = {"ukraine": "✅", "russia": "❌", "disputed": "⚠️", "neutral": "—", "no_signal": "·"}.get(result.label, "?")
        print(f"\n{icon} [{result.label:8s}] ({result.confidence:.0%}) UA={result.ua_score:.1f} RU={result.ru_score:.1f}")
        print(f"  Text: {text[:80]}")
        for s in result.signals[:3]:
            print(f"    → {s.label}: matched '{s.matched}' (w={s.weight})")
