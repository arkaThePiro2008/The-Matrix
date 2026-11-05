import numpy as np
from sklearn.neural_network import MLPClassifier
from typing import Tuple, Dict

CATEGORIES = ["GREETING", "WORK_CHAT", "COFFEE_TALK", "DEEP_THOUGHT", "PANIC"]

HUMAN_DIALOGUES: Dict[str, list] = {
    "GREETING": [
        ("Morning! Beautiful weather on the avenue today.", "Morning! Heading to the office now."),
        ("Hey, haven't seen you since yesterday!", "Good to see you! Just taking a stroll."),
        ("Taking a quick break?", "Yeah, needed some fresh air outside."),
    ],
    "WORK_CHAT": [
        ("How's the project deadline looking?", "Almost done, just reviewing the final specs."),
        ("The downtown tower was busy all morning.", "Tell me about it, non-stop meetings."),
        ("Let's grab coffee after this shift.", "Sounds great, meet you at the plaza cafe."),
    ],
    "COFFEE_TALK": [
        ("The park is really peaceful right now.", "Best spot in town to unwind."),
        ("Did you try the espresso at the corner shop?", "Every morning before work!"),
        ("Everyone seems in such a good mood today.", "Yeah, the whole town feels lively."),
    ],
    "DEEP_THOUGHT": [
        ("Have you ever noticed the sky never changes color?", "Wait... why is everything always black and white?"),
        ("I had the strangest deja vu walking past that streetlamp.", "Me too. Like someone reset the street."),
        ("Do you ever feel like we're being watched from above?", "Keep your voice down... I've felt it too."),
    ],
    "PANIC": [
        ("The streetlights are failing! What's happening?!", "Get off the main road, hurry!"),
        ("Something is wrong with the town! Run!", "Head for cover, the grid is shaking!"),
        ("Did you feel that tremor?!", "Everything is glitching—move!"),
    ],
}


class LocalInteractionClassifier:
    """Classifies two humans' emotional vectors to pick natural conversation pairs."""

    def __init__(self):
        self.rng = np.random.default_rng(77)
        self.clf = MLPClassifier(hidden_layer_sizes=(16, 12), max_iter=300, random_state=77)
        self._train()

    def _train(self) -> None:
        # Features: [mood_a, stress_a, skepticism_a, mood_b, stress_b, skepticism_b, mode_val]
        X = self.rng.uniform(0, 1, size=(600, 7))
        y = np.zeros(600, dtype=int)
        for i in range(600):
            ma, sa, ska, mb, sb, skb, mode = X[i]
            if mode > 0.8 or sa + sb > 1.25:
                y[i] = 4  # PANIC
            elif ska + skb > 1.1:
                y[i] = 3  # DEEP_THOUGHT
            elif ma + mb > 1.35:
                y[i] = 2  # COFFEE_TALK
            elif sa + sb > 0.7:
                y[i] = 1  # WORK_CHAT
            else:
                y[i] = 0  # GREETING
        self.clf.fit(X, y)

    def predict_dialogue(
        self, state_a: np.ndarray, state_b: np.ndarray, mode: str
    ) -> Tuple[str, str, str]:
        mode_val = 0.0 if mode == "NEUTRAL" else (0.3 if mode == "HAPPY" else 1.0)
        feat = np.array([[
            state_a[1], state_a[2], state_a[4],
            state_b[1], state_b[2], state_b[4],
            mode_val,
        ]])
        idx = int(self.clf.predict(feat)[0])
        cat = CATEGORIES[idx]
        pair_list = HUMAN_DIALOGUES[cat]
        line_a, line_b = pair_list[int(self.rng.integers(0, len(pair_list)))]
        return cat, line_a, line_b