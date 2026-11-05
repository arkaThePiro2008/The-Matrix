from typing import Dict, Any


class CreatorController:
    """Controls the 3 Creator states (NEUTRAL, HAPPY, CHAOS) and how they affect town behavior."""

    MODES: Dict[str, Dict[str, Any]] = {
        "NEUTRAL": {
            "walk_speed": 0.34,
            "talk_chance": 0.035,
            "mood_target": 0.60,
            "stress_target": 0.20,
            "skeptic_drift": 0.0002,
        },
        "HAPPY": {
            "walk_speed": 0.30,
            "talk_chance": 0.085,
            "mood_target": 0.92,
            "stress_target": 0.05,
            "skeptic_drift": -0.0005,
        },
        "CHAOS": {
            "walk_speed": 0.72,
            "talk_chance": 0.020,
            "mood_target": 0.15,
            "stress_target": 0.90,
            "skeptic_drift": 0.0035,
        },
    }

    def __init__(self):
        self.current_mode = "NEUTRAL"

    def set_mode(self, mode: str) -> Dict[str, Any]:
        m = mode.upper()
        if m in self.MODES:
            self.current_mode = m
        return self.MODES[self.current_mode]

    def get_params(self) -> Dict[str, Any]:
        return self.MODES[self.current_mode]