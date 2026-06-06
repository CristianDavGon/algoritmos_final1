from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import numpy as np

from tests.models import PartitionResult

_CACHE_FILE = Path(__file__).parent / "data" / "pyphi_cache.json"
_ESTRATEGIA_PYPHI = "Pyphi"


class PyPhiCache:
    """Persistent JSON cache for PyPhi PartitionResult objects.

    Reads the cache file once at startup. New entries are kept in memory and
    flushed explicitly with save(), avoiding a full JSON rewrite per test case.

    Args:
        cache_path: Path to the JSON file. Defaults to tests/data/pyphi_cache.json.
    """

    def __init__(self, cache_path: Path = _CACHE_FILE) -> None:
        self._path = cache_path
        self._store: dict[str, dict] = self._load()
        self._dirty = False

    def _make_key(
        self,
        n_nodes: int,
        tpm_page: str,
        estado_inicial: str,
        alcance_bin: str,
        mecanismo_bin: str,
    ) -> str:
        return f"{n_nodes}|{tpm_page}|{estado_inicial}|{alcance_bin}|{mecanismo_bin}"

    def _load(self) -> dict[str, dict]:
        if self._path.exists():
            with self._path.open(encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding="utf-8") as f:
            json.dump(self._store, f, ensure_ascii=False, indent=2)
        self._dirty = False

    def save(self) -> None:
        """Persist pending cache entries to disk."""
        if self._dirty:
            self._save()

    def get(
        self,
        n_nodes: int,
        tpm_page: str,
        estado_inicial: str,
        alcance_bin: str,
        mecanismo_bin: str,
    ) -> Optional[PartitionResult]:
        """Return cached PyPhi result or None if not present."""
        key = self._make_key(n_nodes, tpm_page, estado_inicial, alcance_bin, mecanismo_bin)
        entry = self._store.get(key)
        if entry is None:
            return None
        return PartitionResult(
            estrategia=_ESTRATEGIA_PYPHI,
            perdida=entry["perdida"],
            particion=entry["particion"],
            dist_subsistema=np.array(entry["dist_subsistema"], dtype=np.float32),
            dist_particion=np.array(entry["dist_particion"], dtype=np.float32),
            tiempo=entry["tiempo"],
        )

    def put(
        self,
        n_nodes: int,
        tpm_page: str,
        estado_inicial: str,
        alcance_bin: str,
        mecanismo_bin: str,
        result: PartitionResult,
    ) -> None:
        """Store a PyPhi result in memory until save() is called."""
        key = self._make_key(n_nodes, tpm_page, estado_inicial, alcance_bin, mecanismo_bin)
        self._store[key] = {
            "perdida": float(result.perdida),
            "particion": result.particion,
            "dist_subsistema": [float(x) for x in result.dist_subsistema.tolist()],
            "dist_particion": [float(x) for x in result.dist_particion.tolist()],
            "tiempo": float(result.tiempo),
        }
        self._dirty = True

    def __len__(self) -> int:
        return len(self._store)
