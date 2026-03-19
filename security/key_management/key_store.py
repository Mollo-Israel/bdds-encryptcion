from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class BankKeyRecord:
    bank_id: int
    algorithm: str
    key_material: dict[str, Any] = field(default_factory=dict)