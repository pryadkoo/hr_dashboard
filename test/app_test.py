import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Настройки страницы
st.set_page_config(page_title="Тестовый стенд", layout="wide")

st.title("Проверка доступности дашборда")
st.write("Если вы видите этот текст, интерактивные фильтры и график то сервис работает! Ура!.")

# 1. Генерируем тестовые данные
np.random.seed(42)
dates = pd.date_range(start="2026-01-01", periods=30)
categories = ["Маркетинг", "Продажи", "Поддержка"]

data = {
    "Дата": np.repeat(dates, len(categories)),
    "Отдел": categories * len(dates),
    "Метрика": np.random.randint(100, 1000, size=len(dates) * len(categories))
}
df = pd.DataFrame(data)

# 2. Боковая панель 
st.sidebar.header("Параметры фильтрации")
selected_dept = st.sidebar.multiselect(
    "Выберите отдел:",
    options=categories,
    default=categories
)

# Фильтруем
df_filtered = df[df["Отдел"].isin(selected_dept)]

# 3. Карточки KPI
col1, col2 = st.columns(2)
col1.metric("Сумма метрики", f"{df_filtered['Метрика'].sum():,}")
col2.metric("Количество записей", len(df_filtered))

# 4. Plotly
fig = px.line(
    df_filtered, 
    x="Дата", 
    y="Метрика", 
    color="Отдел", 
    title="Динамика по дням (наведите курсор для проверки интерактива)"
)
st.plotly_chart(fig, use_container_width=True)

st.success("✅ Тест пройден успешно!")
