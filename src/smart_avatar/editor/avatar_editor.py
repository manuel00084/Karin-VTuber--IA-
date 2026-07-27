"""Avatar Editor --- configuration interface (not a visual editor).

Operates on ``format.kar_format.AvatarData`` (serialization layer).
Do NOT pass ``core.types.AvatarData`` (runtime layer) to this editor.
"""
import json

from src.smart_avatar.format.kar_format import AvatarData, AvatarJSONEncoder


class AvatarEditor:
    """Stores and applies editable avatar parameters as a simple dict."""

    def __init__(self):
        self.params = {
            "hair_physics": True,
            "hair_stiffness": 0.5,
            "hair_damping": 0.5,
            "clothes_physics": True,
            "clothes_stiffness": 0.5,
            "breathing": True,
            "breathing_intensity": 0.5,
            "blink": True,
            "lip_sync": True,
            "eye_tracking": True,
            "body_movement": True,
            "physics_level": "normal",
            "accessory_physics": True,
            "head_tilt": True,
        }

    def get_param(self, name):
        """Get a single parameter value by name."""
        return self.params.get(name)

    def set_param(self, name, value):
        """Set a single parameter value by name."""
        if name in self.params:
            self.params[name] = value

    def get_all_params(self) -> dict:
        """Return a copy of all parameters."""
        return dict(self.params)

    def apply_to_physics(self, physics):
        """Apply editor parameters to a PhysicsData object."""
        physics.breathing["enabled"] = self.params["breathing"]
        physics.breathing["intensity"] = self.params["breathing_intensity"]

        levels = {"low": 0.3, "normal": 0.5, "high": 0.8}
        factor = levels.get(self.params["physics_level"], 0.5)

        for spring in physics.springs:
            if spring.get("type") == "hair":
                spring["enabled"] = self.params["hair_physics"]
                spring["stiffness"] = self.params["hair_stiffness"] * factor
                spring["damping"] = self.params["hair_damping"] * factor
            elif spring.get("type") == "clothes":
                spring["enabled"] = self.params["clothes_physics"]
                spring["stiffness"] = self.params["clothes_stiffness"] * factor
                spring["damping"] = self.params.get("clothes_damping", factor * 0.5)
            elif spring.get("type") == "accessory":
                spring["enabled"] = self.params["accessory_physics"]

    def apply_to_avatar(self, avatar_data: AvatarData):
        """Apply all editor parameters to an AvatarData object."""
        self.apply_to_physics(avatar_data.physics)

        if hasattr(avatar_data, "extra_params"):
            avatar_data.extra_params.update(self.params)
        else:
            avatar_data.extra_params = dict(self.params)

    def to_json(self) -> str:
        """Serialize editor params to JSON string."""
        return json.dumps(self.params, cls=AvatarJSONEncoder, indent=2)

    def from_json(self, data: str):
        """Load editor params from a JSON string."""
        loaded = json.loads(data)
        for key, value in loaded.items():
            if key in self.params:
                self.params[key] = value
