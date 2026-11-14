from pathlib import Path

import pandas as pd


# Пути к файлам
BASE_DIR = Path(__file__).resolve().parent.parent

RAW_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "nba_box_scores_2025_26.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "player_game_stats_2025_26.csv"
)

# Статистические показатели игроков
STAT_COLUMNS = [
    "pts", "ast", "trb", "drb", "orb",
    "stl", "blk", "tov", "pf",
    "fgm", "fga", "fg3m", "fg3a",
    "ftm", "fta", "plus_minus",
]

REQUIRED_COLUMNS = [
    "game_id", "game_date", "season_type",
    "player_id", "player", "team",
    "minutes", "did_not_play",
] + STAT_COLUMNS


def clean_data():
    print("=== NBA Data Cleaning ===")

    # 1. Загрузка оригинальных данных
    df = pd.read_csv(
        RAW_FILE,
        dtype={
            "game_id": "string",
            "player_id": "string",
        },
    )

    initial_rows = len(df)
    print(f"\nИсходных строк: {initial_rows}")

    # 2. Проверка структуры
    missing_columns = set(REQUIRED_COLUMNS) - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Отсутствуют столбцы: {sorted(missing_columns)}"
        )

    # 3. Проверка формата времени
    original_minutes = df["minutes"].copy()

    df["minutes"] = pd.to_numeric(
        df["minutes"],
        errors="coerce",
    )

    invalid_minutes = (
        original_minutes.notna()
        & df["minutes"].isna()
    )

    if invalid_minutes.any():
        raise ValueError(
            "Обнаружены некорректные значения minutes: "
            f"{invalid_minutes.sum()}"
        )

    # 4. Проверка числовых показателей
    for column in STAT_COLUMNS:
        original = df[column].copy()

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

        invalid = original.notna() & df[column].isna()

        if invalid.any():
            raise ValueError(
                f"Некорректные значения {column}: "
                f"{invalid.sum()}"
            )

    # 5. Проверяем строки без времени,
    # но с ненулевой статистикой
    missing_minutes = df["minutes"].isna()

    has_nonzero_stats = (
        df[STAT_COLUMNS]
        .fillna(0)
        .ne(0)
        .any(axis=1)
    )

    suspicious = df[
        missing_minutes & has_nonzero_stats
    ]

    print(
        "Строк без минут, но с ненулевой статистикой:",
        len(suspicious),
    )

    if not suspicious.empty:
        raise ValueError(
            "Есть игроки с ненулевой статистикой, "
            "но отсутствующим временем. "
            "Требуется ручная проверка."
        )

    # 6. Выделяем регулярный сезон
    regular = df[
        df["season_type"] == "Regular Season"
    ].copy()

    print(f"Строк регулярного сезона: {len(regular)}")

    # 7. Отмечаем причины исключения
    missing_identity = (
        regular["player_id"].isna()
        | regular["player"].isna()
    )

    invalid_playtime = (
        regular["minutes"].isna()
        | (regular["minutes"] <= 0)
    )

    print(
        "Без имени или ID:",
        missing_identity.sum(),
    )

    print(
        "Без положительного игрового времени:",
        invalid_playtime.sum(),
    )

    # 8. Формируем таблицу сыгранных матчей
    played = regular[
        ~missing_identity & ~invalid_playtime
    ].copy()

    # 9. Проверяем полноту основных показателей
    missing_stats = played[STAT_COLUMNS].isna().sum()

    if missing_stats.any():
        raise ValueError(
            "В сыгранных матчах обнаружены пропуски:\n"
            + missing_stats[missing_stats > 0].to_string()
        )

    # 10. Проверяем ключ игрок + матч
    duplicates = played.duplicated(
        subset=["game_id", "player_id"]
    )

    if duplicates.any():
        raise ValueError(
            "Обнаружены повторяющиеся записи игрока "
            "в одном матче."
        )

    # 11. Преобразуем дату
    played["game_date"] = pd.to_datetime(
        played["game_date"],
        errors="raise",
    )

    # 12. Сортируем данные
    played = played.sort_values(
        ["game_date", "game_id", "team", "player_id"]
    ).reset_index(drop=True)

    # 13. Сохраняем результат
    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    played.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8",
    )

    print("\n=== Результат ===")
    print(f"Строк после очистки: {len(played)}")
    print(f"Исключено из регулярного сезона: {len(regular) - len(played)}")
    print(f"Уникальных игроков: {played['player_id'].nunique()}")
    print(f"Уникальных команд: {played['team'].nunique()}")
    print(f"Уникальных матчей: {played['game_id'].nunique()}")
    print(f"\nФайл сохранён: {OUTPUT_FILE}")


if __name__ == "__main__":
    clean_data()
