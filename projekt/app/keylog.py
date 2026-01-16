from __future__ import annotations

import os
from datetime import datetime
from typing import Optional


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def log_keys(
    *,
    role: str,
    client_id: Optional[int],
    p: int,
    g: int,
    A: int,
    B: int,
    shared: int,
    enc_key: bytes,
    mac_key: bytes,
    out_dir: str = "keys",
) -> None:
    _ensure_dir(out_dir)
    stamp = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    suffix = f"_{client_id}" if client_id is not None else ""
    fname = os.path.join(out_dir, f"{role}{suffix}.log")

    with open(fname, "a", encoding="utf-8") as f:
        f.write(f"[{stamp}] p={p} g={g} A={A} B={B} shared={shared}\n")
        f.write(f"enc_key_hex={enc_key.hex()}\n")
        f.write(f"mac_key_hex={mac_key.hex()}\n")
        f.write("\n")
