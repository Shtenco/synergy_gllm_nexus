from __future__ import annotations

class SemanticOperatorR:
    """Compatibility shell for the historical Ω-1.4R joblib artifact.

    The frozen object serializes only seed, vectorizer and clf on this class.
    Its historical inference contract is vectorizer.transform followed by
    classifier.predict. No weights or learned state are rebuilt here.
    """
    def predict(self, texts):
        return self.clf.predict(self.vectorizer.transform(texts))
