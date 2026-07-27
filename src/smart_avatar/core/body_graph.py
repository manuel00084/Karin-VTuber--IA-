"""Grafo de relaciones corporales para transmisión de movimiento.

Propaga rotaciones y traslaciones a través de la cadena de huesos del avatar.
Por ejemplo: rotación de cabeza → cuello → hombros → cabello → accesorios.
"""

from __future__ import annotations

from src.smart_avatar.core.types import BodyPartNode, Vec3


class BodyRelationshipGraph:
    """Grafo acíclico dirigido (DAG) de partes del cuerpo.

    Cada nodo tiene dependencias que indican qué partes lo afectan.
    Cuando una parte se mueve, el movimiento se propaga en cascada
    a todas las partes que dependen de ella.
    """

    def __init__(self) -> None:
        self._nodes: dict[str, BodyPartNode] = {}
        self._dependents: dict[str, list[str]] = {}

    # ------------------------------------------------------------------
    # Construcción del grafo
    # ------------------------------------------------------------------

    def add_part(self, name: str, dependencies: list[str] | None = None) -> None:
        """Registra una parte del cuerpo con sus dependencias."""
        deps = dependencies or []
        self._nodes[name] = BodyPartNode(name=name, dependencies=deps)

        for dep in deps:
            self._dependents.setdefault(dep, [])
            if name not in self._dependents[dep]:
                self._dependents[dep].append(name)

    def get_dependents(self, name: str) -> list[str]:
        """Partes que dependen directamente de *name*."""
        return list(self._dependents.get(name, []))

    def get_all_dependents(self, name: str) -> list[str]:
        """Todas las partes afectadas en cascada (BFS)."""
        visited: set[str] = {name}
        queue = list(self._dependents.get(name, []))
        result: list[str] = []

        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            result.append(current)
            queue.extend(self._dependents.get(current, []))

        return result

    # ------------------------------------------------------------------
    # Transmisión de movimiento
    # ------------------------------------------------------------------

    def transmit_motion(
        self,
        source: str,
        delta: Vec3,
        factors: dict[str, float] | None = None,
    ) -> dict[str, Vec3]:
        """Propaga un movimiento desde *source* a todas sus dependientes.

        Args:
            source: Nombre de la parte que inicia el movimiento.
            delta: Vector de movimiento (rotación en grados o traslación).
            factors: Factor de atenuación por parte. Si una parte no está
                     en el dict, se usa el factor heredado del padre.

        Returns:
            Dict mapeando nombre de parte → delta acumulado.
        """
        if source not in self._nodes:
            return {}

        factors = factors or {}
        result: dict[str, Vec3] = {}

        # BFS para propagar con factores de amortiguación decrecientes
        queue: list[tuple[str, Vec3, float]] = []
        for dep in self._dependents.get(source, []):
            factor = factors.get(dep, 0.7)
            scaled = Vec3(
                x=delta.x * factor,
                y=delta.y * factor,
                z=delta.z * factor,
            )
            queue.append((dep, scaled, factor))

        visited: set[str] = {source}

        while queue:
            current, current_delta, parent_factor = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)

            result[current] = current_delta

            for dep in self._dependents.get(current, []):
                if dep in visited:
                    continue
                # Amortiguación compuesta: factor heredado × factor propio
                own = factors.get(dep, 0.7)
                combined = parent_factor * own
                scaled = Vec3(
                    x=current_delta.x * combined / parent_factor if parent_factor else 0.0,
                    y=current_delta.y * combined / parent_factor if parent_factor else 0.0,
                    z=current_delta.z * combined / parent_factor if parent_factor else 0.0,
                )
                queue.append((dep, scaled, combined))

        return result


# ---------------------------------------------------------------------------
# Configuración por defecto del cuerpo humano
# ---------------------------------------------------------------------------

_DEFAULT_GRAPH: dict[str, list[str] | None] = {
    "torso": [],
    "chest": ["torso"],
    "neck": ["chest"],
    "head": ["neck"],
    "left_shoulder": ["chest"],
    "right_shoulder": ["chest"],
    "left_arm": ["left_shoulder"],
    "right_arm": ["right_shoulder"],
    "left_hand": ["left_arm"],
    "right_hand": ["right_arm"],
    "hips": ["torso"],
    "left_leg": ["hips"],
    "right_leg": ["hips"],
    "left_foot": ["left_leg"],
    "right_foot": ["right_leg"],
    # Cara y accesorios — dependen de head
    "left_eye": ["head"],
    "right_eye": ["head"],
    "left_eyebrow": ["head"],
    "right_eyebrow": ["head"],
    "nose": ["head"],
    "mouth": ["head"],
    "hair": ["head"],
    "accessory": ["head"],
}


def create_default_graph() -> BodyRelationshipGraph:
    """Crea un grafo con la estructura anatómica humana por defecto."""
    graph = BodyRelationshipGraph()
    for name, deps in _DEFAULT_GRAPH.items():
        graph.add_part(name, deps or [])
    return graph
