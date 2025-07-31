# dashboard.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os

# --- 1. Загрузка и обработка данных ---
@st.cache_data # Кэшируем данные для ускорения повторных загрузок
def load_and_process_data():
    # Определяем путь к папке 'Визуализация' относительно местоположения этого скрипта
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, "Визуализация")

    # Загружаем файлы, используя полный путь
    try:
        calendar = pd.read_excel(os.path.join(data_dir, 'Календарь.xlsx'))
        partner = pd.read_excel(os.path.join(data_dir, 'Контрагенты.xlsx'))
        plan = pd.read_excel(os.path.join(data_dir, 'План по категориям.xlsx'))
        staff = pd.read_excel(os.path.join(data_dir, 'Сотрудники.xlsx'))
        products = pd.read_excel(os.path.join(data_dir, 'Товары.xlsx'))
        fact = pd.read_excel(os.path.join(data_dir, 'Факт продаж.xlsx'))
    except FileNotFoundError as e:
        st.error(f"Ошибка при загрузке данных: Файл не найден. Проверьте структуру папок. Подробности: {e}")
        st.stop() # Останавливаем выполнение приложения
    except Exception as e: # Ловим другие возможные ошибки (например, с чтением Excel)
        st.error(f"Ошибка при загрузке данных: {e}")
        st.stop()

    # Обработка данных
    fact['orderdate'] = pd.to_datetime(fact['orderdate'])
    calendar['orderdate'] = pd.to_datetime(calendar['orderdate'])
    plan['Date'] = pd.to_datetime(plan['Date'])

    # Создание временных полей
    fact['year'] = fact['orderdate'].dt.year
    fact['month'] = fact['orderdate'].dt.month
    fact['day_of_week'] = fact['orderdate'].dt.day_name()

    # ИСПРАВЛЕННЫЙ расчет прибыли
    fact['profit'] = fact['netsalesamount'] - fact['supplierprice']

    # Объединение таблиц
    df = fact.merge(partner, left_on='name', right_on='name', how='left')
    df = df.merge(products, left_on='productid', right_on='productid', how='left')
    df = df.merge(staff, left_on='employee_id', right_on='employeeid', how='left')
    calendar_clean = calendar[['orderdate', 'day', 'month', 'year']]
    df = df.merge(calendar_clean, left_on='orderdate', right_on='orderdate', how='left', suffixes=('', '_cal'))
    
    return df, plan # Возвращаем df и plan_data

# Загружаем данные один раз при запуске приложения
df, plan_data = load_and_process_data()

# --- 2. Функции для анализа (все 11 вопросов) ---
# Все функции модифицированы для приема DataFrame как аргумента

def get_top_customers_by_category_country(df_to_analyze, category_name, country_name):
    """Вопрос 1: ТОП заказчики по прибыли в категории и стране"""
    filtered = df_to_analyze[(df_to_analyze['categoryname'] == category_name) & (df_to_analyze['country'] == country_name)]
    if len(filtered) == 0:
        return pd.DataFrame(columns=['name', 'profit'])
    result = filtered.groupby('name')['profit'].sum().reset_index()
    result = result.sort_values('profit', ascending=False)
    return result.head(10)

def pareto_analysis(df_to_analyze, country_name):
    """Вопрос 2: 20% заказчиков приносят 80% прибыли в стране"""
    filtered = df_to_analyze[df_to_analyze['country'] == country_name]
    if len(filtered) == 0 or filtered['profit'].sum() == 0:
        return pd.DataFrame()
    customer_profit = filtered.groupby('name')['profit'].sum().reset_index()
    customer_profit = customer_profit.sort_values('profit', ascending=False)
    customer_profit['cumulative_profit'] = customer_profit['profit'].cumsum()
    customer_profit['cumulative_percentage'] = customer_profit['cumulative_profit'] / customer_profit['profit'].sum() * 100
    customer_profit['customer_percentage'] = (customer_profit.index + 1) / len(customer_profit) * 100
    return customer_profit.head(20)

def get_promising_countries(df_to_analyze):
    """Вопрос 3: Перспективные страны"""
    country_metrics = df_to_analyze.groupby('country').agg({
        'profit': 'sum',
        'netsalesamount': 'sum',
        'name': 'nunique'
    }).reset_index()
    country_metrics.columns = ['country', 'total_profit', 'total_sales', 'unique_customers']
    country_metrics = country_metrics.sort_values('total_profit', ascending=False)
    return country_metrics

def get_top_managers_by_sales(df_to_analyze):
    """Вопрос 4: Менеджеры по объему продаж"""
    manager_sales = df_to_analyze.groupby('employeename')['netsalesamount'].sum().reset_index()
    manager_sales = manager_sales.sort_values('netsalesamount', ascending=False)
    return manager_sales

def analyze_manager_discounts(df_to_analyze):
    """Вопрос 5: Менеджеры и скидки"""
    manager_analysis = df_to_analyze.groupby('employeename').agg({
        'netsalesamount': 'sum',
        'discount': 'mean',
        'quantity': 'sum',
        'profit': 'sum'
    }).reset_index()
    manager_analysis['sales_per_transaction'] = manager_analysis['netsalesamount'] / manager_analysis['quantity']
    return manager_analysis

def get_productive_weekdays(df_to_analyze, category_name):
    """Вопрос 6: Продуктивные дни недели для категории"""
    filtered = df_to_analyze[df_to_analyze['categoryname'] == category_name]
    if len(filtered) == 0:
        return pd.DataFrame()
    weekday_sales = filtered.groupby('day_of_week')['netsalesamount'].sum().reset_index()
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekday_sales['day_of_week'] = pd.Categorical(weekday_sales['day_of_week'], categories=day_order, ordered=True)
    weekday_sales = weekday_sales.sort_values('day_of_week')
    return weekday_sales

def get_products_by_manager(df_to_analyze, manager_name):
    """Вопрос 7: Товары, проданные менеджером"""
    filtered = df_to_analyze[df_to_analyze['employeename'] == manager_name]
    if len(filtered) == 0:
        return pd.DataFrame()
    result = filtered.groupby(['productname', 'actualunitprice']).agg({
        'discount': 'mean',
        'quantity': 'sum',
        'netsalesamount': 'sum',
        'profit': 'sum'
    }).reset_index()
    return result

def get_top_products_by_category(df_to_analyze, category_name):
    """Вопрос 8: ТОП товаров в категории"""
    filtered = df_to_analyze[df_to_analyze['categoryname'] == category_name]
    if len(filtered) == 0:
        return pd.DataFrame()
    product_performance = filtered.groupby('productname').agg({
        'quantity': 'sum',
        'profit': 'sum'
    }).reset_index()
    product_performance = product_performance.sort_values('profit', ascending=False)
    return product_performance.head(10)

def analyze_product_trend(df_to_analyze, product_name):
    """Вопрос 9: Анализ тренда товара"""
    filtered = df_to_analyze[df_to_analyze['productname'] == product_name]
    if len(filtered) == 0:
        return pd.DataFrame()
    product_trend = filtered.groupby('year').agg({
        'profit': 'sum',
        'quantity': 'sum',
        'netsalesamount': 'sum'
    }).reset_index()
    return product_trend

def calculate_roi(df_to_analyze):
    """Вопрос 10: ROI по годам"""
    yearly_metrics = df_to_analyze.groupby('year').agg({
        'profit': 'sum',
        'supplierprice': 'sum'
    }).reset_index()
    yearly_metrics['roi'] = np.where(
        yearly_metrics['supplierprice'] != 0,
        (yearly_metrics['profit'] / yearly_metrics['supplierprice']) * 100,
        0
    )
    return yearly_metrics[['year', 'profit', 'supplierprice', 'roi']]

def sales_plan_performance(df_local, plan_local):
    """Вопрос 11: Выполнение плана продаж"""
    # Анализ плана обычно проводится по всем данным
    actual = df_local.groupby(df_local['orderdate'].dt.to_period('M')).agg({
        'grosssalesamount': 'sum',
        'netsalesamount': 'sum'
    }).reset_index()
    actual['Date'] = actual['orderdate'].dt.to_timestamp()
    
    plan_monthly = plan_local.groupby(plan_local['Date'].dt.to_period('M')).agg({
        'Gross_Plan': 'sum',
        'Net_Plan': 'sum'
    }).reset_index()
    plan_monthly['Date'] = plan_monthly['Date'].dt.to_timestamp()
    
    performance = actual.merge(plan_monthly, on='Date', how='outer')
    performance['gross_performance'] = np.where(
        performance['Gross_Plan'] != 0,
        (performance['grosssalesamount'] / performance['Gross_Plan']) * 100,
        0
    )
    performance['net_performance'] = np.where(
        performance['Net_Plan'] != 0,
        (performance['netsalesamount'] / performance['Net_Plan']) * 100,
        0
    )
    return performance


# --- 3. Streamlit Интерфейс ---
st.set_page_config(page_title="Аналитика продаж", layout="wide")
st.title("📊 Аналитическая панель продаж магазина одежды")

# Боковая панель с глобальными фильтрами
st.sidebar.header("Глобальные фильтры")
selected_years = st.sidebar.multiselect(
    "Выберите годы",
    options=sorted(df['year'].unique()),
    default=sorted(df['year'].unique())
)
selected_countries = st.sidebar.multiselect(
    "Выберите страны",
    options=sorted(df['country'].unique()),
    default=sorted(df['country'].unique())
)
# Новые фильтры
selected_categories = st.sidebar.multiselect(
    "Выберите категории товаров",
    options=sorted(df['categoryname'].unique()),
    default=[] # По умолчанию все категории
)
selected_managers = st.sidebar.multiselect(
    "Выберите менеджеров",
    options=sorted(df['employeename'].unique()),
    default=[] # По умолчанию все менеджеры
)

# Фильтрация основного DataFrame
filter_conditions = True
if selected_years:
    filter_conditions &= df['year'].isin(selected_years)
if selected_countries:
    filter_conditions &= df['country'].isin(selected_countries)
if selected_categories:
    filter_conditions &= df['categoryname'].isin(selected_categories)
if selected_managers:
    filter_conditions &= df['employeename'].isin(selected_managers)

filtered_df = df[filter_conditions]

# Отображение ключевых метрик
st.header("Ключевые метрики")
col1, col2, col3 = st.columns(3)
col1.metric("Общая прибыль", f"{filtered_df['profit'].sum():,.2f}")
col2.metric("Объем продаж (Net)", f"{filtered_df['netsalesamount'].sum():,.2f}")
col3.metric("Кол-во уникальных клиентов", filtered_df['name'].nunique())

# Разделение на вкладки для каждого вопроса
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11 = st.tabs([
    "1. ТОП клиенты", "2. 20/80 правило", "3. Страны", "4. Менеджеры",
    "5. Скидки менеджеров", "6. Дни недели", "7. Товары менеджера",
    "8. ТОП товаров", "9. Тренд товара", "10. ROI", "11. План продаж"
])

with tab1:
    st.header("1. ТОП заказчиков по прибыли")
    st.subheader("Женская обувь в Германии (с учетом фильтров)")
    st.info("Анализ проводится по отфильтрованным данным (выбранные года, страны, категории, менеджеры)")
    top_customers_1 = get_top_customers_by_category_country(filtered_df, "Женская обувь", "Германия")
    if not top_customers_1.empty:
        st.dataframe(top_customers_1)
        fig1 = px.bar(
            top_customers_1,
            x='name',
            y='profit',
            title='ТОП клиентов по прибыли (Женская обувь, Германия)',
            color='profit',
            color_continuous_scale='tealrose'
        )
        fig1.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.warning("Нет данных для выбранной категории и страны после применения фильтров.")

with tab2:
    st.header("2. Анализ Парето (20/80)")
    st.subheader("Бразилия (с учетом фильтров)")
    st.info("Анализ проводится по отфильтрованным данным")
    pareto_data_2 = pareto_analysis(filtered_df, "Бразилия")
    if not pareto_data_2.empty:
        st.dataframe(pareto_data_2)
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=pareto_data_2['customer_percentage'],
            y=pareto_data_2['cumulative_percentage'],
            mode='lines+markers',
            name='Кумулятивная прибыль (%)'
        ))
        fig2.add_trace(go.Scatter(
            x=[0, 100],
            y=[0, 100],
            mode='lines',
            name='Линия равенства (20/80)',
            line=dict(dash='dash', color='red')
        ))
        fig2.update_layout(
            title='Анализ Парето: 20% клиентов приносят 80% прибыли (Бразилия)',
            xaxis_title='Процент клиентов (%)',
            yaxis_title='Кумулятивная доля прибыли (%)',
            showlegend=True
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("Нет данных для анализа Парето по Бразилии после применения фильтров.")

with tab3:
    st.header("3. Перспективные страны")
    st.info("Анализ проводится по отфильтрованным данным")
    countries_3 = get_promising_countries(filtered_df)
    if not countries_3.empty:
        st.dataframe(countries_3)
        fig3 = px.bar(
            countries_3.head(10),
            x='country',
            y='total_profit',
            title='ТОП-10 стран по общей прибыли (с фильтрами)',
            color='total_profit',
            color_continuous_scale='blues'
        )
        fig3.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.warning("Нет данных по странам после применения фильтров.")

with tab4:
    st.header("4. ТОП менеджеров по объему продаж")
    st.info("Анализ проводится по отфильтрованным данным")
    manager_sales_4 = get_top_managers_by_sales(filtered_df)
    if not manager_sales_4.empty:
        st.dataframe(manager_sales_4)
        fig4 = px.bar(
            manager_sales_4,
            x='employeename',
            y='netsalesamount',
            title='Объем продаж по менеджерам (с фильтрами)',
            color='netsalesamount',
            color_continuous_scale='sunset'
        )
        fig4.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.warning("Нет данных по менеджерам после применения фильтров.")

with tab5:
    st.header("5. Менеджеры и скидки")
    st.info("Анализ проводится по отфильтрованным данным")
    manager_discounts_5 = analyze_manager_discounts(filtered_df)
    if not manager_discounts_5.empty:
        st.dataframe(manager_discounts_5)
        fig5 = px.scatter(
            manager_discounts_5,
            x='discount',
            y='netsalesamount',
            size='profit',
            color='employeename',
            hover_name='employeename',
            title='Соотношение средней скидки и объема продаж по менеджерам (с фильтрами)',
            labels={'discount': 'Средняя скидка', 'netsalesamount': 'Объем продаж (Net Sales)', 'profit': 'Прибыль'}
        )
        st.plotly_chart(fig5, use_container_width=True)
    else:
        st.warning("Нет данных по менеджерам после применения фильтров.")

with tab6:
    st.header("6. Продуктивные дни недели")
    st.subheader("Одежда для новорожденных (с учетом фильтров)")
    st.info("Анализ проводится по отфильтрованным данным")
    weekdays_6 = get_productive_weekdays(filtered_df, "Одежда для новорожденных")
    if not weekdays_6.empty:
        st.dataframe(weekdays_6)
        fig6 = px.bar(
            weekdays_6,
            x='day_of_week',
            y='netsalesamount',
            title='Объем продаж по дням недели (Одежда для новорожденных)',
            color='netsalesamount',
            color_continuous_scale='mint'
        )
        st.plotly_chart(fig6, use_container_width=True)
    else:
        st.warning("Нет данных для категории 'Одежда для новорожденных' после применения фильтров.")

with tab7:
    st.header("7. Товары, проданные Матвеем Крыловым")
    st.subheader("(с учетом фильтров)")
    st.info("Анализ проводится по отфильтрованным данным")
    matvey_products_7 = get_products_by_manager(filtered_df, "Матвей Крылов")
    if not matvey_products_7.empty:
        st.dataframe(matvey_products_7)
        matvey_top = matvey_products_7.nlargest(10, 'profit')
        if not matvey_top.empty:
            fig7 = px.bar(
                matvey_top,
                x='productname',
                y='profit',
                title='ТОП товаров Матвея Крылова по прибыли',
                color='profit',
                color_continuous_scale='purp'
            )
            fig7.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig7, use_container_width=True)
    else:
        st.warning("Нет данных о продажах Матвея Крылова после применения фильтров.")

with tab8:
    st.header("8. ТОП товаров категории")
    st.subheader("Пляжная одежда (с учетом фильтров)")
    st.info("Анализ проводится по отфильтрованным данным")
    beach_products_8 = get_top_products_by_category(filtered_df, "Пляжная одежда")
    if not beach_products_8.empty:
        st.dataframe(beach_products_8)
        fig8 = px.bar(
            beach_products_8,
            x='productname',
            y=['quantity', 'profit'],
            title='ТОП товаров категории "Пляжная одежда" (Количество и Прибыль)',
            barmode='group'
        )
        fig8.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig8, use_container_width=True)
    else:
        st.warning("Нет данных для категории 'Пляжная одежда' после применения фильтров.")

with tab9:
    st.header("9. Тренд товара")
    st.info("Анализ проводится по отфильтрованным данным")
    # Используем первый товар из отфильтрованных данных для демонстрации
    if not filtered_df.empty:
        sample_product_9 = filtered_df['productname'].iloc[0]
        st.subheader(f"Анализ товара: {sample_product_9}")
        product_trend_9 = analyze_product_trend(filtered_df, sample_product_9)
        if not product_trend_9.empty:
            st.dataframe(product_trend_9)
            fig9 = px.line(
                product_trend_9,
                x='year',
                y='profit',
                markers=True,
                title=f'Динамика прибыли по товару: {sample_product_9}'
            )
            st.plotly_chart(fig9, use_container_width=True)
        else:
            st.warning("Нет данных для тренда этого товара после применения фильтров.")
    else:
        st.warning("Нет данных для анализа тренда после применения фильтров.")

with tab10:
    st.header("10. Коэффициент возврата инвестиций (ROI)")
    st.info("Анализ проводится по отфильтрованным данным")
    roi_data_10 = calculate_roi(filtered_df)
    if not roi_data_10.empty:
        st.dataframe(roi_data_10)
        fig10 = px.line(
            roi_data_10,
            x='year',
            y='roi',
            markers=True,
            title='Коэффициент возврата инвестиций (ROI) по годам (с фильтрами)',
            color_discrete_sequence=['green']
        )
        st.plotly_chart(fig10, use_container_width=True)
    else:
        st.warning("Нет данных для расчета ROI после применения фильтров.")

with tab11:
    st.header("11. Выполнение плана продаж")
    st.info("Анализ выполнения плана показан по всем историческим данным")
    # Используем оригинальные данные df и plan_data, так как план фиксирован
    plan_performance_11 = sales_plan_performance(df, plan_data)
    plan_performance_11['Date'] = pd.to_datetime(plan_performance_11['Date'])

    if not plan_performance_11.empty:
        st.dataframe(plan_performance_11)
        fig11 = go.Figure()
        fig11.add_trace(go.Scatter(
            x=plan_performance_11['Date'],
            y=plan_performance_11['gross_performance'],
            mode='lines+markers',
            name='Выполнение плана (Gross Sales)',
            line=dict(color='blue')
        ))
        fig11.add_trace(go.Scatter(
            x=plan_performance_11['Date'],
            y=plan_performance_11['net_performance'],
            mode='lines+markers',
            name='Выполнение плана (Net Sales)',
            line=dict(color='orange')
        ))
        fig11.add_hline(y=100, line_dash="dash", line_color="red", annotation_text="100% План")
        fig11.update_layout(
            title='Выполнение плана продаж по месяцам',
            xaxis_title="Дата",
            yaxis_title="Выполнение плана (%)"
        )
        st.plotly_chart(fig11, use_container_width=True)
    else:
        st.warning("Нет данных для анализа выполнения плана.")
