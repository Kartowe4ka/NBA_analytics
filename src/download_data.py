
from pathlib import Path
from urllib.request import Request, urlopen

import pandas as pd


# Корневая папка проекта
BASE_DIR = Path(__file__).resolve().parent.parent

# Папка для исходных данных
RAW_DATA_DIR = BASE_DIR / "data" / "raw"

# Публичный источник статистики
DATA_URL = (
    "https://raw.githubusercontent.com/"
    "ismayc/nba-season-data/main/"
    "data/2025-26/box_scores.csv"
)

OUTPUT_FILE = RAW_DATA_DIR / "nba_box_scores_2025_26.csv"


def download_data():
    """Скачивает исходную статистику NBA в CSV."""

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("Загружаем статистику NBA 2025/26...")

    request = Request(
        DATA_URL,
        headers={"User-Agent": "NBA-Analytics-Student-Project/1.0"},
    )

    try:
        with urlopen(request, timeout=60) as response:
            content = response.read()

        if not content:
            raise ValueError("Получен пустой файл.")

        # Сначала проверяем CSV, только затем сохраняем
        from io import BytesIO

        df = pd.read_csv(BytesIO(content))

        required_columns = {
            "game_id",
            "game_date",
            "season_type",
            "player_id",
            "player",
            "team",
            "pts",
            "ast",
        }

        missing_columns = required_columns - set(df.columns)

        if missing_columns:
            raise ValueError(
                f"В источнике отсутствуют столбцы: "
                f"{sorted(missing_columns)}"
            )

        if df.empty:
            raise ValueError("Таблица не содержит строк.")

        OUTPUT_FILE.write_bytes(content)

        print("\nДанные успешно загружены!")
        print(f"Файл: {OUTPUT_FILE}")
        print(f"Количество строк: {len(df)}")
        print(f"Количество столбцов: {len(df.columns)}")
        print(f"Уникальных матчей: {df['game_id'].nunique()}")
        print(f"Уникальных игроков: {df['player_id'].nunique()}")

        print("\nТипы матчей:")
        print(df["season_type"].value_counts(dropna=False))

        print("\nПервые 5 строк:")
        print(
            df[
                ["game_date", "player", "team", "pts", "ast"]
            ].head().to_string(index=False)
        )

    except Exception as error:
        print(f"\nОшибка загрузки: {error}")
        raise


if __name__ == "__main__":
    download_data()
