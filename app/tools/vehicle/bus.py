from dataclasses import dataclass, field
from time import time
from typing import Any, Protocol
from uuid import uuid4


@dataclass(frozen=True)
class VehicleCommandResult:
    command_id: str
    command: str
    payload: dict[str, Any]
    status: str = "ok"
    created_at: float = field(default_factory=time)

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "command_id": self.command_id,
            "command": self.command,
            **self.payload,
        }


class VehicleCommandBus(Protocol):
    async def send(self, command: str, payload: dict[str, Any]) -> VehicleCommandResult:
        ...


class MemoryVehicleCommandBus:
    def __init__(self):
        self.commands: list[VehicleCommandResult] = []

    async def send(self, command: str, payload: dict[str, Any]) -> VehicleCommandResult:
        result = VehicleCommandResult(
            command_id=str(uuid4()),
            command=command,
            payload=dict(payload),
        )
        self.commands.append(result)
        return result
