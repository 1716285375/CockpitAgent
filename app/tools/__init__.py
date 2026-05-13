from app.tools.registry import ToolRegistry
from app.tools.vehicle.ac_control import ACControlTool
from app.tools.vehicle.seat_control import SeatControlTool
from app.tools.vehicle.window_control import WindowControlTool
from app.tools.info.navigation import NavigationTool
from app.tools.info.vehicle_status import VehicleStatusTool
from app.tools.info.weather import WeatherTool
from app.tools.media import PlayMusicTool
from app.tools.preference.user_preference import GetUserPreferenceTool, PreferenceStore, SetUserPreferenceTool
from app.tools.qa import VehicleQATool


def build_default_registry(timeout_seconds: float = 5.0, cache_ttl_seconds: float = 10.0) -> ToolRegistry:
    registry = ToolRegistry(timeout_seconds=timeout_seconds, cache_ttl_seconds=cache_ttl_seconds)
    preference_store = PreferenceStore()
    registry.register_many(
        [
            ACControlTool(),
            SeatControlTool(),
            WindowControlTool(),
            VehicleStatusTool(),
            WeatherTool(),
            NavigationTool(),
            SetUserPreferenceTool(preference_store),
            GetUserPreferenceTool(preference_store),
            VehicleQATool(),
            PlayMusicTool(),
        ]
    )
    return registry


__all__ = ["ToolRegistry", "build_default_registry"]
