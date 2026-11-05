import json
import time
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components
import main as backend_server


def load_css() -> None:
    css_path = Path("style.css")
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


def build_fullscreen_3d_town(map_data: dict, initial_state: dict, ws_port: int = 8765) -> str:
    map_json = json.dumps(map_data)
    init_json = json.dumps(initial_state)

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            * {{ box-sizing: border-box; user-select: none; }}
            body {{
                margin: 0; overflow: hidden; background: #070707;
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, monospace;
                color: #f5f5f5;
            }}

            /* --- TOP BAR (With HOME Button + 3 Creator Modes) --- */
            #top-bar {{
                position: absolute; top: 18px; left: 50%; transform: translateX(-50%);
                display: flex; align-items: center; gap: 10px;
                background: rgba(10, 10, 10, 0.84);
                border: 1px solid rgba(255, 255, 255, 0.22);
                padding: 8px 14px; border-radius: 6px;
                backdrop-filter: blur(12px); z-index: 20;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.65);
            }}
            .home-btn {{
                background: rgba(255, 255, 255, 0.08); color: #ffffff;
                border: 1px solid rgba(255, 255, 255, 0.35);
                padding: 7px 14px; border-radius: 4px;
                font-family: monospace; font-size: 12px; font-weight: 700;
                letter-spacing: 0.14em; cursor: pointer;
                transition: all 0.2s ease;
            }}
            .home-btn:hover {{
                background: #ffffff; color: #000000;
                box-shadow: 0 0 16px rgba(255, 255, 255, 0.8);
            }}
            .divider {{
                width: 1px; height: 20px; background: rgba(255, 255, 255, 0.18);
                margin: 0 2px;
            }}
            .brand {{
                font-family: monospace; font-weight: 800; font-size: 13px;
                letter-spacing: 0.2em; padding: 0 6px;
            }}
            .mode-btn {{
                background: transparent; color: #bbbbbb;
                border: 1px solid rgba(255, 255, 255, 0.2);
                padding: 7px 16px; border-radius: 4px;
                font-family: monospace; font-size: 12px; font-weight: 700;
                letter-spacing: 0.14em; cursor: pointer;
                transition: all 0.2s ease;
            }}
            .mode-btn:hover {{
                color: #ffffff; border-color: #ffffff;
                box-shadow: 0 0 12px rgba(255, 255, 255, 0.35);
            }}
            .mode-btn.active {{
                background: #ffffff; color: #000000; border-color: #ffffff;
                box-shadow: 0 0 18px rgba(255, 255, 255, 0.75);
            }}

            /* --- COLLAPSIBLE RIGHT SIDEBAR (Time Perception + Bot Message Feed) --- */
            #right-sidebar {{
                position: absolute; top: 0; right: 0;
                width: 340px; height: 100vh;
                background: rgba(8, 8, 8, 0.88);
                border-left: 1px solid rgba(255, 255, 255, 0.22);
                backdrop-filter: blur(14px);
                display: flex; flex-direction: column;
                z-index: 25;
                transition: transform 0.32s cubic-bezier(0.16, 1, 0.3, 1);
                box-shadow: -10px 0 35px rgba(0, 0, 0, 0.7);
            }}
            #right-sidebar.collapsed {{
                transform: translateX(340px);
            }}
            #sidebar-toggle {{
                position: absolute; left: -38px; top: 50%;
                transform: translateY(-50%);
                width: 38px; height: 76px;
                background: rgba(10, 10, 10, 0.9);
                border: 1px solid rgba(255, 255, 255, 0.25);
                border-right: none;
                border-radius: 6px 0 0 6px;
                color: #ffffff; font-family: monospace; font-size: 14px;
                cursor: pointer; display: flex; align-items: center; justify-content: center;
                box-shadow: -6px 0 18px rgba(0, 0, 0, 0.5);
                transition: background 0.2s;
            }}
            #sidebar-toggle:hover {{
                background: #ffffff; color: #000000;
            }}

            /* Time Perception Control Section */
            .sidebar-section {{
                padding: 16px 18px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.14);
            }}
            .sec-header {{
                display: flex; justify-content: space-between; align-items: center;
                font-family: monospace; font-size: 11px; font-weight: 700;
                letter-spacing: 0.16em; color: #aaaaaa; margin-bottom: 10px;
            }}
            .time-badge {{
                color: #000000; background: #ffffff;
                padding: 2px 7px; border-radius: 3px; font-weight: 800;
            }}
            input[type=range].time-slider {{
                -webkit-appearance: none; width: 100%; height: 5px;
                background: rgba(255, 255, 255, 0.2); border-radius: 3px; outline: none;
            }}
            input[type=range].time-slider::-webkit-slider-thumb {{
                -webkit-appearance: none; width: 16px; height: 16px;
                border-radius: 50%; background: #ffffff; cursor: pointer;
                box-shadow: 0 0 12px rgba(255, 255, 255, 0.9);
            }}
            .scale-presets {{
                display: flex; justify-content: space-between; margin-top: 8px;
                font-family: monospace; font-size: 10px; color: #777;
            }}
            .scale-presets span {{ cursor: pointer; transition: color 0.15s; }}
            .scale-presets span:hover {{ color: #fff; }}

            /* Live Bot Messages Stream */
            .feed-header {{
                padding: 12px 18px 8px 18px;
                font-family: monospace; font-size: 11px; font-weight: 700;
                letter-spacing: 0.16em; color: #aaaaaa;
                display: flex; justify-content: space-between;
            }}
            #msg-feed {{
                flex: 1; overflow-y: auto; padding: 8px 16px 18px 16px;
                display: flex; flex-direction: column; gap: 9px;
            }}
            #msg-feed::-webkit-scrollbar {{ width: 4px; }}
            #msg-feed::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,0.25); border-radius: 2px; }}

            .msg-card {{
                background: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-left: 3px solid #ffffff;
                border-radius: 4px; padding: 9px 11px;
                cursor: pointer; transition: all 0.18s ease;
            }}
            .msg-card:hover {{
                background: rgba(255, 255, 255, 0.11);
                border-color: rgba(255, 255, 255, 0.45);
            }}
            .msg-meta {{
                display: flex; justify-content: space-between; align-items: center;
                font-family: monospace; font-size: 10px; color: #999; margin-bottom: 4px;
            }}
            .msg-sender {{ color: #ffffff; font-weight: 700; font-size: 11px; }}
            .msg-text {{ font-size: 12px; color: #e8e8e8; line-height: 1.4; }}

            /* Click-to-Inspect Card (Bottom-Left) */
            #inspect-card {{
                position: absolute; bottom: 52px; left: 20px; width: 255px;
                background: rgba(10, 10, 10, 0.88);
                border: 1px solid rgba(255, 255, 255, 0.28);
                border-radius: 6px; padding: 13px 15px;
                backdrop-filter: blur(10px); z-index: 15;
                display: none;
            }}
            #inspect-card h4 {{ margin: 0 0 3px 0; font-size: 14px; }}
            .sub-meta {{ font-size: 11px; color: #999; margin-bottom: 9px; font-family: monospace; }}
            .stat-line {{
                display: flex; justify-content: space-between;
                font-size: 12px; margin: 4px 0; color: #ddd;
            }}

            /* Floating 3D Speech Bubbles */
            #bubble-layer {{
                position: absolute; inset: 0; pointer-events: none; overflow: hidden; z-index: 5;
            }}
            .speech-bubble {{
                position: absolute; transform: translate(-50%, -100%);
                background: rgba(255, 255, 255, 0.94); color: #050505;
                padding: 5px 10px; border-radius: 4px;
                font-size: 11px; font-weight: 600; max-width: 190px;
                text-align: center; box-shadow: 0 4px 14px rgba(0,0,0,0.5);
                white-space: normal; line-height: 1.3;
            }}
            .speech-bubble::after {{
                content: ''; position: absolute; top: 100%; left: 50%;
                transform: translateX(-50%);
                border-width: 5px; border-style: solid;
                border-color: rgba(255,255,255,0.94) transparent transparent transparent;
            }}
            #controls-hint {{
                position: absolute; bottom: 16px; left: 20px;
                font-family: monospace; font-size: 11px; color: #888;
                background: rgba(8, 8, 8, 0.72); padding: 6px 10px;
                border-radius: 4px; border: 1px solid rgba(255,255,255,0.12);
                pointer-events: none; z-index: 15;
            }}
        </style>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    </head>
    <body>
        <!-- TOP BAR WITH HOME BUTTON & CREATOR MODES -->
        <div id="top-bar">
            <button class="home-btn" onclick="goHome()">⌂ HOME</button>
            <div class="divider"></div>
            <div class="brand">THE MATRIX</div>
            <button class="mode-btn active" id="btn-NEUTRAL" onclick="setMode('NEUTRAL')">NEUTRAL</button>
            <button class="mode-btn" id="btn-HAPPY" onclick="setMode('HAPPY')">HAPPY</button>
            <button class="mode-btn" id="btn-CHAOS" onclick="setMode('CHAOS')">CHAOS</button>
        </div>

        <!-- COLLAPSIBLE RIGHT SIDEBAR: TIME PERCEPTION SLIDER + BOT MESSAGE STREAM -->
        <div id="right-sidebar">
            <button id="sidebar-toggle" onclick="toggleSidebar()" title="Collapse / Expand Sidebar">▶</button>

            <div class="sidebar-section">
                <div class="sec-header">
                    <span>PERCEPTION OF TIME</span>
                    <span class="time-badge" id="time-readout">1.0x NORMAL</span>
                </div>
                <input
                    type="range" class="time-slider" id="time-slider"
                    min="0.1" max="4.0" step="0.1" value="1.0"
                    oninput="onTimeSliderChange(this.value)"
                >
                <div class="scale-presets">
                    <span onclick="setTimeScale(0.2)">0.2x SLOW-MO</span>
                    <span onclick="setTimeScale(1.0)">1.0x REAL</span>
                    <span onclick="setTimeScale(2.5)">2.5x FAST</span>
                    <span onclick="setTimeScale(4.0)">4.0x HYPER</span>
                </div>
            </div>

            <div class="feed-header">
                <span>TOWN BOT MESSAGES</span>
                <span id="msg-count-label">LIVE</span>
            </div>
            <div id="msg-feed"></div>
        </div>

        <div id="bubble-layer"></div>

        <div id="inspect-card">
            <h4 id="card-name">Liam-01</h4>
            <div class="sub-meta" id="card-job">Architect</div>
            <div class="stat-line"><span>Status</span><span id="card-act">Walking</span></div>
            <div class="stat-line"><span>Mood</span><span id="card-mood">70%</span></div>
            <div class="stat-line"><span>Stress</span><span id="card-stress">15%</span></div>
            <div class="stat-line"><span>Skepticism</span><span id="card-skep">10%</span></div>
        </div>

        <div id="controls-hint">
            Left-Drag: Rotate &nbsp;|&nbsp; Right-Drag: Pan &nbsp;|&nbsp; Scroll: Zoom &nbsp;|&nbsp; Click Human or Message: Focus
        </div>

        <script>
            const MAP = {map_json};
            let STATE = {init_json};
            let selectedAgentId = null;
            let timeScale = STATE.time_scale || 1.0;
            let lastRenderedMsgUid = 0;

            // --- NAVIGATION BACK TO HOME.PY ---
            function goHome() {{
                try {{
                    const parentUrl = new URL(window.parent.location.href);
                    parentUrl.searchParams.set('view', 'home');
                    window.parent.location.href = parentUrl.toString();
                }} catch (e) {{
                    window.location.search = '?view=home';
                }}
            }}

            // --- COLLAPSIBLE SIDEBAR TOGGLE ---
            function toggleSidebar() {{
                const sb = document.getElementById('right-sidebar');
                const btn = document.getElementById('sidebar-toggle');
                sb.classList.toggle('collapsed');
                btn.innerText = sb.classList.contains('collapsed') ? '◀' : '▶';
            }}

            // --- TIME PERCEPTION SLIDER CONTROL ---
            function formatTimeBadge(val) {{
                const v = parseFloat(val).toFixed(1);
                if (v <= 0.4) return v + 'x BULLET-TIME';
                if (v < 0.9) return v + 'x SLOW-MO';
                if (v <= 1.1) return v + 'x NORMAL';
                if (v <= 2.5) return v + 'x FAST';
                return v + 'x HYPER-SPEED';
            }}

            function setTimeScale(val) {{
                const slider = document.getElementById('time-slider');
                slider.value = val;
                onTimeSliderChange(val);
            }}

            function onTimeSliderChange(val) {{
                timeScale = parseFloat(val);
                document.getElementById('time-readout').innerText = formatTimeBadge(timeScale);
                if (ws && ws.readyState === WebSocket.OPEN) {{
                    ws.send(JSON.stringify({{ type: "TIME_SCALE", value: timeScale }}));
                }} else {{
                    fetch("http://127.0.0.1:{ws_port}/timescale/" + timeScale, {{ method: "POST" }});
                }}
            }}

            // --- 1. SCENE, CAMERA & RENDERER ---
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0x0c0c0c);
            scene.fog = new THREE.FogExp2(0x0c0c0c, 0.0045);

            const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.5, 600);
            camera.position.set(0, 65, 95);

            const renderer = new THREE.WebGLRenderer({{ antialias: true }});
            renderer.setSize(window.innerWidth, window.innerHeight);
            renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
            document.body.appendChild(renderer.domElement);

            const controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.06;
            controls.maxPolarAngle = Math.PI / 2.05;
            controls.minDistance = 12;
            controls.maxDistance = 220;

            // --- 2. LIGHTING ---
            const hemiLight = new THREE.HemisphereLight(0xffffff, 0x222222, 0.65);
            scene.add(hemiLight);
            const dirLight = new THREE.DirectionalLight(0xffffff, 0.75);
            dirLight.position.set(60, 110, 50);
            scene.add(dirLight);

            // --- 3. MONOCHROME 3D TOWN GEOMETRY ---
            const ground = new THREE.Mesh(
                new THREE.PlaneGeometry(220, 220),
                new THREE.MeshLambertMaterial({{ color: 0x242424 }})
            );
            ground.rotation.x = -Math.PI / 2;
            ground.position.y = -0.05;
            scene.add(ground);

            const parkLawn = new THREE.Mesh(
                new THREE.BoxGeometry(28, 0.15, 28),
                new THREE.MeshLambertMaterial({{ color: 0x333333 }})
            );
            parkLawn.position.set(0, 0.05, 0);
            scene.add(parkLawn);

            const fountainBase = new THREE.Mesh(
                new THREE.CylinderGeometry(3.2, 3.6, 0.8, 24),
                new THREE.MeshLambertMaterial({{ color: 0x888888 }})
            );
            fountainBase.position.set(0, 0.4, 0);
            scene.add(fountainBase);

            const obelisk = new THREE.Mesh(
                new THREE.ConeGeometry(1.1, 6.5, 4),
                new THREE.MeshLambertMaterial({{ color: 0xeaeaea }})
            );
            obelisk.position.set(0, 3.6, 0);
            scene.add(obelisk);

            const roadMat = new THREE.MeshLambertMaterial({{ color: 0x111111 }});
            const dashMat = new THREE.MeshBasicMaterial({{ color: 0x888888 }});

            MAP.roads.forEach(coord => {{
                const nsRoad = new THREE.Mesh(new THREE.PlaneGeometry(MAP.road_width, 180), roadMat);
                nsRoad.rotation.x = -Math.PI / 2;
                nsRoad.position.set(coord, 0.01, 0);
                scene.add(nsRoad);

                const ewRoad = new THREE.Mesh(new THREE.PlaneGeometry(180, MAP.road_width), roadMat);
                ewRoad.rotation.x = -Math.PI / 2;
                ewRoad.position.set(0, 0.015, coord);
                scene.add(ewRoad);

                for (let d = -80; d <= 80; d += 8) {{
                    const nsDash = new THREE.Mesh(new THREE.PlaneGeometry(0.25, 3.2), dashMat);
                    nsDash.rotation.x = -Math.PI / 2;
                    nsDash.position.set(coord, 0.025, d);
                    scene.add(nsDash);

                    const ewDash = new THREE.Mesh(new THREE.PlaneGeometry(3.2, 0.25), dashMat);
                    ewDash.rotation.x = -Math.PI / 2;
                    ewDash.position.set(d, 0.025, coord);
                    scene.add(ewDash);
                }}
            }});

            function createBuildingTexture(type) {{
                const canvas = document.createElement('canvas');
                canvas.width = 128; canvas.height = 256;
                const ctx = canvas.getContext('2d');
                ctx.fillStyle = type === 'HOUSE' ? '#2c2c2c' : '#1b1b1b';
                ctx.fillRect(0, 0, 128, 256);

                const rows = type === 'HOUSE' ? 3 : 12;
                const cols = type === 'HOUSE' ? 3 : 4;
                const padX = 10, padY = 12;
                const winW = (128 - padX * (cols + 1)) / cols;
                const winH = (230 - padY * (rows + 1)) / rows;

                for (let r = 0; r < rows; r++) {{
                    for (let c = 0; c < cols; c++) {{
                        const lit = Math.random() > 0.32;
                        ctx.fillStyle = lit ? (Math.random() > 0.4 ? '#d8d8d8' : '#8c8c8c') : '#0d0d0d';
                        ctx.fillRect(padX + c * (winW + padX), padY + r * (winH + padY), winW, winH);
                    }}
                }}
                return new THREE.CanvasTexture(canvas);
            }}

            const officeTex = createBuildingTexture('OFFICE');
            const houseTex = createBuildingTexture('HOUSE');

            MAP.buildings.forEach(b => {{
                const bGroup = new THREE.Group();
                bGroup.position.set(b.x, 0, b.z);

                const bodyGeom = new THREE.BoxGeometry(b.w, b.h, b.d);
                const bodyMesh = new THREE.Mesh(
                    bodyGeom,
                    new THREE.MeshLambertMaterial({{ map: b.type === 'HOUSE' ? houseTex : officeTex }})
                );
                bodyMesh.position.y = b.h / 2;
                bGroup.add(bodyMesh);

                const edges = new THREE.EdgesGeometry(bodyGeom);
                const edgeLines = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({{ color: 0x555555 }}));
                edgeLines.position.y = b.h / 2;
                bGroup.add(edgeLines);

                if (b.type === 'HOUSE') {{
                    const roofGeom = new THREE.ConeGeometry(b.w * 0.78, 3.6, 4);
                    roofGeom.rotateY(Math.PI / 4);
                    const roof = new THREE.Mesh(roofGeom, new THREE.MeshLambertMaterial({{ color: 0x444444 }}));
                    roof.position.y = b.h + 1.8;
                    bGroup.add(roof);
                }} else if (b.type === 'CAFE' || b.type === 'SHOP') {{
                    const awning = new THREE.Mesh(
                        new THREE.BoxGeometry(b.w + 1.2, 0.5, 2.2),
                        new THREE.MeshBasicMaterial({{ color: 0xd0d0d0 }})
                    );
                    awning.position.set(0, 3.2, b.d / 2 + 0.8);
                    bGroup.add(awning);
                }}
                scene.add(bGroup);
            }});

            const trunkMat = new THREE.MeshLambertMaterial({{ color: 0x3a3a3a }});
            const foliageMat = new THREE.MeshLambertMaterial({{ color: 0x7a7a7a }});
            MAP.trees.forEach(t => {{
                const tree = new THREE.Group();
                const trunk = new THREE.Mesh(new THREE.CylinderGeometry(0.28, 0.4, 2.4, 8), trunkMat);
                trunk.position.y = 1.2;
                tree.add(trunk);
                const canopy1 = new THREE.Mesh(new THREE.SphereGeometry(1.7 * t.scale, 10, 10), foliageMat);
                canopy1.position.y = 3.2;
                tree.add(canopy1);
                const canopy2 = new THREE.Mesh(new THREE.SphereGeometry(1.2 * t.scale, 10, 10), foliageMat);
                canopy2.position.set(0.6, 4.1, 0.4);
                tree.add(canopy2);
                tree.position.set(t.x, 0, t.z);
                scene.add(tree);
            }});

            const poleMat = new THREE.MeshLambertMaterial({{ color: 0x666666 }});
            const bulbMat = new THREE.MeshBasicMaterial({{ color: 0xffffff }});
            const streetBulbs = [];
            MAP.streetlights.forEach(sl => {{
                const lamp = new THREE.Group();
                const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.16, 5.2, 8), poleMat);
                pole.position.y = 2.6;
                lamp.add(pole);
                const bulb = new THREE.Mesh(new THREE.SphereGeometry(0.35, 8, 8), bulbMat);
                bulb.position.y = 5.3;
                lamp.add(bulb);
                streetBulbs.push(bulb);
                lamp.position.set(sl.x, 0, sl.z);
                scene.add(lamp);
            }});

            // --- 4. ARTICULATED 3D HUMANS ---
            const humans = {{}};
            const pickableTorsoMeshes = [];

            function createHumanModel(agent) {{
                const root = new THREE.Group();
                root.position.set(agent.x, 0, agent.z);

                const suitShade = 120 + (agent.id % 5) * 25;
                const clothesMat = new THREE.MeshLambertMaterial({{
                    color: new THREE.Color(`rgb(${{suitShade}}, ${{suitShade}}, ${{suitShade}})`)
                }});
                const skinMat = new THREE.MeshLambertMaterial({{ color: 0xf0f0f0 }});
                const darkMat = new THREE.MeshLambertMaterial({{ color: 0x303030 }});

                const head = new THREE.Mesh(new THREE.SphereGeometry(0.32, 12, 12), skinMat);
                head.position.y = 2.05;
                root.add(head);

                const torso = new THREE.Mesh(new THREE.BoxGeometry(0.62, 0.85, 0.34), clothesMat);
                torso.position.y = 1.38;
                torso.userData = {{ agentId: agent.id }};
                root.add(torso);
                pickableTorsoMeshes.push(torso);

                const leftArmPivot = new THREE.Group();
                leftArmPivot.position.set(-0.42, 1.72, 0);
                const leftArm = new THREE.Mesh(new THREE.BoxGeometry(0.18, 0.68, 0.18), clothesMat);
                leftArm.position.y = -0.30;
                leftArmPivot.add(leftArm);
                root.add(leftArmPivot);

                const rightArmPivot = new THREE.Group();
                rightArmPivot.position.set(0.42, 1.72, 0);
                const rightArm = new THREE.Mesh(new THREE.BoxGeometry(0.18, 0.68, 0.18), clothesMat);
                rightArm.position.y = -0.30;
                rightArmPivot.add(rightArm);
                root.add(rightArmPivot);

                const leftLegPivot = new THREE.Group();
                leftLegPivot.position.set(-0.17, 0.92, 0);
                const leftLeg = new THREE.Mesh(new THREE.BoxGeometry(0.22, 0.85, 0.22), darkMat);
                leftLeg.position.y = -0.42;
                leftLegPivot.add(leftLeg);
                root.add(leftLegPivot);

                const rightLegPivot = new THREE.Group();
                rightLegPivot.position.set(0.17, 0.92, 0);
                const rightLeg = new THREE.Mesh(new THREE.BoxGeometry(0.22, 0.85, 0.22), darkMat);
                rightLeg.position.y = -0.42;
                rightLegPivot.add(rightLeg);
                root.add(rightLegPivot);

                const selRing = new THREE.Mesh(
                    new THREE.RingGeometry(0.55, 0.78, 20),
                    new THREE.MeshBasicMaterial({{ color: 0xffffff, side: THREE.DoubleSide }})
                );
                selRing.rotation.x = -Math.PI / 2;
                selRing.position.y = 0.04;
                selRing.visible = false;
                root.add(selRing);

                const bubble = document.createElement('div');
                bubble.className = 'speech-bubble';
                bubble.style.display = 'none';
                document.getElementById('bubble-layer').appendChild(bubble);

                scene.add(root);
                return {{
                    root, leftArmPivot, rightArmPivot, leftLegPivot, rightLegPivot, selRing, bubble,
                    targetX: agent.x, targetZ: agent.z, targetH: agent.h,
                    speed: agent.spd, phase: agent.id * 0.7, data: agent
                }};
            }}

            STATE.agents.forEach(a => {{
                humans[a.id] = createHumanModel(a);
            }});

            // --- 5. BOT MESSAGE FEED UPDATER ---
            function syncMessageSidebar(messages) {{
                if (!messages || messages.length === 0) return;
                const feedEl = document.getElementById('msg-feed');
                let added = false;

                messages.forEach(m => {{
                    if (m.uid > lastRenderedMsgUid) {{
                        lastRenderedMsgUid = m.uid;
                        added = true;
                        const card = document.createElement('div');
                        card.className = 'msg-card';
                        card.onclick = () => focusOnBot(m.agent_id);
                        const partnerTag = m.partner ? ` → ${{m.partner}}` : '';
                        card.innerHTML = `
                            <div class="msg-meta">
                                <span class="msg-sender">${{m.sender}}${{partnerTag}}</span>
                                <span>${{m.job}} · ${{m.time_str}}</span>
                            </div>
                            <div class="msg-text">"${{m.text}}"</div>
                        `;
                        feedEl.prepend(card);
                        while (feedEl.children.length > 35) {{
                            feedEl.removeChild(feedEl.lastChild);
                        }}
                    }}
                }});
            }}

            function focusOnBot(agentId) {{
                const h = humans[agentId];
                if (!h) return;
                selectedAgentId = agentId;
                Object.values(humans).forEach(item => item.selRing.visible = false);
                h.selRing.visible = true;
                controls.target.set(h.root.position.x, 1.5, h.root.position.z);
                document.getElementById('inspect-card').style.display = 'block';
                refreshInspectCard(h.data);
            }}

            // --- 6. WEBSOCKET STREAM ---
            let ws = null;
            function connectWS() {{
                ws = new WebSocket("ws://127.0.0.1:{ws_port}/ws");
                ws.onmessage = (event) => {{
                    const payload = JSON.parse(event.data);
                    STATE = payload;
                    updateModeVisuals(payload.mode);
                    syncMessageSidebar(payload.messages);

                    payload.agents.forEach(a => {{
                        const h = humans[a.id];
                        if (h) {{
                            h.targetX = a.x;
                            h.targetZ = a.z;
                            h.targetH = a.h;
                            h.speed = a.spd;
                            h.data = a;
                        }}
                    }});
                    if (selectedAgentId !== null && humans[selectedAgentId]) {{
                        refreshInspectCard(humans[selectedAgentId].data);
                    }}
                }};
                ws.onclose = () => setTimeout(connectWS, 1500);
            }}
            connectWS();

            function setMode(modeName) {{
                if (ws && ws.readyState === WebSocket.OPEN) {{
                    ws.send(JSON.stringify({{ type: "MODE", value: modeName }}));
                }} else {{
                    fetch("http://127.0.0.1:{ws_port}/mode/" + modeName, {{ method: "POST" }});
                }}
                updateModeVisuals(modeName);
            }}

            function updateModeVisuals(mode) {{
                ['NEUTRAL', 'HAPPY', 'CHAOS'].forEach(m => {{
                    const btn = document.getElementById('btn-' + m);
                    if (btn) btn.classList.toggle('active', m === mode);
                }});
                if (mode === 'HAPPY') {{
                    scene.background.setHex(0x161616);
                    scene.fog.color.setHex(0x161616);
                    hemiLight.intensity = 0.92;
                }} else if (mode === 'CHAOS') {{
                    scene.background.setHex(0x050505);
                    scene.fog.color.setHex(0x050505);
                    hemiLight.intensity = 0.35;
                }} else {{
                    scene.background.setHex(0x0c0c0c);
                    scene.fog.color.setHex(0x0c0c0c);
                    hemiLight.intensity = 0.65;
                }}
            }}

            // --- 7. CLICK HUMAN IN 3D WORLD TO INSPECT ---
            const raycaster = new THREE.Raycaster();
            const mouse = new THREE.Vector2();

            window.addEventListener('pointerdown', (e) => {{
                if (
                    e.target.closest('#top-bar') ||
                    e.target.closest('#right-sidebar') ||
                    e.target.closest('#inspect-card')
                ) return;

                mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
                mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;
                raycaster.setFromCamera(mouse, camera);
                const hits = raycaster.intersectObjects(pickableTorsoMeshes);
                if (hits.length > 0) {{
                    focusOnBot(hits[0].object.userData.agentId);
                }} else {{
                    selectedAgentId = null;
                    Object.values(humans).forEach(h => h.selRing.visible = false);
                    document.getElementById('inspect-card').style.display = 'none';
                }}
            }});

            function refreshInspectCard(a) {{
                document.getElementById('card-name').innerText = a.name;
                document.getElementById('card-job').innerText = a.job;
                document.getElementById('card-act').innerText = a.act;
                document.getElementById('card-mood').innerText = Math.round(a.mood * 100) + '%';
                document.getElementById('card-stress').innerText = Math.round(a.stress * 100) + '%';
                document.getElementById('card-skep').innerText = Math.round(a.skep * 100) + '%';
            }}

            // --- 8. 60 FPS RENDER LOOP SCALED BY TIME PERCEPTION ---
            let walkClock = 0;
            const projVec = new THREE.Vector3();

            function animate() {{
                requestAnimationFrame(animate);
                walkClock += 0.14 * timeScale;
                const lerpRate = Math.min(0.65, 0.20 * timeScale);

                if (STATE.mode === 'CHAOS') {{
                    streetBulbs.forEach((b, idx) => {{
                        b.visible = Math.sin(walkClock * 3.0 + idx) > -0.3;
                    }});
                }} else {{
                    streetBulbs.forEach(b => b.visible = true);
                }}

                Object.values(humans).forEach(h => {{
                    h.root.position.x += (h.targetX - h.root.position.x) * lerpRate;
                    h.root.position.z += (h.targetZ - h.root.position.z) * lerpRate;

                    let diff = h.targetH - h.root.rotation.y;
                    while (diff < -Math.PI) diff += Math.PI * 2;
                    while (diff > Math.PI) diff -= Math.PI * 2;
                    h.root.rotation.y += diff * lerpRate;

                    if (h.speed > 0.02) {{
                        const swing = Math.sin(walkClock * (h.speed * 3.2) + h.phase) * 0.65;
                        h.leftLegPivot.rotation.x = swing;
                        h.rightLegPivot.rotation.x = -swing;
                        h.leftArmPivot.rotation.x = -swing * 0.8;
                        h.rightArmPivot.rotation.x = swing * 0.8;
                    }} else {{
                        const talkGesture = h.data.msg ? Math.sin(walkClock * 0.8 + h.phase) * 0.18 : 0;
                        h.leftLegPivot.rotation.x *= 0.8;
                        h.rightLegPivot.rotation.x *= 0.8;
                        h.leftArmPivot.rotation.x = talkGesture;
                        h.rightArmPivot.rotation.x = -talkGesture;
                    }}

                    if (h.data.msg && h.data.msg.length > 0) {{
                        projVec.set(h.root.position.x, 2.85, h.root.position.z);
                        projVec.project(camera);
                        if (projVec.z < 1.0) {{
                            const sx = (projVec.x * 0.5 + 0.5) * window.innerWidth;
                            const sy = (-(projVec.y * 0.5) + 0.5) * window.innerHeight;
                            h.bubble.style.left = sx + 'px';
                            h.bubble.style.top = sy + 'px';
                            h.bubble.innerText = h.data.msg;
                            h.bubble.style.display = 'block';
                        }} else {{
                            h.bubble.style.display = 'none';
                        }}
                    }} else {{
                        h.bubble.style.display = 'none';
                    }}
                }});

                controls.update();
                renderer.render(scene, camera);
            }}
            animate();

            window.addEventListener('resize', () => {{
                camera.aspect = window.innerWidth / window.innerHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(window.innerWidth, window.innerHeight);
            }});
        </script>
    </body>
    </html>
    """


def render_dashboard() -> None:
    load_css()
    backend_server.ensure_background_server(port=8765)
    time.sleep(0.15)

    map_data = backend_server.brain.town.get_static_map_data()
    init_state = backend_server.brain.get_state_payload()

    components.html(
        build_fullscreen_3d_town(map_data, init_state, ws_port=8765),
        height=880,
        scrolling=False,
    )


if __name__ == "__main__":
    st.set_page_config(page_title="THE MATRIX // 3D Town", layout="wide")
    render_dashboard()