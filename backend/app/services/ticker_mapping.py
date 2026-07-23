import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OVERRIDE_PATH = REPO_ROOT / "backend" / "data" / "yahoo_ticker_overrides.json"


def load_ticker_overrides(path: Path | None = None) -> dict[str, str]:
    override_path = path or DEFAULT_OVERRIDE_PATH
    if not override_path.exists():
        return {}

    with override_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def map_symbol_to_yahoo_ticker(symbol: str, overrides: dict[str, str] | None = None) -> str:
    override_map = overrides or {}
    return override_map.get(symbol, f"{symbol}.NS")