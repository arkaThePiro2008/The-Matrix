import networkx as nx
import numpy as np
from typing import List, Dict, Tuple, Any


class TownGrid:
    """
    Constructs a structured 3D town with paved avenues, sidewalks, crosswalks,
    distinct architectural buildings (offices, houses, cafes), trees, and streetlights.
    """

    def __init__(self):
        # Road centerlines at -60, -20, 20, 60 (4x4 street grid, 3x3 city blocks)
        self.road_coords = [-60, -20, 20, 60]
        self.road_width = 8.0
        self.sidewalk_offset = 5.2  # Distance from road center to sidewalk path

        self.graph = nx.Graph()
        self.buildings: List[Dict[str, Any]] = []
        self.trees: List[Dict[str, float]] = []
        self.streetlights: List[Dict[str, float]] = []
        self.benches: List[Dict[str, float]] = []

        self.homes: List[Tuple[float, float]] = []
        self.workplaces: List[Tuple[float, float]] = []
        self.social_spots: List[Tuple[float, float]] = []

        self._build_sidewalk_network()
        self._build_city_blocks()

    def _build_sidewalk_network(self) -> None:
        """Creates a realistic pedestrian sidewalk and crosswalk graph."""
        offsets = [-self.sidewalk_offset, self.sidewalk_offset]
        # Create 4 sidewalk corner nodes around every intersection
        for rx in self.road_coords:
            for rz in self.road_coords:
                corners = [(round(rx + dx, 1), round(rz + dz, 1)) for dx in offsets for dz in offsets]
                for c in corners:
                    self.graph.add_node(c)
                # Crosswalks connecting corners across the street
                for i in range(len(corners)):
                    for j in range(i + 1, len(corners)):
                        c1, c2 = corners[i], corners[j]
                        if c1[0] == c2[0] or c1[1] == c2[1]:
                            dist = abs(c1[0] - c2[0]) + abs(c1[1] - c2[1])
                            self.graph.add_edge(c1, c2, weight=dist)

        # Connect sidewalks along city blocks and add mid-block building entrances
        all_nodes = list(self.graph.nodes)
        for n1 in all_nodes:
            for n2 in all_nodes:
                if n1 >= n2:
                    continue
                # Same X sidewalk line, adjacent intersections
                if n1[0] == n2[0] and abs(abs(n1[1] - n2[1]) - (40.0 - 2 * self.sidewalk_offset)) < 1.0:
                    mid_z = round((n1[1] + n2[1]) / 2.0, 1)
                    mid_node = (n1[0], mid_z)
                    self.graph.add_node(mid_node)
                    self.graph.add_edge(n1, mid_node, weight=abs(n1[1] - mid_z))
                    self.graph.add_edge(mid_node, n2, weight=abs(n2[1] - mid_z))
                # Same Z sidewalk line, adjacent intersections
                if n1[1] == n2[1] and abs(abs(n1[0] - n2[0]) - (40.0 - 2 * self.sidewalk_offset)) < 1.0:
                    mid_x = round((n1[0] + n2[0]) / 2.0, 1)
                    mid_node = (mid_x, n1[1])
                    self.graph.add_node(mid_node)
                    self.graph.add_edge(n1, mid_node, weight=abs(n1[0] - mid_x))
                    self.graph.add_edge(mid_node, n2, weight=abs(n2[0] - mid_x))

        # Place streetlights at intersections
        for rx in self.road_coords:
            for rz in self.road_coords:
                self.streetlights.append({"x": rx - 5.5, "z": rz - 5.5})
                self.streetlights.append({"x": rx + 5.5, "z": rz + 5.5})

    def _build_city_blocks(self) -> None:
        """Populates the 9 city blocks with offices, cafes, a central park, and houses."""
        block_centers = [-40, 0, 40]
        b_id = 0

        for bx in block_centers:
            for bz in block_centers:
                # Center Block (0, 0) is the Central Town Park & Plaza
                if bx == 0 and bz == 0:
                    # Connect plaza pathways into the sidewalk graph
                    center_node = (0.0, 0.0)
                    self.graph.add_node(center_node)
                    for gate in [(0.0, -14.8), (0.0, 14.8), (-14.8, 0.0), (14.8, 0.0)]:
                        self.graph.add_node(gate)
                        self.graph.add_edge(center_node, gate, weight=14.8)
                        self.social_spots.append(gate)
                    self.social_spots.append(center_node)

                    # Park Benches & Trees around Central Plaza
                    for angle in np.linspace(0, 2 * np.pi, 8, endpoint=False):
                        tx, tz = float(np.cos(angle) * 10.5), float(np.sin(angle) * 10.5)
                        self.trees.append({"x": round(tx, 2), "z": round(tz, 2), "scale": 1.15})
                    for bx_off, bz_off in [(-5, -5), (5, -5), (-5, 5), (5, 5)]:
                        self.benches.append({"x": float(bx_off), "z": float(bz_off)})
                        self.social_spots.append((float(bx_off), float(bz_off)))
                    continue

                # Determine district type by block location
                if bx == -40:
                    # West blocks: Downtown Office & Civic Towers
                    sub_offsets = [(-7.5, -7.5), (7.5, -7.5), (-7.5, 7.5), (7.5, 7.5)]
                    heights = [26.0, 19.0, 22.0, 30.0]
                    for (ox, oz), h in zip(sub_offsets, heights):
                        cx, cz = bx + ox, bz + oz
                        self.buildings.append({
                            "id": b_id,
                            "type": "OFFICE",
                            "x": cx,
                            "z": cz,
                            "w": 9.5,
                            "d": 9.5,
                            "h": h,
                        })
                        b_id += 1
                        door = self.nearest_node(cx, cz)
                        self.workplaces.append(door)
                elif bx == 40:
                    # East blocks: Residential Neighborhood (Houses with pitched roofs & trees)
                    sub_offsets = [(-8.0, -8.0), (8.0, -8.0), (-8.0, 8.0), (8.0, 8.0)]
                    for ox, oz in sub_offsets:
                        cx, cz = bx + ox, bz + oz
                        self.buildings.append({
                            "id": b_id,
                            "type": "HOUSE",
                            "x": cx,
                            "z": cz,
                            "w": 7.5,
                            "d": 7.5,
                            "h": 6.5,
                        })
                        b_id += 1
                        door = self.nearest_node(cx, cz)
                        self.homes.append(door)
                    self.trees.append({"x": float(bx), "z": float(bz), "scale": 0.95})
                else:
                    # North/South Center blocks: Mixed Cafes, Shops & Apartments
                    sub_offsets = [(-7.5, -7.5), (7.5, -7.5), (-7.5, 7.5), (7.5, 7.5)]
                    types = ["CAFE", "APARTMENT", "SHOP", "APARTMENT"]
                    heights = [8.0, 15.0, 9.0, 14.0]
                    for (ox, oz), btype, h in zip(sub_offsets, types, heights):
                        cx, cz = bx + ox, bz + oz
                        self.buildings.append({
                            "id": b_id,
                            "type": btype,
                            "x": cx,
                            "z": cz,
                            "w": 8.5,
                            "d": 8.5,
                            "h": h,
                        })
                        b_id += 1
                        door = self.nearest_node(cx, cz)
                        if btype in ("CAFE", "SHOP"):
                            self.social_spots.append(door)
                            self.workplaces.append(door)
                        else:
                            self.homes.append(door)

    def nearest_node(self, x: float, z: float) -> Tuple[float, float]:
        best_node = (0.0, 0.0)
        best_dist = 1e9
        for n in self.graph.nodes:
            d = (n[0] - x) ** 2 + (n[1] - z) ** 2
            if d < best_dist:
                best_dist = d
                best_node = n
        return best_node

    def find_path(self, start: Tuple[float, float], goal: Tuple[float, float]) -> List[Tuple[float, float]]:
        s_node = self.nearest_node(start[0], start[1])
        g_node = self.nearest_node(goal[0], goal[1])
        if s_node == g_node:
            return [g_node]
        try:
            return nx.astar_path(
                self.graph,
                s_node,
                g_node,
                heuristic=lambda a, b: abs(a[0] - b[0]) + abs(a[1] - b[1]),
                weight="weight",
            )
        except nx.NetworkXNoPath:
            return [g_node]

    def get_static_map_data(self) -> Dict[str, Any]:
        return {
            "roads": self.road_coords,
            "road_width": self.road_width,
            "buildings": self.buildings,
            "trees": self.trees,
            "streetlights": self.streetlights,
            "benches": self.benches,
        }