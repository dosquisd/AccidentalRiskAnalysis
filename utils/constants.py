from pathlib import Path

ROOT = Path(__file__).parents[1]
RAW_DATA_DIR = ROOT / "data" / "raw"
PROCESSED_DATA_DIR = ROOT / "data" / "processed"

DAY_OF_WEEK_MAP = {
    1: "Lunes",
    2: "Martes",
    3: "Miercoles",
    4: "Jueves",
    5: "Viernes",
    6: "Sábado",
    7: "Domingo",
}

FIGURES_DIR = ROOT / "figures"
