import time
import numpy as np
from typing import List, Dict, Any, Tuple
from world_grid import TownGrid
from emotion_classifier import LocalInteractionClassifier
from creator_controller import CreatorController
import database

FIRST_NAMES = [
    "Liam", "Noah", "Elena", "Maya", "Lucas", "Sora", "Kael", "Vera", "Julian", "Nora",
    "Marcus", "Iris", "Devon", "Clara", "Zane", "Tessa", "Owen", "Freya", "Leo", "Aria",
]
OCCUPATIONS = [
    "Architect", "Data Analyst", "Barista", "Civil Engineer", "Journalist",
    "Systems Operator", "Urban Planner", "Archivist", "Grid Technician", "Designer",
]


class MatrixPopulationBrain:
    """Simulates 100 humans with homes, workplaces, sidewalk navigation, and live message streams."""

    def __init__(self, num_agents: int = 100):
        self.n = num_agents
        self.rng = np.random.default_rng(42)
        self.tick = 0
        self.time_scale = 1.0  # Controlled by the Time Perception slider (0.1x to 4.0x)
        self.town = TownGrid()
        self.classifier = LocalInteractionClassifier()
        self.creator = CreatorController()
        database.init_db()

        # State vectors: [Energy, Mood, Stress, Social, Skepticism]
        self.states = np.zeros((self.n, 5), dtype=np.float32)
        self.states[:, 0] = self.rng.uniform(0.45, 0.95, self.n)
        self.states[:, 1] = self.rng.uniform(0.50, 0.75, self.n)
        self.states[:, 2] = self.rng.uniform(0.10, 0.25, self.n)
        self.states[:, 3] = self.rng.uniform(0.40, 0.80, self.n)
        self.states[:, 4] = self.rng.uniform(0.05, 0.25, self.n)

        self.names = [f"{FIRST_NAMES[i % len(FIRST_NAMES)]}-{i:02d}" for i in range(self.n)]
        self.jobs = [OCCUPATIONS[i % len(OCCUPATIONS)] for i in range(self.n)]

        self.home_nodes = [self.town.homes[i % len(self.town.homes)] for i in range(self.n)]
        self.work_nodes = [self.town.workplaces[i % len(self.town.workplaces)] for i in range(self.n)]
        self.social_nodes = [self.town.social_spots[i % len(self.town.social_spots)] for i in range(self.n)]

        self.pos = np.zeros((self.n, 2), dtype=np.float32)
        self.vel = np.zeros((self.n, 2), dtype=np.float32)
        self.heading = np.zeros(self.n, dtype=np.float32)
        self.paths: List[List[Tuple[float, float]]] = [[] for _ in range(self.n)]

        self.activities = ["COMMUTING" for _ in range(self.n)]
        self.pause_timer = np.zeros(self.n, dtype=np.int32)
        self.chat_partner = np.full(self.n, -1, dtype=np.int32)
        self.speech_bubble = ["" for _ in range(self.n)]
        self.speech_ttl = np.zeros(self.n, dtype=np.int32)

        # Rolling feed of messages for the collapsible right sidebar
        self.msg_seq = 0
        self.message_feed: List[Dict[str, Any]] = []

        all_sidewalk_nodes = list(self.town.graph.nodes)
        for i in range(self.n):
            start_node = all_sidewalk_nodes[i % len(all_sidewalk_nodes)]
            jitter = self.rng.uniform(-0.8, 0.8, size=2)
            self.pos[i] = [start_node[0] + jitter[0], start_node[1] + jitter[1]]
            self._assign_next_destination(i)

    def set_time_scale(self, scale: float) -> float:
        self.time_scale = float(np.clip(scale, 0.1, 4.0))
        return self.time_scale

    def _assign_next_destination(self, i: int) -> None:
        mode = self.creator.current_mode
        energy, _, _, social, _ = self.states[i]

        if mode == "CHAOS":
            self.activities[i] = "FLEEING"
            all_nodes = list(self.town.graph.nodes)
            goal = all_nodes[int(self.rng.integers(0, len(all_nodes)))]
        elif mode == "HAPPY" and self.rng.random() < 0.65:
            self.activities[i] = "HANGING OUT"
            goal = self.town.social_spots[int(self.rng.integers(0, len(self.town.social_spots)))]
        else:
            roll = self.rng.random()
            if energy < 0.30:
                self.activities[i] = "HEADING HOME"
                goal = self.home_nodes[i]
            elif social < 0.45 or roll < 0.35:
                self.activities[i] = "COFFEE BREAK"
                goal = self.social_nodes[i]
            else:
                self.activities[i] = "GOING TO WORK"
                goal = self.work_nodes[i]

        path = self.town.find_path((float(self.pos[i, 0]), float(self.pos[i, 1])), goal)
        lane_shift = float((i % 5 - 2) * 0.35)
        self.paths[i] = [(p[0] + lane_shift, p[1] + lane_shift) for p in path]

    def set_mode(self, mode: str) -> None:
        prev = self.creator.current_mode
        self.creator.set_mode(mode)
        database.log_mode_change(self.tick, self.creator.current_mode)
        if prev != self.creator.current_mode:
            for i in range(self.n):
                if self.creator.current_mode == "CHAOS":
                    self.pause_timer[i] = 0
                    self._assign_next_destination(i)
                elif self.rng.random() < 0.5:
                    self._assign_next_destination(i)

    def _push_bot_message(self, agent_id: int, partner_id: int, category: str, text: str) -> None:
        self.msg_seq += 1
        entry = {
            "uid": self.msg_seq,
            "tick": self.tick,
            "agent_id": int(agent_id),
            "sender": self.names[agent_id],
            "job": self.jobs[agent_id],
            "partner": self.names[partner_id] if partner_id >= 0 else None,
            "category": category,
            "text": text,
            "time_str": time.strftime("%H:%M:%S"),
        }
        self.message_feed.append(entry)
        if len(self.message_feed) > 45:
            self.message_feed = self.message_feed[-45:]

    def step(self) -> Dict[str, Any]:
        self.tick += 1
        params = self.creator.get_params()
        mode = self.creator.current_mode

        self.states[:, 1] += (params["mood_target"] - self.states[:, 1]) * 0.03
        self.states[:, 2] += (params["stress_target"] - self.states[:, 2]) * 0.04
        self.states[:, 4] = np.clip(self.states[:, 4] + params["skeptic_drift"], 0.0, 1.0)

        active_bubbles = self.speech_ttl > 0
        self.speech_ttl[active_bubbles] -= 1
        for i in np.where(self.speech_ttl == 0)[0]:
            self.speech_bubble[i] = ""

        for i in range(self.n):
            if self.pause_timer[i] > 0:
                self.pause_timer[i] -= 1
                self.vel[i] = [0.0, 0.0]
                partner = self.chat_partner[i]
                if partner >= 0:
                    dx = self.pos[partner, 0] - self.pos[i, 0]
                    dz = self.pos[partner, 1] - self.pos[i, 1]
                    if dx * dx + dz * dz > 1e-4:
                        self.heading[i] = float(np.arctan2(dx, dz))
                if self.pause_timer[i] == 0:
                    self.chat_partner[i] = -1
                    if not self.paths[i]:
                        self._assign_next_destination(i)
                continue

            if not self.paths[i]:
                if self.activities[i] == "GOING TO WORK":
                    self.activities[i] = "WORKING"
                    self.pause_timer[i] = int(self.rng.integers(35, 75))
                    self.states[i, 0] = max(0.1, float(self.states[i, 0] - 0.12))
                elif self.activities[i] == "HEADING HOME":
                    self.activities[i] = "RESTING AT HOME"
                    self.pause_timer[i] = int(self.rng.integers(40, 80))
                    self.states[i, 0] = min(1.0, float(self.states[i, 0] + 0.35))
                elif self.activities[i] in ("COFFEE BREAK", "HANGING OUT"):
                    self.activities[i] = "RELAXING"
                    self.pause_timer[i] = int(self.rng.integers(25, 55))
                    self.states[i, 3] = min(1.0, float(self.states[i, 3] + 0.25))
                else:
                    self._assign_next_destination(i)
                continue

            wx, wz = self.paths[i][0]
            dx = wx - float(self.pos[i, 0])
            dz = wz - float(self.pos[i, 1])
            dist = float(np.hypot(dx, dz))

            speed = params["walk_speed"] * (0.88 + 0.24 * (i % 5) / 4.0)
            if dist <= speed:
                self.pos[i] = [wx, wz]
                self.paths[i].pop(0)
            else:
                vx = (dx / dist) * speed
                vz = (dz / dist) * speed
                self.pos[i, 0] += vx
                self.pos[i, 1] += vz
                self.vel[i] = [vx, vz]
                self.heading[i] = float(np.arctan2(vx, vz))

        self._trigger_human_conversations(params["talk_chance"], mode)
        return self.get_state_payload()

    def _trigger_human_conversations(self, talk_chance: float, mode: str) -> None:
        diff_x = self.pos[:, 0, None] - self.pos[None, :, 0]
        diff_z = self.pos[:, 1, None] - self.pos[None, :, 1]
        dist_sq = diff_x * diff_x + diff_z * diff_z
        np.fill_diagonal(dist_sq, 9999.0)

        close_pairs = np.argwhere((dist_sq > 0.6) & (dist_sq < 6.5))
        used = set()
        triggered = 0

        for a, b in close_pairs:
            a, b = int(a), int(b)
            if a > b or a in used or b in used:
                continue
            if self.pause_timer[a] > 0 or self.pause_timer[b] > 0:
                continue
            if self.rng.random() > talk_chance:
                continue

            used.add(a)
            used.add(b)
            cat, line_a, line_b = self.classifier.predict_dialogue(self.states[a], self.states[b], mode)

            duration = 38 if mode != "CHAOS" else 18
            self.pause_timer[a] = duration
            self.pause_timer[b] = duration
            self.chat_partner[a] = b
            self.chat_partner[b] = a
            self.activities[a] = "TALKING"
            self.activities[b] = "TALKING"

            self.speech_bubble[a] = line_a
            self.speech_ttl[a] = duration
            self.speech_bubble[b] = line_b
            self.speech_ttl[b] = duration

            # Push both bots' messages to the live sidebar feed
            self._push_bot_message(a, b, cat, line_a)
            self._push_bot_message(b, a, cat, line_b)
            database.log_dialogue(self.tick, a, b, cat, line_a)

            triggered += 1
            if triggered >= 2:
                break

    def get_state_payload(self) -> Dict[str, Any]:
        agents_out = []
        for i in range(self.n):
            speed = float(np.hypot(self.vel[i, 0], self.vel[i, 1]))
            agents_out.append({
                "id": i,
                "name": self.names[i],
                "job": self.jobs[i],
                "x": round(float(self.pos[i, 0]), 2),
                "z": round(float(self.pos[i, 1]), 2),
                "h": round(float(self.heading[i]), 3),
                "spd": round(speed, 3),
                "act": self.activities[i],
                "mood": round(float(self.states[i, 1]), 2),
                "stress": round(float(self.states[i, 2]), 2),
                "skep": round(float(self.states[i, 4]), 2),
                "msg": self.speech_bubble[i],
            })
        return {
            "tick": self.tick,
            "mode": self.creator.current_mode,
            "time_scale": round(self.time_scale, 2),
            "agents": agents_out,
            "messages": self.message_feed[-30:],
        }