# THE MATRIX // 3D Urban Digital Twin & Autonomous Multi-Agent Simulation

![Python](https://img.shields.io/badge/Python-3.10%2B-black?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-WebSockets-black?style=for-the-badge&logo=fastapi&logoColor=white)
![Three.js](https://img.shields.io/badge/Three.js-WebGL_r128-black?style=for-the-badge&logo=threedotjs&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-Vectorized_AI-black?style=for-the-badge&logo=numpy&logoColor=white)
![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-MLP_Classifier-black?style=for-the-badge&logo=scikitlearn&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-Brutalist_HUD-black?style=for-the-badge&logo=streamlit&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-WAL_Mode-black?style=for-the-badge&logo=sqlite&logoColor=white)

> **A real-time, monochrome 3D virtual town inhabited by 100 autonomous human agents governed by vectorized Utility AI, $A^*$ sidewalk pathfinding, and a local neural interaction classifier—running at $60\text{ FPS}$ with zero external cloud LLM API costs.**

---

## 1. Overview

Traditional multi-agent simulations and open-world games face a sharp trade-off: simple rule-based NPCs follow repetitive loops and clip through geometry, whereas cloud-based Large Language Model (LLM) agents introduce multi-second network latency and high API costs when scaled to a crowd.

**THE MATRIX** solves this by decoupling an asynchronous $15\text{ Hz}$ Python simulation server (`FastAPI` + `NumPy` + `Scikit-Learn`) from a hardware-accelerated 3D WebGL viewport (`Three.js` inside `Streamlit`). Inside a structured monochrome city, **100 articulated 3D human agents** commute between their homes, downtown offices, cafes, and a central park strictly along paved sidewalks and zebra crosswalks. As the **Creator**, you can shift the global world state between **Neutral**, **Happy**, and **Chaos**, dilate the perception of time from $0.1\times$ bullet-time to $4.0\times$ hyper-speed, and monitor every citizen's live conversations in a collapsible sidebar.

---

## 2. Key Features

* **Structured 3D Monochrome Town (`world_grid.py`):** Features a $4 \times 4$ paved avenue grid, dashed lane markings, raised sidewalks, crosswalks, downtown office towers, residential houses with pitched roofs, storefront cafes, monochrome trees, and 64 streetlights.
* **Articulated 3D Humanoids & Sidewalk Routines (`agent_brain.py`):** Every citizen has a permanent Home, Workplace, and favorite Social Spot. Agents feature hierarchical shoulder and hip joints that swing naturally in sync with their walking speed and turn smoothly to face each other when conversing.
* **Zero-API Local Neural Dialogue (`emotion_classifier.py`):** A pre-trained `Scikit-Learn` Multi-Layer Perceptron (`MLPClassifier`) evaluates dual-agent emotional vectors on proximity encounters to trigger contextual face-to-face conversations and floating 3D speech bubbles.
* **The Creator Triad Console (`creator_controller.py`):** Instant global state injection switching the town between **NEUTRAL**, **HAPPY**, and **CHAOS** modes—altering walking speeds, conversation probabilities, ambient lighting, streetlight stability, and collective stress.
* **Perception of Time Dilation (`dashboard.py` & `main.py`):** A real-time slider scaling both backend simulation ticks and frontend limb kinematics from $0.1\times$ slow-motion to $4.0\times$ time-lapse.
* **Collapsible Live Bot Message Stream:** Slide-out right sidebar displaying real-time bot dialogues, job titles, and timestamps. Clicking any message card or 3D human locks the camera onto that citizen and opens their telemetry inspector.
* **Non-Blocking SQLite WAL Persistence (`database.py`):** Audits all proximity conversations and Creator mode shifts using Write-Ahead Logging (`PRAGMA journal_mode=WAL`) with zero frame drops.

---

## 3. System Architecture & Data Flow

The project uses a decoupled **Client–Server–Persistence** pipeline so server-side matrix math never blocks browser rendering:

1. **Entry Portal (`home.py`):** Renders a full-screen monochrome background video stream, scanline vignette overlay, and glowing `GET STARTED` portal button.
2. **Asynchronous Simulation Clock (`main.py`):** Launches automatically in a background daemon thread on port `8765`, stepping the population brain at $\approx 15\text{ Hz}$ (scaled by the Time Perception multiplier $\tau$) and broadcasting compact $14\text{ KB}$ JSON state deltas over WebSockets.
3. **Vectorized Spatial & Utility Brain (`agent_brain.py` & `world_grid.py`):** Updates the $100 \times 5$ internal drive matrix in $< 1.8\text{ ms}$ per tick and computes pedestrian routes over the `NetworkX` sidewalk graph.
4. **Edge ML & WAL Database (`emotion_classifier.py` & `database.py`):** Classifies pairwise encounters within $0.6\text{ m} < d < 2.55\text{ m}$ and commits dialogue records to `matrix_town.db`.
5. **60 FPS WebGL Viewport (`dashboard.py`):** Interpolates agent coordinates, animates limb pivots, projects 3D-to-2D HTML speech bubbles, and streams live messages into the collapsible sidebar.

---

## 4. Mathematical & Algorithmic Foundations

### 4.1 $A^*$ Sidewalk Pathfinding
The town sidewalk network is modeled as an undirected weighted graph $G = (V, E)$. Optimal pedestrian routes between homes, offices, and cafes are computed via the $A^*$ search algorithm using the admissible Manhattan distance heuristic:

$$f(n) = g(n) + h(n, g), \quad \text{where} \quad h(n, g) = |x_n - x_g| + |z_n - z_g|$$

Each agent $i$ applies a lateral sidewalk lane offset $\delta_i \in [-0.70, +0.70]\text{ m}$ so pedestrians walk side-by-side rather than overlapping on a single line.

### 4.2 Vectorized 5D Internal State Machine
Each citizen $i \in \{0, 1, \dots, 99\}$ maintains a normalized five-dimensional drive vector:

$$S_i(t) = \begin{bmatrix} E_i(t) & M_i(t) & St_i(t) & So_i(t) & Sk_i(t) \end{bmatrix}^T \in [0, 1]^5$$

representing **Energy** ($E_i$), **Mood** ($M_i$), **Stress** ($St_i$), **Social Drive** ($So_i$), and **Reality Skepticism** ($Sk_i$). Every tick, the population matrix $\mathbf{S} \in \mathbb{R}^{100 \times 5}$ drifts toward the active Creator Mode targets ($\mu_{\text{mood}}, \mu_{\text{stress}}$):

$$M_i(t+1) = M_i(t) + \alpha_m \left( \mu_{\text{mood}} - M_i(t) \right)$$

$$St_i(t+1) = St_i(t) + \alpha_s \left( \mu_{\text{stress}} - St_i(t) \right)$$

### 4.3 Local MLP Interaction Classifier
When two agents $a$ and $b$ enter conversational range on a sidewalk, a 7D feature vector $X_{a,b} = [M_a, St_a, Sk_a, M_b, St_b, Sk_b, C_{\text{mode}}]$ is passed through a two-layer $(16, 12)$ ReLU neural network to classify the encounter into **Greeting**, **Work Chat**, **Coffee Talk**, **Deep Thought**, or **Panic**. Both agents pause and orient their heading angle $\theta$ toward each other:

$$\theta = \text{atan2}(\Delta x, \Delta z)$$

### 4.4 Time-Perception Dilation & Limb Kinematics
The Time Perception slider controls a scalar $\tau \in [0.1, 4.0]$ that simultaneously scales the server sleep interval $\Delta t_{\text{tick}}$ and the frontend leg/arm swing oscillation $\phi_{\text{leg}}(t)$:

$$\Delta t_{\text{tick}} = \text{clip}\left( \frac{0.065}{\tau}, \, 0.014, \, 0.650 \right), \quad \phi_{\text{leg}}(t) = A \cdot \sin\left( \omega(t) \cdot v_i + \psi_i \right) \quad \left(\frac{d\omega}{dt} = 0.14 \cdot \tau\right)$$

---

## 5. Creator Triad Mode Parameters

| Creator Mode | Walk Speed | Talk Probability | Target Mood ($\mu_{\text{mood}}$) | Target Stress ($\mu_{\text{stress}}$) | Environmental & Behavioral Effect |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **NEUTRAL** | $0.34\text{ m/tick}$ | $3.5\%$ | $0.60$ | $0.20$ | Balanced daily commutes between homes, offices, and cafes under stark monochrome lighting. |
| **HAPPY** | $0.30\text{ m/tick}$ | $8.5\%$ | $0.92$ | $0.05$ | High-key illumination; citizens gravitate toward the central park and cafes with frequent chats. |
| **CHAOS** | $0.72\text{ m/tick}$ | $2.0\%$ | $0.15$ | $0.90$ | Streetlights flicker; citizens abandon work routines to flee rapidly while panic spreads. |

---

## 6. Project Directory Blueprint

```text
the-matrix-simulation/
├── home.py                 # Full-screen background video portal & "GET STARTED" entrypoint
├── dashboard.py            # Three.js 3D town viewport, top Creator bar & collapsible sidebar
├── main.py                 # FastAPI server, background daemon launcher & WebSocket streamer
├── agent_brain.py          # Vectorized 100-agent NumPy state machine & routine scheduler
├── world_grid.py           # Procedural 3D city block generator & NetworkX A* sidewalk graph
├── emotion_classifier.py   # Local Scikit-Learn MLP neural classifier & dialogue bank
├── creator_controller.py   # Global state tensors for Neutral, Happy, and Chaos modes
├── database.py             # Thread-safe SQLite WAL persistence engine (matrix_town.db)
├── style.css               # Monochrome brutalist stylesheet, scanlines & glow animations
└── requirements.txt        # Python package dependencies
```

---

## 7. Installation & Quick Start

### Prerequisites
* **Python 3.10+** installed on Windows, macOS, or Linux.
* A modern web browser with WebGL enabled (Chrome, Edge, Brave, or Firefox).

### Step 1: Clone the Repository & Install Dependencies
```bash
git clone https://github.com/your-username/the-matrix-simulation.git
cd the-matrix-simulation
pip install -r requirements.txt
```

### Step 2: Launch the Application
Run the Streamlit portal from `home.py`. When you click **GET STARTED**, `dashboard.py` will automatically launch the background FastAPI WebSocket engine on port `8765`:
```bash
streamlit run home.py
```

### Optional: Using a Local 4K Background Video
To avoid third-party CDN hotlink restrictions (`HTTP 403`) on 4K background videos, place any MP4 video named `matrix_bg.mp4` in the project root and expose it via `FileResponse` in `main.py` at `http://127.0.0.1:8765/video/bg`.

---

## 8. System Benchmarks

Tested on local hardware with **100 active articulated agents**, **32 textured buildings**, and **64 streetlights**:

* **NumPy Tick Computation Latency:** $< 1.8\text{ ms}$ per tick (supports up to $60\text{ ticks/sec}$ at $4.0\times$ hyper-speed).
* **3D WebGL Frame Rate:** Locked $60\text{ FPS}$ at $1080\text{p}$ resolution.
* **Total Memory Footprint:** $\approx 145\text{ MB}$ RAM (Python backend + MLP model + NetworkX graph + SQLite WAL).
* **WebSocket Frame Payload:** $\approx 14\text{ KB}$ serialized JSON per broadcast.

---

## 9. Real-World Engineering Applications

1. **Urban Digital Twins & Pedestrian Infrastructure:** Evaluates how sidewalk widths, crosswalk locations, and building zoning impact commuter bottlenecks before physical construction.
2. **Disaster & Evacuation Stress-Testing:** Models crowd panic propagation, fleeing velocities, and congestion points during emergencies (`CHAOS` mode).
3. **Epidemiological & Information Contagion Modeling:** Tracks exact pairwise spatial encounters across residential, workplace, and social hubs.
4. **Zero-Cost Autonomous Game NPC Engines:** Powers hundreds of reactive background citizens with daily schedules and contextual dialogue without cloud LLM latency or API bills.

---

## 10. Future Roadmap

* **Deep Q-Network (DQN) Reinforcement Learning:** Allow agents to learn optimal commuting times over multi-week cycles to avoid congested avenues.
* **Autonomous Vehicular Traffic Layer:** Add cars and transit buses along the asphalt road grid synchronized with pedestrian crosswalk signals.
* **Multi-Floor Interior Navigation Mesh:** Expand the 2D sidewalk graph into a 3D multi-story navigation mesh inside office towers and houses.

---

## 11. License & Credits

Developed as a **First-Year B.Tech Computer Science & Engineering Project (2026–2027)**. Released under the MIT License for educational and research use.