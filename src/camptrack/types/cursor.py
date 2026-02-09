from __future__ import annotations
from typing import Any, Protocol, Optional, Tuple, List

class Cursor(Protocol):
    def execute(
        self,
        query: str,
        params: Optional[Tuple[Any, ...]] = None
    ) -> "Cursor":
        ...
    def executemany(
        self,
        query: str,
        seq_of_params: List[Tuple[Any, ...]]
    ) -> "Cursor":
        ...
    def fetchall(self) -> List[Tuple[Any, ...]]:
        ...
    def fetchone(self) -> Optional[Tuple[Any, ...]]:
        ...
    @property
    def lastrowid(self) -> int:
        ...
