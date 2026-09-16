import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import urllib.parse  # Добавляем этот импорт для работы с ссылками

# Настройка страницы
st.set_page_config(page_title="👩‍💼 Текучка кадров", layout="wide")

@st.cache_data(ttl=10800) # Кэшируем на 3ч.
def load_data():
    sheet_id = "1yMi4B18NMKmD53WK2iuWN2FAfLy1VkoG-Kwdbb1N-R0"
    
    # Оборачиваем русские названия в urllib.parse.quote()
    sheet_name_analit = urllib.parse.quote("Аналитика2") 
    sheet_name_details = urllib.parse.quote("Ушедшие") 
    
    url_analit = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name_analit}"
    url_details = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name_details}"
    
    # Читаем данные
    df_analit = pd.read_csv(url_analit)
    df_details = pd.read_csv(url_details)
    
    # Создаем датафрейм руководителей
    mgr_data = {
        "Отдел": ["IT.DEV", "IT. QA", "Support Senior", "Support", "Admin", "Marketing", "QC"],
        "Руководитель": ["Алексей", "Александра", "Mr. White", "Mr. Black", "Евгений", "Professor", "Joker"]
    }
    df_managers = pd.DataFrame(mgr_data)
    
    # НАСТРОЙКА НАЗВАНИЙ КОЛОНОК 
    col_dept_an = "Отдел"
    col_dept_det = "Отдел"
    
    # Джойним руководителей
    if col_dept_an in df_analit.columns:
        df_analit = pd.merge(df_analit, df_managers, left_on=col_dept_an, right_on="Отдел", how="left")
    if col_dept_det in df_details.columns:
        df_details = pd.merge(df_details, df_managers, left_on=col_dept_det, right_on="Отдел", how="left")
        
    return df_analit, df_details

df_analit, df_details = load_data()

st.title("👩‍💼 Текучка кадров (Inflow / Outflow)")
st.markdown("---")

# --- ФИЛЬТРЫ СВЕРХУ ---
col_f1, col_f2 = st.columns(2)
with col_f1:
    depts = df_details['Отдел'].dropna().unique().tolist() if 'Отдел' in df_details.columns else []
    selected_depts = st.multiselect("Отдел", options=depts)
with col_f2:
    mgrs = df_details['Руководитель'].dropna().unique().tolist() if 'Руководитель' in df_details.columns else []
    selected_mgrs = st.multiselect("Руководитель", options=mgrs)

# Применяем фильтры к обоим датафреймам
filtered_analit = df_analit.copy()
filtered_details = df_details.copy()

if selected_depts:
    if 'Отдел' in filtered_analit.columns:
        filtered_analit = filtered_analit[filtered_analit['Отдел'].isin(selected_depts)]
    if 'Отдел' in filtered_details.columns:
        filtered_details = filtered_details[filtered_details['Отдел'].isin(selected_depts)]

if selected_mgrs:
    if 'Руководитель' in filtered_analit.columns:
        filtered_analit = filtered_analit[filtered_analit['Руководитель'].isin(selected_mgrs)]
    if 'Руководитель' in filtered_details.columns:
        filtered_details = filtered_details[filtered_details['Руководитель'].isin(selected_mgrs)]

# --- КОНСТАНТЫ КОЛОНОК АНАЛИТИКИ ---
col_month = "Дата"
col_inflow = "Принято"
col_outflow = "Уволено"
col_hc_start = "Число на начало"
col_hc_end = "Число на конец"

# Вычисляем "Число на конец", так как его нет в исходной таблице
if not filtered_analit.empty and set([col_hc_start, col_inflow, col_outflow]).issubset(filtered_analit.columns):
    filtered_analit[col_hc_end] = filtered_analit[col_hc_start] + filtered_analit[col_inflow] - filtered_analit[col_outflow]

st.markdown("---")

# --- 1) KPI КАРТОЧКИ ---
kpi_col1, kpi_col2 = st.columns(2)

# Агрегируем данные для расчета текучки
if not filtered_analit.empty and set([col_inflow, col_outflow, col_hc_start, col_hc_end]).issubset(filtered_analit.columns):
    total_outflow = filtered_analit[col_outflow].sum()
    avg_headcount = (filtered_analit[col_hc_start].sum() + filtered_analit[col_hc_end].sum()) / 2
    
    turnover_rate = (total_outflow / avg_headcount * 100) if avg_headcount > 0 else 0
    actual_headcount = filtered_analit[col_hc_end].iloc[-1] # Последняя запись в отфильтрованной дате
else:
    turnover_rate = 0.0
    actual_headcount = 0

with kpi_col1:
    st.metric(label="Текучка кадров (Turnover Rate)", value=f"{turnover_rate:.1f}%")
with kpi_col2:
    st.metric(label="Актуальное кол-во сотрудников", value=int(actual_headcount))

st.markdown("---")

# --- 2) ВИЗУАЛЬНЫЙ ЭЛЕМЕНТ: Inflow + Outflow Chart ---
st.subheader("Динамика найма и увольнений (Net Flow)")

if not filtered_analit.empty and col_month in filtered_analit.columns:
    # Группируем по датам на случай, если выбрали несколько отделов
    chart_data = filtered_analit.groupby(col_month)[[col_inflow, col_outflow, col_hc_start]].sum().reset_index()
    
    fig = go.Figure()
    
    # Принятые (Положительные столбцы)
    fig.add_trace(go.Bar(
        x=chart_data[col_month], 
        y=chart_data[col_inflow], 
        name='Принято', 
        marker_color='#2ecc71',
        text=chart_data[col_inflow],
        textposition='auto'
    ))
    
    # Уволенные (Отрицательные столбцы) - умножаем на -1 для отображения вниз
    fig.add_trace(go.Bar(
        x=chart_data[col_month], 
        y=-chart_data[col_outflow], 
        name='Уволено', 
        marker_color='#e74c3c',
        text=chart_data[col_outflow],
        textposition='auto'
    ))
    
    # Линейный график - Штат на начало
    fig.add_trace(go.Scatter(
        x=chart_data[col_month], 
        y=chart_data[col_hc_start], 
        mode='lines+markers', 
        name='Штат (на начало)', 
        line=dict(color='#3498db', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        barmode='relative',
        title="Inflow vs Outflow & Headcount",
        xaxis_title="Период",
        yaxis_title="Количество сотрудников",
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Нет данных для графика или неверно указаны названия колонок в коде.")

st.markdown("---")

# --- 3) ДЕТАЛЬНАЯ ТАБЛИЦА (Ушедшие) ---
st.subheader("Детализация по ушедшим сотрудникам")

# Доп. фильтры специально для таблицы
col_initiator = "Инициатор"
col_reason = "Причины увольнения"
col_probation = "ИС"

if not filtered_details.empty:
    t_col1, t_col2, t_col3 = st.columns(3)
    
    with t_col1:
        if col_initiator in filtered_details.columns:
            init_opts = filtered_details[col_initiator].dropna().unique()
            selected_init = st.multiselect("Инициатор", options=init_opts)
            if selected_init:
                filtered_details = filtered_details[filtered_details[col_initiator].isin(selected_init)]
                
    with t_col2:
        if col_reason in filtered_details.columns:
            reason_opts = filtered_details[col_reason].dropna().unique()
            selected_reason = st.multiselect("Причина увольнения", options=reason_opts)
            if selected_reason:
                filtered_details = filtered_details[filtered_details[col_reason].isin(selected_reason)]
                
    with t_col3:
        if col_probation in filtered_details.columns:
            prob_opts = filtered_details[col_probation].dropna().unique()
            selected_prob = st.multiselect("Статус ИС", options=prob_opts)
            if selected_prob:
                filtered_details = filtered_details[filtered_details[col_probation].isin(selected_prob)]

    # Вывод интерактивной таблицы
    st.dataframe(filtered_details, use_container_width=True, hide_index=True)
else:
    st.info("Нет данных по уволенным с заданными фильтрами.")
