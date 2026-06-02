"""
Genera archivos CSV de TPM binaria para N=20 y N=25 nodos.
Misma lógica que Manager.generar_red(): semilla=73, randint(2), fmt='%d'.
"""
import shutil
import sys
import time
from pathlib import Path

import numpy as np

SEED = 73
QNODES_SAMPLES = Path("code/QNodes/src/.samples")
GEOMIP_SAMPLES = Path("code/GeoMIP/data/samples")
CHUNK = 1 << 18  # 262 144 filas por chunk


def generate(n: int) -> None:
    num_states = 1 << n
    filename = f"N{n}A.csv"
    primary = QNODES_SAMPLES / filename

    print(f"\n=== N{n}A.csv ({num_states} filas × {n} cols) ===")
    QNODES_SAMPLES.mkdir(parents=True, exist_ok=True)

    np.random.seed(SEED)
    t0 = time.time()

    with open(primary, "w", newline="") as fh:
        remaining = num_states
        written = 0
        while remaining > 0:
            chunk = min(CHUNK, remaining)
            data = np.random.randint(2, size=(chunk, n), dtype=np.int8)
            np.savetxt(fh, data, delimiter=",", fmt="%d")
            written += chunk
            remaining -= chunk
            pct = 100 * written / num_states
            elapsed = time.time() - t0
            print(f"  {written:>12,} / {num_states:,}  ({pct:5.1f}%)  {elapsed:.1f}s", end="\r")

    size_mb = primary.stat().st_size / (1024 ** 2)
    print(f"\n  QNodes: {primary}  [{size_mb:.1f} MB en {time.time()-t0:.1f}s]")

    # Copiar a GeoMIP
    GEOMIP_SAMPLES.mkdir(parents=True, exist_ok=True)
    dest = GEOMIP_SAMPLES / filename
    shutil.copy2(primary, dest)
    print(f"  GeoMIP: {dest}  [copiado]")


if __name__ == "__main__":
    ns = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else [20, 25]
    for n in ns:
        generate(n)
    print("\nListo.")
