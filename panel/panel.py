import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# Настройка страницы
st.set_page_config(page_title="💻 HR Panel", layout="wide")

# --- КНОПКА ПЕРЕХОДА НА ВТОРОЙ ДАШБОРД ---
st.link_button("➡️ Перейти к дашборду Текучки кадров", "https://hrdashboard-flow.streamlit.app/")

@st.cache_data(ttl=10800) # Кэшируем на 3ч.
def load_data():
    sheet_id = "1Ng7P1ZU3ObeE3XSVjWGGGjMfJOD5rAvQor4mfWbuWbM"
    
    sheet_name_union = "union" 
    sheet_name_metrics = "metrics" 
    
    url_union = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name_union}"
    url_metrics = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name_metrics}"
    
    df = pd.read_csv(url_union)
    metrics_df = pd.read_csv(url_metrics)
    
    dept_col = [c for c in df.columns if c.startswith('1.')][0]
    tenure_col = [c for c in df.columns if c.startswith('2.')][0]
    date_col = 'Отметка времени'
    
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df['Дата'] = df[date_col].dt.date
    
    return df, metrics_df, dept_col, tenure_col

df, metrics_df, dept_col, tenure_col = load_data()

# --- НАЗВАНИЕ И ФИЛЬТРЫ СВЕРХУ ---
st.title("HR Panel")
st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    selected_depts = st.multiselect("Отдел", options=df[dept_col].dropna().unique())
with col2:
    selected_tenures = st.multiselect("Стаж работы", options=df[tenure_col].dropna().unique())

# Применяем фильтры
filtered_df = df.copy()
if selected_depts:
    filtered_df = filtered_df[filtered_df[dept_col].isin(selected_depts)]
if selected_tenures:
    filtered_df = filtered_df[filtered_df[tenure_col].isin(selected_tenures)]

st.markdown("---")

# --- KPI КАРТОЧКИ ---
# Ищем колонки под метрики динамически, опираясь на справочник (номера 3 и 17)
esi_col = [c for c in df.columns if c.startswith('3.')][0]
enps_col = [c for c in df.columns if c.startswith('17.')][0]

kpi_cols = st.columns(3)
with kpi_cols[0]:
    st.metric("Кол-во ответов", len(filtered_df))
with kpi_cols[1]:
    avg_esi = filtered_df[esi_col].mean()
    st.metric("Средний ESI", f"{avg_esi:.2f}" if pd.notnull(avg_esi) else "Нет данных")
with kpi_cols[2]:
    avg_enps = filtered_df[enps_col].mean()
    st.metric("Средний eNPS", f"{avg_enps:.2f}" if pd.notnull(avg_enps) else "Нет данных")

st.markdown("---")

# --- ДВА БАР-ЧАРТА (ГОРИЗОНТАЛЬНЫЕ) ---
st.subheader("Разрез метрик ESI и eNPS")
group_by_option = st.radio("Сгруппировать графики по:", ["Отдел", "Стаж работы"], horizontal=True)
group_col = dept_col if group_by_option == "Отдел" else tenure_col

col_chart1, col_chart2 = st.columns(2)

# Агрегация для графиков
chart_data = filtered_df.groupby(group_col)[[esi_col, enps_col]].mean().reset_index()

with col_chart1:
    fig_esi = px.bar(chart_data, y=group_col, x=esi_col, orientation='h', 
                     title="ESI", text_auto='.2f', color_discrete_sequence=['#3498db'])
    st.plotly_chart(fig_esi, use_container_width=True)

with col_chart2:
    fig_enps = px.bar(chart_data, y=group_col, x=enps_col, orientation='h', 
                      title="eNPS", text_auto='.2f', color_discrete_sequence=['#2ecc71'])
    st.plotly_chart(fig_enps, use_container_width=True)

st.markdown("---")

# --- ВЕРТИКАЛЬНЫЙ БАР-ЧАРТ ДИНАМИКИ ---
st.subheader("Динамика показателей во времени")

numeric_cols = filtered_df.select_dtypes(include=['int64', 'float64']).columns.tolist()
numeric_cols = [c for c in numeric_cols if c not in ['Баллы']] 

y_axis_col = st.selectbox("Выберите метрику для оси Y:", numeric_cols)

if not filtered_df.empty and y_axis_col:
    # Приводим к дате и месяцу
    filtered_df['Дата'] = pd.to_datetime(filtered_df['Дата'])
    filtered_df['Месяц'] = filtered_df['Дата'].dt.strftime('%Y-%m')
    
    # Группируем и сортируем по времени (в прямом порядке, слева направо)
    time_data = filtered_df.groupby('Месяц')[y_axis_col].mean().reset_index()
    time_data = time_data.sort_values('Месяц')
    
    # Строим вертикальный столбчатый график
    fig_time = px.bar(
        time_data, 
        x='Месяц', 
        y=y_axis_col, 
        title=f"Динамика: {y_axis_col[:50]}...",
        text_auto='.2f'
    )
    
    # Месяцы у нас по оси X, фиксируем это как категории, чтобы не слипались
    fig_time.update_xaxes(type='category')
    st.plotly_chart(fig_time, use_container_width=True)

st.markdown("---")

# --- ОТКРЫТАЯ ОБРАТНАЯ СВЯЗЬ (ТАБЛИЦА) ---
st.subheader("Открытая обратная связь (Вопросы 16 и 18)")
q16_col = [c for c in df.columns if c.startswith('16.')][0]
q18_col = [c for c in df.columns if c.startswith('18.')][0]

feedback_df = filtered_df.dropna(subset=[q16_col, q18_col], how='all').reset_index(drop=True)

if not feedback_df.empty:
    st.caption(f"Всего ответов: {len(feedback_df)}")
    
    # Оставляем только нужные колонки и переименовываем для читаемости
    display_df = feedback_df[[dept_col, tenure_col, q16_col, q18_col]].rename(columns={
        dept_col: "Отдел",
        tenure_col: "Стаж",
        q16_col: "Что изменить (Q16)",
        q18_col: "Что мешает (Q18)"
    })
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
else:
    st.write("Нет текстовых ответов по выбранным фильтрам.")

st.markdown("---")

# --- ILLUSTRATION DIAGRAM (ТИПИЧНЫЙ СОТРУДНИК) ---
st.subheader("Портрет типичного сотрудника (на основе фильтров)")

if not filtered_df.empty:
    mode_dept = filtered_df[dept_col].mode()[0] if not filtered_df[dept_col].empty else "Неизвестно"
    mode_tenure = filtered_df[tenure_col].mode()[0] if not filtered_df[tenure_col].empty else "Неизвестно"
    
    # Берем самые частые или случайные ответы для облака мыслей
    sample_q18 = filtered_df[q18_col].dropna().iloc[0] if not filtered_df[q18_col].dropna().empty else "Всё ок"
    sample_q16 = filtered_df[q16_col].dropna().iloc[0] if not filtered_df[q16_col].dropna().empty else "Ничего не хочу менять"
    
    col_left, col_mid, col_right = st.columns([1, 1, 2])
    
    with col_mid:
        st.markdown("<h1 style='text-align: center; font-size: 80px;'>🧑‍💻</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center;'><b>Отдел:</b> {mode_dept}<br><b>Стаж:</b> {mode_tenure}</p>", unsafe_allow_html=True)
        
    with col_left:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.info(f"💭 **Впечатление (ESI):**\nВ среднем оценивает на {avg_esi:.1f} из 5")
        st.info(f"💭 **Лояльность (eNPS):**\nГотовность рекомендовать: {avg_enps:.1f} из 10")
        
    with col_right:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.error(f"🗣 **Что болит:**\n*{sample_q18}*")
        st.success(f"🗣 **Что хочет изменить:**\n*{sample_q16}*")
else:
    st.write("Недостаточно данных для формирования портрета.")
