from app.tools.registry import ToolRegistry
from app.infra.audit import AuditSink
from app.tools.vehicle.bus import MemoryVehicleCommandBus, VehicleCommandBus
from app.tools.vehicle.ac_control import ACControlTool
from app.tools.vehicle.seat_control import SeatControlTool
from app.tools.vehicle.window_control import WindowControlTool
from app.tools.info.navigation import NavigationTool
from app.tools.info.vehicle_status import VehicleStatusTool
from app.tools.info.weather import StaticWeatherProvider, WeatherProvider, WeatherTool
from app.tools.media import PlayMusicTool
from app.tools.preference.user_preference import GetUserPreferenceTool, MemoryPreferenceStore, PreferenceStore, SetUserPreferenceTool
from app.tools.qa import VehicleQATool


def build_default_registry(
    timeout_seconds: float = 5.0,
    cache_ttl_seconds: float = 10.0,
    preference_store: PreferenceStore | None = None,
    audit_sink: AuditSink | None = None,
    vehicle_bus: VehicleCommandBus | None = None,
    weather_provider: WeatherProvider | None = None,
) -> ToolRegistry:
    registry = ToolRegistry(
        timeout_seconds=timeout_seconds,
        cache_ttl_seconds=cache_ttl_seconds,
        audit_sink=audit_sink,
    )
    preference_store = preference_store or MemoryPreferenceStore()
    vehicle_bus = vehicle_bus or MemoryVehicleCommandBus()
    weather_provider = weather_provider or StaticWeatherProvider()
    registry.register_many(
        [
            ACControlTool(vehicle_bus),
            SeatControlTool(vehicle_bus),
            WindowControlTool(vehicle_bus),
            VehicleStatusTool(),
            WeatherTool(weather_provider),
            NavigationTool(),
            SetUserPreferenceTool(preference_store),
            GetUserPreferenceTool(preference_store),
            VehicleQATool(),
            PlayMusicTool(),
        ]
    )
    return registry


__all__ = ["ToolRegistry", "build_default_registry"]
