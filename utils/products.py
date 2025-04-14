# utils/products.py

import pandas as pd
import os

PRODUCTS_PATH = "storage/products.csv"

def get_product_info(product_name: str) -> str:
    if not os.path.exists(PRODUCTS_PATH):
        return "⚠️ Таблиця товарів не знайдена."

    df = pd.read_csv(PRODUCTS_PATH)
    if "Название" not in df.columns:
        return "⚠️ У таблиці немає колонки 'Название'."

    match = df[df["Название"].str.lower() == product_name.lower()]
    if match.empty:
        return f"❌ Товар '{product_name}' не знайдено."

    row = match.iloc[0]
    return "\n".join([f"• {col}: {row[col]}" for col in df.columns])

def add_product(product_name: str, quantity: int, description: str, price: float) -> str:
    """
    Добавляет новый продукт в таблицу products.csv.

    :param product_name: Название продукта
    :param quantity: Количество
    :param description: Описание продукта
    :param price: Цена продукта
    :return: Сообщение об успешном добавлении или ошибке
    """
    if not os.path.exists(PRODUCTS_PATH):
        # Создаем файл, если он не существует
        df = pd.DataFrame(columns=["Название", "Количество", "Описание", "Цена"])
        df.to_csv(PRODUCTS_PATH, index=False)

    df = pd.read_csv(PRODUCTS_PATH)

    # Проверяем, существует ли продукт с таким же названием
    if not df.empty and product_name in df["Название"].values:
        # Обновляем существующий продукт
        idx = df[df["Название"] == product_name].index[0]
        df.at[idx, "Количество"] = quantity
        df.at[idx, "Описание"] = description
        df.at[idx, "Цена"] = price
        df.to_csv(PRODUCTS_PATH, index=False)
        return f"✅ Продукт '{product_name}' успешно обновлен."

    # Добавляем новый продукт
    new_product = {
        "Название": product_name,
        "Количество": quantity,
        "Описание": description,
        "Цена": price
    }
    df = pd.concat([df, pd.DataFrame([new_product])], ignore_index=True)
    df.to_csv(PRODUCTS_PATH, index=False)

    return f"✅ Продукт '{product_name}' успешно добавлен."

def list_all_products() -> str:
    if not os.path.exists(PRODUCTS_PATH):
        return "⚠️ Таблиця товарів не знайдена."

    df = pd.read_csv(PRODUCTS_PATH)
    if df.empty:
        return "📦 Таблиця товарів порожня."

    result = "🧾 Наявні товари:\n"
    for _, row in df.iterrows():
        result += f"- {row['Название']}: {row['Цена']} грн (в наявності: {row['Количество']})\n"
    return result.strip()
