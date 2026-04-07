"""
Sovereignty Framing Classifier for Crimea — v2

Single classifier used by ALL scanners (GDELT, academic, any future source).
Signals are defined in sovereignty_signals.py — this file only does matching + scoring.

Usage:
    from sovereignty_classifier import SovereigntyClassifier
    clf = SovereigntyClassifier()
    result = clf.classify("Weather in Simferopol, Russia today...")
"""

import re
from dataclasses import dataclass, field

from sovereignty_signals import ALL_SIGNALS, CRIMEA_REFERENCE


@dataclass
class Signal:
    """A single sovereignty signal detected in text."""
    matched: str
    direction: str  # "ukraine" or "russia"
    weight: float
    signal_type: str
    context: str = ""


@dataclass
class ClassificationResult:
    label: str  # "ukraine", "russia", "disputed", "no_signal"
    confidence: float
    signals: list[Signal] = field(default_factory=list)
    ua_score: float = 0.0
    ru_score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "confidence": round(self.confidence, 3),
            "ua_score": round(self.ua_score, 3),
            "ru_score": round(self.ru_score, 3),
            "signal_count": len(self.signals),
            "signals": [
                {"matched": s.matched, "direction": s.direction,
                 "weight": s.weight, "type": s.signal_type}
                for s in self.signals
            ],
        }


class SovereigntyClassifier:
    """Classifies text for Crimea sovereignty framing using 81 signals in 3 languages."""

    def __init__(self):
        self._signals = ALL_SIGNALS

    def has_crimea_reference(self, text: str) -> bool:
        """Quick check: does the text mention Crimea?"""
        return bool(CRIMEA_REFERENCE.search(text))

    def classify(self, text: str) -> ClassificationResult:
        """Classify text for sovereignty framing."""
        signals = []

        for regex, direction, weight, sig_type in self._signals:
            for match in regex.finditer(text):
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                signals.append(Signal(
                    matched=match.group(),
                    direction=direction,
                    weight=weight,
                    signal_type=sig_type,
                    context=text[start:end].strip(),
                ))

        if not signals:
            return ClassificationResult("no_signal", 0.0)

        ua_score = sum(s.weight for s in signals if s.direction == "ukraine")
        ru_score = sum(s.weight for s in signals if s.direction == "russia")
        total = ua_score + ru_score

        if total == 0:
            return ClassificationResult("no_signal", 0.0, signals, ua_score, ru_score)

        if ua_score > ru_score:
            confidence = min(0.95, ua_score / total)
            return ClassificationResult("ukraine", confidence, signals, ua_score, ru_score)
        elif ru_score > ua_score:
            confidence = min(0.95, ru_score / total)
            return ClassificationResult("russia", confidence, signals, ua_score, ru_score)
        else:
            return ClassificationResult("disputed", 0.5, signals, ua_score, ru_score)


if __name__ == "__main__":
    clf = SovereigntyClassifier()

    tests = [
        # English
        ("Weather in Simferopol, Ukraine today: 18°C", "ukraine"),
        ("Weather in Simferopol, Russia: 18°C", "russia"),
        ("Autonomous Republic of Crimea, Ukraine", "ukraine"),
        ("Republic of Crimea, Russia — Simferopol", "russia"),
        ("Russia illegally annexed Crimea in 2014", "ukraine"),
        ("Crimea reunified with Russia in 2014", "russia"),
        ("Crimea as part of Russia since 2014", "russia"),
        ("Temporarily occupied Crimea", "ukraine"),
        ("International Crimea Platform summit", "ukraine"),
        # Russian
        ("Крым наш!", "russia"),
        ("Воссоединение Крыма с Россией", "russia"),
        ("Оккупированный Крым", "ukraine"),
        ("Республика Крым, Россия", "russia"),
        # Ukrainian
        ("Крим — це Україна", "ukraine"),
        ("Тимчасово окупований Крим", "ukraine"),
        ("Деокупація Криму", "ukraine"),
        # Neutral (no signal)
        ("Beautiful beaches on the peninsula", "no_signal"),
        ("A random article about nothing", "no_signal"),
    ]

    print("Sovereignty Classifier v2 — Test Results")
    print(f"81 signals across 3 languages")
    print("=" * 60)

    correct = 0
    for text, expected in tests:
        result = clf.classify(text)
        ok = result.label == expected
        correct += ok
        icon = "✓" if ok else "✗"
        status = {"ukraine": "✅", "russia": "❌", "disputed": "⚠️", "no_signal": "·"}.get(result.label, "?")
        print(f"  {icon} {status} [{result.label:10s}] (expect={expected:10s}) {text[:55]}")
        if not ok:
            print(f"    WRONG! Got signals: {[s.matched for s in result.signals]}")

    print(f"\n{correct}/{len(tests)} correct")
