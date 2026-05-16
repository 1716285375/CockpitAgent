import asyncio

from app.tools.vehicle.ac_control import ACControlTool
from app.tools.vehicle.bus import MemoryVehicleCommandBus
from app.tools.vehicle.seat_control import SeatControlTool
from app.tools.vehicle.window_control import WindowControlTool


def test_vehicle_tools_send_commands_through_bus():
    bus = MemoryVehicleCommandBus()

    async def run():
        ac = await ACControlTool(bus).execute(temperature=22, mode="auto", fan_level=2)
        seat = await SeatControlTool(bus).execute(position="driver", action="heat_on", level=2)
        window = await WindowControlTool(bus).execute(window="all", action="close")
        return ac, seat, window

    ac, seat, window = asyncio.run(run())

    assert ac["command"] == "AC_SET"
    assert seat["command"] == "SEAT_SET"
    assert window["command"] == "WINDOW_SET"
    assert len(bus.commands) == 3
    assert bus.commands[0].payload["current_temp"] == 22
