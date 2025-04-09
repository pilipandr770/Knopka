# utils/products.py

import pandas as pd
import os

PRODUCTS_PATH = "storage/products.csv"

def get_product_info(product_name: str) -> str:
    if not os.path.exists(PRODUCTS_PATH):
        return "⚠️ Таблиця товарів не знайдена."

    df = pd.read_csv(PRODUCTS_PATH)
    if "назва" not in df.columns:
        return "⚠️ У таблиці немає колонки 'назва'."

    match = df[df["назва"].str.lower() == product_name.lower()]
    if match.empty:
        return f"❌ Товар '{product_name}' не знайдено."

    row = match.iloc[0]
    return "\n".join([f"• {col}: {row[col]}" for col in df.columns])

def add_product(назва: str, категорія: str = "", ціна: str = "", **kwargs) -> str:
    df = pd.read_csv(PRODUCTS_PATH) if os.path.exists(PRODUCTS_PATH) else pd.DataFrame(columns=["назва", "категорія", "ціна", "на складі"])
    if назва in df["назва"].values:
        return f"⚠️ Товар '{назва}' вже існує."

    new_row = {
        "назва": назва,
        "категорія": категорія,
        "ціна": ціна,
        "на складі": kwargs.get("на складі", "1")
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(PRODUCTS_PATH, index=False)
    return f"✅ Товар '{назва}' додано до таблиці (як тестовий запис)."

def list_all_products() -> str:
    if not os.path.exists(PRODUCTS_PATH):
        return "⚠️ Таблиця товарів не знайдена."

    df = pd.read_csv(PRODUCTS_PATH)
    if df.empty:
        return "📦 Таблиця товарів порожня."

    result = "🧾 У нас є такі товари:\n"
    for _, row in df.iterrows():
        result += f"- {row['назва']} ({row['категорія']}): {row['ціна']} грн\n"
    return result.strip()
