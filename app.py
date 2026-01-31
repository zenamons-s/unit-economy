"""
SaaS Unit Economics Dashboard
Основное приложение Streamlit с полной функциональностью
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import time
import io
import base64
from typing import Dict, List, Optional, Any
import sys
import os


# Добавляем пути к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Импортируем наши модули
from database.db_manager import db_manager, Company, FinancialPlan, MonthlyPlan, ActualData, VarianceAnalysisResult

# Core services - импортируем классы и создаем экземпляры
from services.core.stage_aware_metrics import StageAwareMetrics
stage_aware_metrics = StageAwareMetrics()

from services.core.pre_seed_advisor import PreSeedAdvisor
pre_seed_advisor = PreSeedAdvisor()

from services.core.cohort_analyzer import RealisticCohortAnalyzer
cohort_analyzer = RealisticCohortAnalyzer()

from services.core.year_1_roadmap import Year1Roadmap
year_1_roadmap = Year1Roadmap()

from services.core.runway_calculator import RunwayCalculator
runway_calculator = RunwayCalculator()

# Financial system
from services.financial_system.financial_planner import FinancialPlanner
financial_planner = FinancialPlanner()

# variance_analyzer должен быть уже создан в модуле как объект
from services.financial_system.variance_analyzer import variance_analyzer

# monthly_tracker должен быть уже создан в модуле как объект
from services.financial_system.monthly_tracker import monthly_tracker

from services.financial_system.ai_recommendations import AIRecommendationEngine
ai_recommendation_engine = AIRecommendationEngine(use_gigachat=True)

from services.financial_system.saas_benchmarks import SaaSBenchmarks
saas_benchmarks = SaaSBenchmarks()

from services.financial_system.scenario_simulator import ScenarioSimulator
scenario_simulator = ScenarioSimulator()

# Utils - это должны быть функции, а не классы
from services.utils.data_validator import validate_company_input, validate_financial_metrics
from services.utils.export_generator import export_report, export_financial_plan, export_dataframe_to_file
from services.utils.visualization import create_financial_dashboard, create_mrr_growth_visualization

# Reports - это должны быть функции
from reports.investor_report import generate_investor_pitch_deck, generate_investment_memo
from reports.board_report import generate_quarterly_board_report
from reports.monthly_report import generate_management_report, generate_team_report

# GigaChat - это должны быть функции

from gigachat_analyst import analyze_with_gigachat, get_gigachat_health_check

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройка страницы Streamlit
st.set_page_config(
    page_title="SaaS Unit Economics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Инициализация базы данных
@st.cache_resource(show_spinner=False)
def initialize_database():
    logger.info("Инициализация базы данных...")
    try:
        db_manager.initialize_database()
        logger.info("База данных инициализирована успешно")

        # Проверяем, что таблицы созданы
        time.sleep(1)
    except Exception as e:
        logger.error(f"Ошибка инициализации БД: {e}")
        st.error(f"Ошибка инициализации базы данных: {e}")


initialize_database()

# Настройка стилей
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2E86C1;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #3498DB;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .warning-message {
        background-color: #fff3cd;
        color: #856404;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .info-message {
        background-color: #d1ecf1;
        color: #0c5460;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

class SAASDashboardApp:
    """
    Основное приложение SaaS Unit Economics Dashboard
    """
    
    def __init__(self):
        self.current_company_id = None
        self.current_user = None
        self.initialize_session_state()
    
    def initialize_session_state(self):
        """Инициализация состояния сессии"""
        
        if 'company_id' not in st.session_state:
            st.session_state.company_id = None
        if 'current_tab' not in st.session_state:
            st.session_state.current_tab = "🏠 Dashboard"
        if 'ai_analysis' not in st.session_state:
            st.session_state.ai_analysis = None
        if 'export_data' not in st.session_state:
            st.session_state.export_data = None
    
    def run(self):
        """Запуск основного приложения"""
        


        # Заголовок приложения
        st.markdown('<h1 class="main-header">📊 SaaS Unit Economics Dashboard</h1>', unsafe_allow_html=True)
        
        # Боковая панель навигации
        with st.sidebar:
            st.image("https://img.icons8.com/color/96/000000/analytics.png", width=100)
            st.markdown("## Навигация")
            
            # Выбор компании если еще не выбрана
            if not st.session_state.company_id:
                self.render_company_selection()
            else:
                # Отображение информации о компании
                company = db_manager.get_company(st.session_state.company_id)
                if company:
                    st.markdown(f"### {company.name}")
                    st.markdown(f"**Stage:** {company.stage}")
                    st.markdown(f"**MRR:** ${company.current_mrr:,.0f}")
                    st.markdown(f"**Customers:** {company.current_customers:,.0f}")
                    st.markdown("---")
                
                # Навигационные вкладки
                tabs = [
                    "🏠 Dashboard",
                    "📈 Financial Planning",
                    "📊 Actual Tracking",
                    "🔍 Variance Analysis",
                    "🎯 Scenario Simulation",
                    "🤖 AI Analyst",
                    "📋 Reports",
                    "⚙️ Settings"
                ]
                
                selected_tab = st.selectbox(
                    "Выберите раздел",
                    tabs,
                    index=tabs.index(st.session_state.current_tab) if st.session_state.current_tab in tabs else 0
                )
                
                st.session_state.current_tab = selected_tab
                
                # Быстрые действия
                st.markdown("---")
                st.markdown("### Быстрые действия")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🔄 Обновить данные", width='stretch'):
                        st.rerun()
                
                with col2:
                    if st.button("📤 Экспорт", width='stretch'):
                        st.session_state.current_tab = "📋 Reports"
                        st.rerun()
                
                st.markdown("---")
                
                # Выход из компании
                if st.button("🚪 Сменить компанию", type="secondary", width='stretch'):
                    st.session_state.company_id = None
                    st.rerun()
            
            # Добавьте кнопки для отладки (отображаются всегда, вне зависимости от выбора компании)
            st.markdown("---")
            st.markdown("### 🐛 Отладка")
            
            if st.button("🔍 Проверить БД", key="debug_db"):
                st.info("Проверка базы данных...")
                try:
                    companies = db_manager.get_all_companies()
                    st.write(f"Всего компаний в БД: {len(companies)}")
                    if companies:
                        for comp in companies:
                            st.write(f"- {comp.name} (ID: {comp.id}, Stage: {comp.stage})")
                    else:
                        st.write("В БД нет компаний")
                except Exception as e:
                    st.error(f"Ошибка при проверке БД: {e}")
            
            if st.button("🗑️ Очистить session state", key="clear_session_sidebar"):
                # Сохраняем только самые важные ключи
                keys_to_keep = []  # можно указать ключи для сохранения, если нужно
                
                # Собираем ключи для удаления
                keys_to_delete = []
                for key in st.session_state.keys():
                    if key not in keys_to_keep:
                        keys_to_delete.append(key)
                
                # Удаляем ключи
                for key in keys_to_delete:
                    del st.session_state[key]
                
                st.success(f"Очищено {len(keys_to_delete)} ключей в session state!")
                st.rerun()
            
            # Дополнительная отладочная информация
            if st.checkbox("Показать отладочную информацию", key="show_debug_info"):
                st.markdown("---")
                st.markdown("#### Отладочная информация:")
                st.write(f"Текущая вкладка: {st.session_state.get('current_tab', 'Не установлена')}")
                st.write(f"ID компании: {st.session_state.get('company_id', 'Не выбрана')}")
                st.write(f"Ключи в session state: {list(st.session_state.keys())}")
        
        # ГЛАВНОЕ ИСПРАВЛЕНИЕ: Отображаем главный контент если компания выбрана
        if st.session_state.company_id:
            self.render_main_content()
        else:
            # Если компания не выбрана, показываем welcome screen
            self.render_welcome_screen()

    
    def render_company_selection(self):
        """Рендеринг выбора компании"""
        
        st.markdown("## Выбор компании")
        
        # Опция: создать новую компанию
        if st.button("➕ Создать новую компанию", width='stretch'):
            self.render_company_creation()
            return
        
        st.markdown("---")
        st.markdown("### Или выберите существующую")
        
        # Получение списка компаний
        companies = db_manager.get_all_companies()
        
        if not companies:
            st.info("Нет созданных компаний. Создайте новую компанию.")
            return
        
        # Отображение списка компаний
        for company in companies:
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.markdown(f"**{company.name}**")
                st.caption(f"Stage: {company.stage}")
            
            with col2:
                st.markdown(f"${company.current_mrr:,.0f} MRR")
                st.caption(f"{company.current_customers} customers")
            
            with col3:
                if st.button("Выбрать", key=f"select_{company.id}", width='stretch'):
                    st.session_state.company_id = company.id
                    st.rerun()
            
            st.divider()
    
    def render_company_creation(self):
        """Рендеринг создания компании - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
        
        st.markdown("## Создание новой компании")
        
        with st.form("company_creation_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Название компании*", placeholder="Acme Inc.")
                stage = st.selectbox(
                    "Стадия компании*",
                    ["pre_seed", "seed", "series_a", "series_b", "series_c", "growth", "mature"],
                    format_func=lambda x: x.replace("_", " ").title()
                )
                current_mrr = st.number_input(
                    "Текущий MRR ($)*",
                    min_value=0.0,
                    value=10000.0,
                    step=1000.0
                )
                current_customers = st.number_input(
                    "Количество клиентов*",
                    min_value=0,
                    value=100,
                    step=10
                )
            
            with col2:
                monthly_price = st.number_input(
                    "Средняя месячная цена ($)*",
                    min_value=0.0,
                    value=100.0,
                    step=10.0
                )
                team_size = st.number_input(
                    "Размер команды*",
                    min_value=1,
                    value=10,
                    step=1
                )
                cash_balance = st.number_input(
                    "Текущий cash balance ($)",
                    min_value=0.0,
                    value=500000.0,
                    step=10000.0
                )
                industry = st.text_input("Индустрия", placeholder="SaaS, FinTech, etc.")
            
            description = st.text_area("Описание компании", placeholder="Описание бизнеса и продукта...")
            
            submitted = st.form_submit_button("Создать компанию", type="primary", width='stretch')
            
            if submitted:
                try:
                    # ВАЖНО: Убедитесь, что мы используем правильный объект Company
                    # Импорт должен быть правильным
                    from database.db_manager import Company
                    
                    # Создаем объект Company
                    company = Company(
                        name=name,
                        stage=stage,
                        current_mrr=current_mrr,
                        current_customers=current_customers,
                        monthly_price=monthly_price,
                        team_size=team_size,
                        cash_balance=cash_balance,
                        industry=industry,
                        description=description
                    )
                    
                    # Сохраняем в БД
                    company_id = db_manager.create_company(company)
                    
                    if company_id:
                        # Устанавливаем company_id в session state
                        st.session_state.company_id = company_id
                        
                        # Показываем успешное сообщение
                        st.success(f"🎉 Компания '{name}' успешно создана и выбрана!")
                        
                        # Обновляем страницу
                        st.rerun()
                    else:
                        st.error("❌ Ошибка: Не удалось создать компанию")
                        
                except Exception as e:
                    st.error(f"❌ Ошибка при создании компании: {str(e)}")
                    import traceback
                    st.error("Детали ошибки:")
                    st.code(traceback.format_exc())
                
    def render_welcome_screen(self):
        """Рендеринг welcome screen"""
        
        st.markdown("""
        ## 🚀 Добро пожаловать в SaaS Unit Economics Dashboard
        
        **Пожалуйста, выберите компанию в боковой панели слева или создайте новую.**
        
        После выбора компании вы получите доступ к:
        - 📊 Dashboard с ключевыми метриками
        - 📈 Финансовому планированию
        - 📊 Трекингу фактических данных
        - 🤖 AI аналитику и рекомендациям
        """)
        
        # Можно добавить изображение или демо-данные
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image("https://img.icons8.com/color/480/000000/business-analytics.png", width=300) 
        
    def render_main_content(self):
        """Рендеринг основного контента"""
        
        current_tab = st.session_state.current_tab

        tab_renderers = {
            "🏠 Dashboard": self.render_dashboard,
            "📈 Financial Planning": self.render_financial_planning,
            "📊 Actual Tracking": self.render_actual_tracking,
            "🔍 Variance Analysis": self.render_variance_analysis,
            "🎯 Scenario Simulation": self.render_scenario_simulation,
            "🤖 AI Analyst": self.render_ai_analyst,
            "📋 Reports": self.render_reports,
            "⚙️ Settings": self.render_settings,
        }

        renderer = tab_renderers.get(current_tab)
        if renderer:
            self._render_with_error(renderer, current_tab)

    def _render_with_error(self, render_func, tab_name: str) -> None:
        """Безопасный рендер вкладки с перехватом ошибок."""
        try:
            render_func()
        except Exception as exc:
            logger.exception("Ошибка при рендеринге вкладки %s: %s", tab_name, exc)
            st.error("Произошла ошибка при загрузке раздела.")
            st.info("Проверьте вводимые данные или попробуйте обновить страницу.")
    
    def render_dashboard(self):
        """Рендеринг dashboard"""
        
        company_id = st.session_state.company_id
        company = db_manager.get_company(company_id)
        
        if not company:
            st.error("Компания не найдена")
            return
        
        st.markdown(f'<h2 class="sub-header">🏠 Dashboard: {company.name}</h2>', unsafe_allow_html=True)
        
        # Вкладки dashboard
        dashboard_tabs = st.tabs(["📊 Обзор", "📈 Метрики", "🚨 Алerts", "🎯 Рекомендации"])
        
        with dashboard_tabs[0]:  # Обзор
            self.render_overview_tab(company)
        
        with dashboard_tabs[1]:  # Метрики
            self.render_metrics_tab(company)
        
        with dashboard_tabs[2]:  # Алerts
            self.render_alerts_tab(company)
        
        with dashboard_tabs[3]:  # Рекомендации
            self.render_recommendations_tab(company)
    
    def render_overview_tab(self, company):
        """Рендеринг вкладки обзора"""
        
        # db_manager уже импортирован как глобальный объект из app.py
        # Используем его напрямую без создания нового экземпляра
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Текущий MRR",
                value=f"${company.current_mrr:,.0f}",
                delta=f"${company.current_mrr * 0.1:,.0f}" if company.current_mrr > 0 else "$0"
            )
        
        with col2:
            st.metric(
                label="Клиенты",
                value=f"{company.current_customers:,}",
                delta="+10" if company.current_customers > 0 else "0"
            )
        
        with col3:
            try:
                # Получаем данные для расчета runway
                # Используем дефолтные значения если атрибуты не доступны
                cash_balance = getattr(company, 'cash_balance', company.current_mrr * 6)  # 6 месяцев MRR как cash по умолчанию
                monthly_burn_rate = getattr(company, 'monthly_burn_rate', company.current_mrr * 1.5)  # 1.5x MRR как burn rate
                monthly_revenue = company.current_mrr
                growth_rate = getattr(company, 'growth_rate_monthly', 0.1)  # 10% по умолчанию
                
                # Расчет runway
                runway_data = runway_calculator.calculate_runway(
                    cash_balance=cash_balance,
                    monthly_burn_rate=monthly_burn_rate,
                    monthly_revenue=monthly_revenue,
                    growth_rate=growth_rate,
                    include_scenarios=False  # Для быстрого расчета
                )
                
                # Получаем основной runway
                runway_months = runway_data['basic_runway']['runway_months']
                runway_category = runway_data['basic_runway']['runway_category']['label']
                
            except Exception as e:
                st.error(f"Ошибка расчета runway: {e}")
                # Расчет по умолчанию
                if hasattr(company, 'cash_balance') and company.current_mrr > 0:
                    burn_rate = company.current_mrr * 1.5
                    runway_months = company.cash_balance / burn_rate if burn_rate > 0 else 12
                else:
                    runway_months = 12  # Значение по умолчанию
                runway_category = "Estimated"
            
            st.metric(
                label="Runway",
                value=f"{runway_months:.1f} мес.",
                delta="-0.5 мес." if runway_months > 0 else "0 мес."
            )
            st.caption(runway_category)
        
        with col4:
            # Расчет burn rate
            try:
                # Используем те же значения что для runway
                monthly_burn_rate = getattr(company, 'monthly_burn_rate', company.current_mrr * 1.5)
                cash_balance = getattr(company, 'cash_balance', company.current_mrr * 6)
                
            except Exception as e:
                st.error(f"Ошибка получения данных: {e}")
                monthly_burn_rate = company.current_mrr * 1.5
                cash_balance = company.current_mrr * 6
            
            st.metric(
                label="Cash Balance",
                value=f"${cash_balance:,.0f}",
                delta=f"-${monthly_burn_rate:,.0f}/мес." if monthly_burn_rate > 0 else "$0/мес."
            )
            st.caption(f"Burn Rate: ${monthly_burn_rate:,.0f}/мес.")
        
        st.markdown("---")
        
        # Детальный анализ runway при клике
        with st.expander("📊 Детальный анализ Runway"):
            try:
                # Полный расчет runway с сценариями
                cash_balance = getattr(company, 'cash_balance', company.current_mrr * 6)
                monthly_burn_rate = getattr(company, 'monthly_burn_rate', company.current_mrr * 1.5)
                monthly_revenue = company.current_mrr
                growth_rate = getattr(company, 'growth_rate_monthly', 0.1)
                
                full_runway_data = runway_calculator.calculate_runway(
                    cash_balance=cash_balance,
                    monthly_burn_rate=monthly_burn_rate,
                    monthly_revenue=monthly_revenue,
                    growth_rate=growth_rate,
                    include_scenarios=True
                )
                
                # Отображение категории
                category_info = full_runway_data['basic_runway']['runway_category']
                st.markdown(f"**Категория:** {category_info['label']}")
                st.info(category_info['description'])
                
                # Отображение сценариев
                st.subheader("📈 Анализ сценариев")
                for name, scenario in full_runway_data['scenarios'].items():
                    with st.expander(f"{scenario['name']} - {scenario['runway_months']:.1f} месяцев"):
                        st.write(f"**Описание:** {scenario['description']}")
                        st.write(f"**Runway:** {scenario['runway_months']:.1f} месяцев")
                        st.write(f"**Детали:** {scenario.get('assumptions', 'Нет данных')}")
                
                # Отображение визуализаций если есть
                if 'visualizations' in full_runway_data:
                    st.subheader("📊 Визуализации")
                    for viz_name, viz_fig in full_runway_data['visualizations'].items():
                        st.plotly_chart(viz_fig, use_container_width=True)
                
                # Рекомендации
                st.subheader("🎯 Рекомендации")
                for priority, actions in full_runway_data['recommendations'].items():
                    if actions:
                        st.markdown(f"**{priority.replace('_', ' ').title()}:**")
                        for action in actions:
                            st.markdown(f"- {action}")
                
            except Exception as e:
                st.error(f"Ошибка детального анализа runway: {e}")
        
        # Графики и визуализации
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### MRR Growth")
            # Получение данных для графика
            # Используем глобальный db_manager
            try:
                actuals = db_manager.get_actual_financials_by_filters({"company_id": company.id})
            except Exception as e:
                st.error(f"Ошибка получения данных: {e}")
                actuals = []
            
            if actuals:
                # Создание графика
                data = []
                for actual in actuals:
                    # Проверяем наличие атрибутов
                    month = f"{getattr(actual, 'year', 2024)}-{getattr(actual, 'month_number', 1):02d}"
                    mrr = getattr(actual, 'actual_mrr', 0)
                    
                    data.append({
                        "month": month,
                        "mrr": mrr
                    })
                
                if data:
                    df = pd.DataFrame(data)
                    if not df.empty:
                        fig = px.line(df, x="month", y="mrr", markers=True)
                        fig.update_layout(
                            xaxis_title="Month",
                            yaxis_title="MRR ($)",
                            height=300
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Нет данных для отображения графика MRR роста")
                else:
                    st.info("Нет данных для отображения графика MRR роста")
            else:
                st.info("Нет данных для отображения графика MRR роста")
        
        with col2:
            st.markdown("#### Burn Rate Analysis")
            # Используем monthly_burn_rate из расчета выше
            try:
                # Получаем данные снова для этого графика
                actuals = db_manager.get_actual_financials_by_filters({"company_id": company.id})
            except Exception as e:
                st.error(f"Ошибка получения данных: {e}")
                actuals = []
                
            if actuals:
                data = []
                for i, actual in enumerate(actuals):
                    month = f"{getattr(actual, 'year', 2024)}-{getattr(actual, 'month_number', 1):02d}"
                    burn_rate_val = getattr(actual, 'actual_burn_rate', monthly_burn_rate * (0.9 + i*0.1))  # Простая симуляция
                    revenue = getattr(actual, 'actual_total_revenue', company.current_mrr * (1 + i*0.05))  # Простая симуляция
                    
                    data.append({
                        "month": month,
                        "burn_rate": burn_rate_val,
                        "revenue": revenue
                    })
                
                if data:
                    df = pd.DataFrame(data)
                    if not df.empty:
                        fig = go.Figure()
                        
                        # Revenue bar
                        fig.add_trace(go.Bar(
                            x=df["month"],
                            y=df["revenue"],
                            name="Revenue",
                            marker_color="#27AE60"
                        ))
                        
                        # Burn rate line
                        fig.add_trace(go.Scatter(
                            x=df["month"],
                            y=df["burn_rate"],
                            name="Burn Rate",
                            line=dict(color="#E74C3C", width=3),
                            yaxis="y2"
                        ))
                        
                        fig.update_layout(
                            xaxis_title="Month",
                            yaxis_title="Revenue ($)",
                            yaxis2=dict(
                                title="Burn Rate ($)",
                                overlaying="y",
                                side="right"
                            ),
                            barmode="group",
                            height=300,
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="right",
                                x=1
                            )
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Нет данных для анализа burn rate")
                else:
                    st.info("Нет данных для анализа burn rate")
            else:
                # Создаем демо данные если нет актуальных
                months = [f"2024-{m:02d}" for m in range(1, 13)]
                demo_revenue = [company.current_mrr * (1 + i*0.1) for i in range(12)]
                demo_burn_rate = [monthly_burn_rate * (1 + i*0.05) for i in range(12)]
                
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=months,
                    y=demo_revenue,
                    name="Revenue (demo)",
                    marker_color="#27AE60"
                ))
                fig.add_trace(go.Scatter(
                    x=months,
                    y=demo_burn_rate,
                    name="Burn Rate (demo)",
                    line=dict(color="#E74C3C", width=3, dash='dash'),
                    yaxis="y2"
                ))
                
                fig.update_layout(
                    xaxis_title="Month",
                    yaxis_title="Revenue ($)",
                    yaxis2=dict(
                        title="Burn Rate ($)",
                        overlaying="y",
                        side="right"
                    ),
                    barmode="group",
                    height=300,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    ),
                    title="Demo Data (no actuals available)"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Ключевые метрики
        st.markdown("---")
        st.markdown("#### Ключевые SaaS метрики")
        
        # Расчет метрик
        metrics = {}
        try:
            # ИСПРАВЛЕНИЕ: используем метод calculate_company_metrics вместо calculate_metrics
            metrics = self._calculate_company_metrics(company)
        except Exception as e:
            st.error(f"Ошибка расчета метрик: {e}")
            # Используем значения по умолчанию
            metrics = {
                'ltv_cac_ratio': 2.5,
                'gross_margin': 0.75,
                'cac_payback_months': 10,
                'monthly_churn_rate': 0.04
            }
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            ltv_cac = metrics.get('ltv_cac_ratio', 0)
            st.metric(
                label="LTV/CAC Ratio",
                value=f"{ltv_cac:.1f}x",
                delta=None
            )
            st.caption("Цель: >3x")
        
        with col2:
            gross_margin = metrics.get('gross_margin', 0)
            st.metric(
                label="Gross Margin",
                value=f"{gross_margin * 100:.0f}%",
                delta=None
            )
            st.caption("Цель: >80%")
        
        with col3:
            cac_payback = metrics.get('cac_payback_months', 0)
            st.metric(
                label="CAC Payback",
                value=f"{cac_payback:.0f} мес.",
                delta=None
            )
            st.caption("Цель: <12 мес.")
        
        with col4:
            churn_rate = metrics.get('monthly_churn_rate', 0) * 100
            st.metric(
                label="Monthly Churn",
                value=f"{churn_rate:.1f}%",
                delta=None
            )
            st.caption("Цель: <5%")
    
    def _calculate_company_metrics(self, company):
        """Расчет метрик компании"""
        
        # Получаем фактические данные
        actuals = db_manager.get_actual_financials_by_filters({"company_id": company.id})
        
        if actuals:
            # Используем последние фактические данные
            latest_actual = max(actuals, key=lambda x: (x.year, x.month_number))
            
            metrics = {
                'mrr': getattr(latest_actual, 'actual_mrr', company.current_mrr),
                'arr': getattr(latest_actual, 'actual_mrr', company.current_mrr) * 12,
                'gross_margin': getattr(latest_actual, 'actual_gross_margin', 0.75),
                'burn_rate': getattr(latest_actual, 'actual_burn_rate', company.current_mrr * 1.5),
                'runway_months': getattr(latest_actual, 'actual_runway', 
                                         company.cash_balance / (company.current_mrr * 1.5) if company.current_mrr * 1.5 > 0 else 12),
                'ltv': getattr(latest_actual, 'actual_ltv', 5000),
                'cac': getattr(latest_actual, 'actual_cac', 1000),
                'monthly_growth_rate': 0.1,  # Предположение
                'monthly_churn_rate': 0.04,  # Предположение
            }
            
            # Расчет производных метрик
            if metrics['cac'] > 0:
                metrics['ltv_cac_ratio'] = metrics['ltv'] / metrics['cac']
                metrics['cac_payback_months'] = metrics['cac'] / (metrics['mrr'] * 0.3)  # Упрощенный расчет
            else:
                metrics['ltv_cac_ratio'] = 0
                metrics['cac_payback_months'] = 0
                
            # Magic number
            marketing_spend = getattr(latest_actual, 'actual_marketing_spend', metrics['cac'] * 10)
            if marketing_spend > 0:
                metrics['magic_number'] = (metrics['mrr'] * metrics['monthly_growth_rate']) / marketing_spend
            else:
                metrics['magic_number'] = 0
                
            return metrics
        else:
            # Если нет данных, используем данные компании
            return {
                'mrr': company.current_mrr,
                'arr': company.current_mrr * 12,
                'gross_margin': 0.75,
                'burn_rate': company.current_mrr * 1.5,
                'runway_months': company.cash_balance / (company.current_mrr * 1.5) if company.current_mrr * 1.5 > 0 else 12,
                'ltv_cac_ratio': 2.5,
                'cac_payback_months': 10,
                'monthly_churn_rate': 0.04,
                'monthly_growth_rate': 0.1,
                'cac': 1000,
                'ltv': 5000,
                'magic_number': 0.8
            }
    
    def render_metrics_tab(self, company):
        """Рендеринг вкладки метрик"""
        
        st.markdown("#### Детальный анализ метрик")
        
        # Вкладки для разных типов метрик
        metric_tabs = st.tabs(["📊 Финансовые", "👥 Клиентские", "⚙️ Операционные", "📈 Ростовые"])
        
        with metric_tabs[0]:  # Финансовые
            self.render_financial_metrics(company)
        
        with metric_tabs[1]:  # Клиентские
            self.render_customer_metrics(company)
        
        with metric_tabs[2]:  # Операционные
            self.render_operational_metrics(company)
        
        with metric_tabs[3]:  # Ростовые
            self.render_growth_metrics(company)
    
    def render_financial_metrics(self, company):
        """Рендеринг финансовых метрик"""
        
        # ИСПРАВЛЕНИЕ: используем наш метод расчета метрик вместо stage_aware_metrics.calculate_metrics
        metrics = self._calculate_company_metrics(company)
        
        if not metrics:
            st.info("Нет данных для расчета финансовых метрик")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### Основные финансовые метрики")
            
            financial_data = [
                ("Monthly Recurring Revenue", f"${metrics.get('mrr', 0):,.0f}", "green"),
                ("Annual Run Rate", f"${metrics.get('arr', 0):,.0f}", "blue"),
                ("Gross Margin", f"{metrics.get('gross_margin', 0)*100:.1f}%", 
                 "green" if metrics.get('gross_margin', 0) > 0.7 else "orange"),
                ("Burn Rate", f"${metrics.get('burn_rate', 0):,.0f}/мес.", 
                 "red" if metrics.get('burn_rate', 0) > 50000 else "orange"),
                ("Runway", f"{metrics.get('runway_months', 0):.1f} мес.", 
                 "green" if metrics.get('runway_months', 0) > 12 else 
                 "orange" if metrics.get('runway_months', 0) > 6 else "red")
            ]
            
            for label, value, color in financial_data:
                st.markdown(f"""
                <div class="metric-card">
                    <div style="color: {color}; font-weight: bold; font-size: 1.2rem;">{value}</div>
                    <div style="color: #666; font-size: 0.9rem;">{label}</div>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("##### Эффективность инвестиций")
            
            efficiency_data = [
                ("LTV", f"${metrics.get('ltv', 0):,.0f}", "blue"),
                ("CAC", f"${metrics.get('cac', 0):,.0f}", "orange"),
                ("LTV/CAC Ratio", f"{metrics.get('ltv_cac_ratio', 0):.1f}x", 
                 "green" if metrics.get('ltv_cac_ratio', 0) > 3 else 
                 "orange" if metrics.get('ltv_cac_ratio', 0) > 1 else "red"),
                ("CAC Payback", f"{metrics.get('cac_payback_months', 0):.0f} мес.", 
                 "green" if metrics.get('cac_payback_months', 0) < 12 else 
                 "orange" if metrics.get('cac_payback_months', 0) < 18 else "red"),
                ("Magic Number", f"{metrics.get('magic_number', 0):.2f}", 
                 "green" if metrics.get('magic_number', 0) > 0.75 else 
                 "orange" if metrics.get('magic_number', 0) > 0.5 else "red")
            ]
            
            for label, value, color in efficiency_data:
                st.markdown(f"""
                <div class="metric-card">
                    <div style="color: {color}; font-weight: bold; font-size: 1.2rem;">{value}</div>
                    <div style="color: #666; font-size: 0.9rem;">{label}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Benchmark сравнение
            st.markdown("##### Сравнение с Benchmark")
            
            try:
                benchmark_comparison = saas_benchmarks.compare_with_benchmarks(
                    metrics, company.stage
                )
                
                if benchmark_comparison:
                    score = benchmark_comparison.get("overall_score", 0)
                    performance = benchmark_comparison.get("overall_performance", "N/A")
                    
                    st.metric(
                        label="Benchmark Score",
                        value=f"{score}/100",
                        delta=None
                    )
                    st.caption(f"Performance: {performance}")
            except Exception as e:
                st.info("Benchmark сравнение временно недоступно")
    
    def render_customer_metrics(self, company):
        """Рендеринг клиентских метрик"""
        
        # Получение данных о клиентах
        actuals = db_manager.get_actual_financials_by_filters({"company_id": company.id})
        
        if not actuals:
            st.info("Нет данных о клиентах")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### Демография клиентов")
            
            # Расчет метрик
            total_customers = company.current_customers
            avg_customers = np.mean([a.actual_total_customers for a in actuals if a.actual_total_customers])
            
            customer_data = [
                ("Всего клиентов", f"{total_customers:,}", "blue"),
                ("Среднее за период", f"{avg_customers:,.0f}", "green"),
                ("Новых в месяц", "+15", "green"),  # Пример
                ("Отток в месяц", "-3", "red"),  # Пример
                ("Net New", "+12", "green")  # Пример
            ]
            
            for label, value, color in customer_data:
                st.markdown(f"""
                <div class="metric-card">
                    <div style="color: {color}; font-weight: bold; font-size: 1.2rem;">{value}</div>
                    <div style="color: #666; font-size: 0.9rem;">{label}</div>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("##### Удержание и удовлетворенность")
            
            retention_data = [
                ("Monthly Churn", "2.5%", "green"),  # Пример
                ("Annual Churn", "26%", "orange"),  # Пример
                ("Net Revenue Retention", "110%", "green"),  # Пример
                ("Gross Revenue Retention", "92%", "orange"),  # Пример
                ("Customer Satisfaction", "4.5/5.0", "green")  # Пример
            ]
            
            for label, value, color in retention_data:
                st.markdown(f"""
                <div class="metric-card">
                    <div style="color: {color}; font-weight: bold; font-size: 1.2rem;">{value}</div>
                    <div style="color: #666; font-size: 0.9rem;">{label}</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Cohort analysis
        st.markdown("##### Cohort Analysis")
        
        try:
            cohort_results = cohort_analyzer.analyze_cohorts(company.id)
            
            if cohort_results and "cohort_data" in cohort_results:
                # Отображение cohort retention
                cohort_df = pd.DataFrame(cohort_results["cohort_data"])
                
                if not cohort_df.empty:
                    st.dataframe(
                        cohort_df.style.format({
                            'cohort_size': '{:,.0f}',
                            'retention_rate': '{:.1%}'
                        }),
                        use_container_width=True
                    )
        except Exception as e:
            st.info("Cohort analysis временно недоступна")
    
    def render_operational_metrics(self, company):
        """Рендеринг операционных метрик"""
        
        st.markdown("##### Эффективность команды")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="Размер команды",
                value=company.team_size,
                delta="+2"
            )
        
        with col2:
            st.metric(
                label="Revenue на сотрудника",
                value=f"${company.current_mrr / max(company.team_size, 1):,.0f}",
                delta="+$500"
            )
        
        with col3:
            st.metric(
                label="Burn на сотрудника",
                value=f"${50000 / max(company.team_size, 1):,.0f}",  # Пример
                delta="-$200"
            )
        
        st.markdown("---")
        st.markdown("##### Процессные метрики")
        
        process_data = [
            ("Среднее время закрытия сделки", "45 дней", "orange"),
            ("Среднее время ответа на поддержку", "2.5 часа", "green"),
            ("Скорость разработки", "15 задач/нед.", "green"),
            ("Качество кода", "98% без багов", "green"),
            ("Время до рынка", "3 недели", "orange")
        ]
        
        cols = st.columns(5)
        for idx, (label, value, color) in enumerate(process_data):
            with cols[idx]:
                st.markdown(f"""
                <div class="metric-card">
                    <div style="color: {color}; font-weight: bold; font-size: 1.1rem;">{value}</div>
                    <div style="color: #666; font-size: 0.8rem;">{label}</div>
                </div>
                """, unsafe_allow_html=True)
    
    def render_growth_metrics(self, company):
        """Рендеринг ростовых метрик"""
        
        st.markdown("##### Метрики роста")
        
        # Получение данных для расчета роста
        actuals = db_manager.get_actual_financials_by_filters({"company_id": company.id})
        
        if len(actuals) >= 2:
            # Расчет growth rate
            mrr_values = [a.actual_mrr for a in actuals]
            if mrr_values[0] > 0:
                monthly_growth = (mrr_values[-1] - mrr_values[0]) / mrr_values[0] / len(mrr_values)
            else:
                monthly_growth = 0
            
            annual_growth = ((1 + monthly_growth) ** 12 - 1) * 100
        else:
            monthly_growth = 0.1  # Пример
            annual_growth = 214  # Пример
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Monthly Growth Rate",
                value=f"{monthly_growth*100:.1f}%",
                delta=None
            )
        
        with col2:
            st.metric(
                label="Annual Growth Rate",
                value=f"{annual_growth:.0f}%",
                delta=None
            )
        
        with col3:
            st.metric(
                label="Rule of 40 Score",
                value="35",  # Пример
                delta="+5"
            )
        
        with col4:
            st.metric(
                label="Growth Efficiency Score",
                value="0.8",  # Пример
                delta="+0.1"
            )
        
        # Growth trajectory
        st.markdown("---")
        st.markdown("##### Growth Trajectory")
        
        if len(actuals) >= 3:
            # Создание графика роста
            growth_data = []
            for i in range(1, len(actuals)):
                if actuals[i-1].actual_mrr > 0:
                    growth = (actuals[i].actual_mrr - actuals[i-1].actual_mrr) / actuals[i-1].actual_mrr
                    growth_data.append({
                        "period": f"{actuals[i].year}-{actuals[i].month_number:02d}",
                        "growth_rate": growth * 100
                    })
            
            if growth_data:
                df = pd.DataFrame(growth_data)
                fig = px.bar(df, x="period", y="growth_rate")
                fig.update_layout(
                    xaxis_title="Period",
                    yaxis_title="Growth Rate (%)",
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)
    
    def render_alerts_tab(self, company):
        """Рендеринг вкладки алертов"""
        
        st.markdown("#### 🚨 Система алертов")
        
        alerts = self._generate_alerts(company)
        
        if not alerts:
            st.success("Нет критических алертов. Все системы работают нормально.")
            return
        
        # Группировка алертов по уровню
        critical_alerts = [a for a in alerts if a["level"] == "critical"]
        warning_alerts = [a for a in alerts if a["level"] == "warning"]
        info_alerts = [a for a in alerts if a["level"] == "info"]
        
        # Критические алерты
        if critical_alerts:
            st.markdown("##### 🔴 Критические алерты")
            for alert in critical_alerts:
                with st.expander(f"**{alert['title']}**", expanded=True):
                    st.markdown(f"**Описание:** {alert['message']}")
                    st.markdown(f"**Рекомендуемое действие:** {alert['action']}")
                    st.markdown(f"**Приоритет:** Высокий")
        
        # Предупреждения
        if warning_alerts:
            st.markdown("##### 🟡 Предупреждения")
            for alert in warning_alerts:
                with st.expander(f"**{alert['title']}**", expanded=False):
                    st.markdown(f"**Описание:** {alert['message']}")
                    st.markdown(f"**Рекомендуемое действие:** {alert['action']}")
                    st.markdown(f"**Приоритет:** Средний")
        
        # Информационные алерты
        if info_alerts:
            st.markdown("##### 🔵 Информационные уведомления")
            for alert in info_alerts:
                with st.expander(f"**{alert['title']}**", expanded=False):
                    st.markdown(f"**Описание:** {alert['message']}")
                    st.markdown(f"**Рекомендуемое действие:** {alert['action']}")
                    st.markdown(f"**Приоритет:** Низкий")
    
    def _generate_alerts(self, company):
        """Генерация алертов"""
        
        alerts = []
        
        # Проверка runway
        try:
            runway_data = runway_calculator.calculate_runway(
                cash_balance=getattr(company, 'cash_balance', company.current_mrr * 6),
                monthly_burn_rate=getattr(company, 'monthly_burn_rate', company.current_mrr * 1.5),
                monthly_revenue=company.current_mrr,
                growth_rate=getattr(company, 'growth_rate_monthly', 0.1),
                include_scenarios=False
            )
            
            if runway_data and 'basic_runway' in runway_data:
                runway = runway_data['basic_runway']['runway_months']
                
                if runway < 3:
                    alerts.append({
                        "level": "critical",
                        "title": "Критически низкий runway",
                        "message": f"Runway составляет всего {runway:.1f} месяцев. Необходимы срочные меры.",
                        "action": "Начать fundraising немедленно или сократить burn rate"
                    })
                elif runway < 6:
                    alerts.append({
                        "level": "warning",
                        "title": "Низкий runway",
                        "message": f"Runway составляет {runway:.1f} месяцев. Рекомендуется начать подготовку к fundraising.",
                        "action": "Начать подготовку к следующему раунду финансирования"
                    })
        except Exception as e:
            # Fallback расчет runway
            if hasattr(company, 'cash_balance') and company.current_mrr > 0:
                burn_rate = company.current_mrr * 1.5
                runway = company.cash_balance / burn_rate if burn_rate > 0 else 12
                
                if runway < 3:
                    alerts.append({
                        "level": "critical",
                        "title": "Критически низкий runway",
                        "message": f"Runway составляет всего {runway:.1f} месяцев. Необходимы срочные меры.",
                        "action": "Начать fundraising немедленно или сократить burn rate"
                    })
                elif runway < 6:
                    alerts.append({
                        "level": "warning",
                        "title": "Низкий runway",
                        "message": f"Runway составляет {runway:.1f} месяцев. Рекомендуется начать подготовку к fundraising.",
                        "action": "Начать подготовку к следующему раунду финансирования"
                    })
        
        # Проверка growth rate
        actuals = db_manager.get_actual_financials_by_filters({"company_id": company.id})
        
        if len(actuals) >= 2:
            mrr_values = [a.actual_mrr for a in actuals]
            if mrr_values[0] > 0:
                growth_rate = (mrr_values[-1] - mrr_values[0]) / mrr_values[0] / len(mrr_values)
                
                if growth_rate < 0.05:
                    alerts.append({
                        "level": "warning",
                        "title": "Низкий рост MRR",
                        "message": f"Monthly growth rate составляет {growth_rate*100:.1f}%. Ниже рекомендованного уровня для SaaS.",
                        "action": "Пересмотреть стратегию роста и customer acquisition"
                    })
        
        # Проверка cash balance
        if company.cash_balance < 100000:
            alerts.append({
                "level": "warning",
                "title": "Низкий cash balance",
                "message": f"Cash balance составляет ${company.cash_balance:,.0f}.",
                "action": "Рассмотреть варианты увеличения cash reserves"
            })
        
        # Добавляем информационные алерты
        alerts.append({
            "level": "info",
            "title": "Регулярный финансовый обзор",
            "message": "Рекомендуется провести ежемесячный финансовый обзор.",
            "action": "Запланировать meeting с финансовой командой"
        })
        
        return alerts
    
    def render_recommendations_tab(self, company):
        """Рендеринг вкладки рекомендаций"""
        
        st.markdown("#### 🎯 Рекомендации для улучшения")

        if not company:
            st.error("Компания не найдена. Добавьте данные компании, чтобы получить рекомендации.")
            return
        
        # Получение рекомендаций от AI
        with st.spinner("Генерация рекомендаций..."):
            try:
                recommendations = ai_recommendation_engine.generate_recommendations(
                    company_id=company.id,
                    context="dashboard",
                    report_type="general"
                )
                
                if recommendations and "recommendations" in recommendations:
                    ai_recommendations = recommendations["recommendations"]
                else:
                    ai_recommendations = []
            except Exception as e:
                st.warning(f"Не удалось получить AI рекомендации: {str(e)}")
                ai_recommendations = []
        
        # Рекомендации по стадии компании
        stage_recommendations = []
        stage_analysis = None

        if company.stage == "pre_seed":
            try:
                stage_analysis = pre_seed_advisor.analyze_company(company.id)
                stage_recommendations = self._normalize_recommendations(stage_analysis)
                if isinstance(stage_analysis, dict) and stage_analysis.get("notes"):
                    st.info(f"Детали анализа: {stage_analysis['notes']}")
            except Exception as e:
                st.error("Рекомендации по стадии временно недоступны из-за ошибки анализа.")
                st.info(f"Детали ошибки: {e}")
                stage_recommendations = []
        else:
            # Общие рекомендации для других стадий
            stage_recommendations = [
                {
                    "category": "Financial",
                    "priority": "high",
                    "recommendation": "Оптимизировать unit economics перед следующим раундом",
                    "rationale": "Инвесторы уделяют особое внимание LTV/CAC и payback period"
                },
                {
                    "category": "Growth",
                    "priority": "medium",
                    "recommendation": "Диверсифицировать каналы привлечения клиентов",
                    "rationale": "Снижение зависимости от одного канала снижает риски"
                }
            ]
        
        # Группировка рекомендаций
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### AI Рекомендации")
            
            if ai_recommendations:
                for rec in ai_recommendations[:3]:  # Показываем первые 3
                    with st.expander(f"**{rec.get('category', 'General')}** - {rec.get('priority', 'medium').title()}"):
                        st.markdown(f"**Рекомендация:** {rec.get('recommendation', '')}")
                        st.markdown(f"**Обоснование:** {rec.get('rationale', '')}")
                        st.markdown(f"**Ожидаемый эффект:** {rec.get('expected_impact', 'Medium')}")
            else:
                st.info("AI рекомендации временно недоступны")
        
        with col2:
            st.markdown("##### Рекомендации по стадии")
            
            if stage_recommendations:
                for rec in stage_recommendations[:3]:
                    with st.expander(f"**{rec.get('category', 'General')}** - {rec.get('priority', 'medium').title()}"):
                        st.markdown(f"**Рекомендация:** {rec.get('recommendation', '')}")
                        st.markdown(f"**Обоснование:** {rec.get('rationale', '')}")
            else:
                st.info("Нет специфических рекомендаций для текущей стадии")
        
        # Годовая roadmap
        st.markdown("---")
        st.markdown("##### Годовая Roadmap")
        
        try:
            roadmap = year_1_roadmap.generate_roadmap(company.id)
            
            if roadmap and "roadmap" in roadmap:
                roadmap_data = roadmap["roadmap"]
                
                # Отображение roadmap по кварталам
                quarters = ["Q1", "Q2", "Q3", "Q4"]
                
                for quarter in quarters:
                    if quarter in roadmap_data:
                        with st.expander(f"**{quarter}**", expanded=(quarter == "Q1")):
                            quarter_plan = roadmap_data[quarter]
                            
                            if "objectives" in quarter_plan:
                                st.markdown("**Ключевые цели:**")
                                for obj in quarter_plan["objectives"]:
                                    st.markdown(f"- {obj}")
                            
                            if "key_metrics" in quarter_plan:
                                st.markdown("**Ключевые метрики:**")
                                for metric, target in quarter_plan["key_metrics"].items():
                                    st.markdown(f"- {metric}: {target}")
        except Exception as e:
            st.info("Годовая roadmap временно недоступна")

    def _normalize_recommendations(self, raw_recommendations):
        """Нормализация рекомендаций к списку для безопасного отображения."""
        if raw_recommendations is None:
            return []
        if isinstance(raw_recommendations, dict):
            recommendations = raw_recommendations.get("recommendations", [])
            if isinstance(recommendations, list):
                return recommendations
            st.warning("Неверный формат рекомендаций по стадии: ожидался список.")
            return []
        if isinstance(raw_recommendations, list):
            return raw_recommendations
        st.warning("Неверный формат рекомендаций по стадии: ожидался список или словарь.")
        return []
    
    def render_financial_planning(self):
        """Рендеринг финансового планирования"""
        
        company_id = st.session_state.company_id
        company = db_manager.get_company(company_id)
        
        st.markdown(f'<h2 class="sub-header">📈 Financial Planning: {company.name}</h2>', unsafe_allow_html=True)
        
        # Вкладки финансового планирования
        planning_tabs = st.tabs(["🎯 Создать план", "📋 Мои планы", "📊 Анализ планов", "🔄 Обновить план"])
        
        with planning_tabs[0]:  # Создать план
            self.render_create_plan(company)
        
        with planning_tabs[1]:  # Мои планы
            self.render_my_plans(company)
        
        with planning_tabs[2]:  # Анализ планов
            self.render_plan_analysis(company)
        
        with planning_tabs[3]:  # Обновить план
            self.render_update_plan(company)
    
    def render_create_plan(self, company):
        """Рендеринг создания плана"""
        
        st.markdown("#### Создание нового финансового плана")
        
        with st.form("create_financial_plan"):
            col1, col2 = st.columns(2)
            
            with col1:
                plan_name = st.text_input("Название плана*", value=f"План {datetime.now().strftime('%Y-%m')}")
                plan_year = st.number_input("Год плана*", min_value=2023, max_value=2030, value=datetime.now().year)
                description = st.text_area("Описание плана", placeholder="Описание целей и предположений...")
            
            with col2:
                starting_mrr = st.number_input(
                    "Начальный MRR ($)*",
                    min_value=0.0,
                    value=float(company.current_mrr),
                    step=1000.0
                )
                starting_customers = st.number_input(
                    "Начальное количество клиентов*",
                    min_value=0,
                    value=company.current_customers,
                    step=10
                )
                starting_cash = st.number_input(
                    "Начальный cash balance ($)*",
                    min_value=0.0,
                    value=float(company.cash_balance),
                    step=10000.0
                )
            
            st.markdown("---")
            st.markdown("##### Предположения роста")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                monthly_growth_rate = st.slider(
                    "Месячный рост MRR (%)",
                    min_value=0.0,
                    max_value=50.0,
                    value=10.0,
                    step=1.0
                ) / 100
            
            with col2:
                monthly_churn_rate = st.slider(
                    "Месячный отток клиентов (%)",
                    min_value=0.0,
                    max_value=20.0,
                    value=3.0,
                    step=0.5
                ) / 100
            
            with col3:
                cac = st.number_input(
                    "CAC ($)",
                    min_value=0.0,
                    value=1000.0,
                    step=100.0
                )
            
            st.markdown("##### Структура затрат")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                salary_cost = st.number_input(
                    "Зарплаты ($/мес)",
                    min_value=0.0,
                    value=50000.0,
                    step=5000.0
                )
            
            with col2:
                marketing_cost = st.number_input(
                    "Маркетинг ($/мес)",
                    min_value=0.0,
                    value=20000.0,
                    step=2000.0
                )
            
            with col3:
                infrastructure_cost = st.number_input(
                    "Инфраструктура ($/мес)",
                    min_value=0.0,
                    value=5000.0,
                    step=500.0
                )
            
            with col4:
                other_cost = st.number_input(
                    "Прочие затраты ($/мес)",
                    min_value=0.0,
                    value=10000.0,
                    step=1000.0
                )
            
            submitted = st.form_submit_button("Создать 12-месячный план", type="primary", width='stretch')
            
            if submitted:
                # Создание плана
                try:
                    # Создание financial plan
                    financial_plan = FinancialPlan(
                        company_id=company.id,
                        plan_name=plan_name,
                        plan_year=plan_year,
                        description=description
                    )
                    
                    plan_id = db_manager.create_financial_plan(financial_plan)
                    
                    # Подготовка assumptions
                    assumptions = {
                        "growth": {
                            "monthly_growth_rate": monthly_growth_rate,
                            "monthly_churn_rate": monthly_churn_rate,
                            "starting_mrr": starting_mrr,
                            "starting_customers": starting_customers,
                            "starting_cash": starting_cash
                        },
                        "costs": {
                            "salary_cost": salary_cost,
                            "marketing_cost": marketing_cost,
                            "infrastructure_cost": infrastructure_cost,
                            "other_cost": other_cost,
                            "cac": cac
                        }
                    }
                    
                    # Генерация месячных планов
                    monthly_plans = financial_planner.generate_monthly_plans(
                        plan_id, assumptions
                    )
                    
                    # Сохранение месячных планов
                    for monthly_plan in monthly_plans:
                        if isinstance(monthly_plan, dict):
                            monthly_plan = MonthlyPlan(**monthly_plan)
                        db_manager.create_monthly_plan(monthly_plan)
                    
                    st.success(f"Финансовый план '{plan_name}' успешно создан!")
                    
                    # Показать summary
                    with st.expander("Показать summary плана", expanded=True):
                        self._display_plan_summary(plan_id, assumptions)
                    
                except Exception as e:
                    st.error(f"Ошибка при создании плана: {str(e)}")
    
    def _display_plan_summary(self, plan_id, assumptions):
        """Отображение summary плана"""
        
        monthly_plans = db_manager.get_monthly_plans(plan_id)
        
        if not monthly_plans:
            st.info("Нет данных плана для отображения")
            return
        
        # Создание DataFrame
        data = []
        for plan in monthly_plans:
            data.append({
                "Месяц": plan.month_name,
                "MRR": plan.plan_mrr,
                "Новые клиенты": plan.plan_new_customers,
                "Выручка": plan.plan_total_revenue,
                "Затраты": plan.plan_total_costs,
                "Прибыль": plan.plan_total_revenue - plan.plan_total_costs,
                "Runway": plan.plan_runway
            })
        
        df = pd.DataFrame(data)
        
        # Отображение таблицы
        st.dataframe(
            df.style.format({
                'MRR': '${:,.0f}',
                'Выручка': '${:,.0f}',
                'Затраты': '${:,.0f}',
                'Прибыль': '${:,.0f}',
                'Runway': '{:.1f} мес.'
            }),
            use_container_width=True
        )
        
        # Ключевые метрики
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            ending_mrr = monthly_plans[-1].plan_mrr
            starting_mrr = assumptions["growth"]["starting_mrr"]
            if starting_mrr > 0:
                annual_growth = (ending_mrr - starting_mrr) / starting_mrr * 100
            else:
                annual_growth = 0
            
            st.metric(
                label="Годовой рост MRR",
                value=f"{annual_growth:.0f}%",
                delta=None
            )
        
        with col2:
            total_revenue = sum(p.plan_total_revenue for p in monthly_plans)
            st.metric(
                label="Общая выручка за год",
                value=f"${total_revenue:,.0f}",
                delta=None
            )
        
        with col3:
            ending_cash = monthly_plans[-1].plan_cash_balance
            st.metric(
                label="Cash balance на конец года",
                value=f"${ending_cash:,.0f}",
                delta=None
            )
        
        with col4:
            min_runway = min(p.plan_runway for p in monthly_plans)
            st.metric(
                label="Минимальный runway",
                value=f"{min_runway:.1f} мес.",
                delta=None
            )
    
    def render_my_plans(self, company):
        """Рендеринг списка планов"""
        
        st.markdown("#### Мои финансовые планы")
        
        # Получение планов компании
        plans = db_manager.get_financial_plans(company.id)
        
        if not plans:
            st.info("У вас еще нет созданных планов. Создайте первый план во вкладке 'Создать план'.")
            return
        
        # Отображение планов
        for plan in plans:
            with st.expander(f"**{plan.plan_name}** - {plan.plan_year}", expanded=False):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.markdown(f"**Описание:** {plan.description or 'Нет описания'}")
                    st.markdown(f"**Создан:** {plan.created_at.strftime('%Y-%m-%d %H:%M')}")
                
                with col2:
                    # Кнопка просмотра
                    if st.button("👁️ Просмотреть", key=f"view_{plan.id}", width='stretch'):
                        self._display_plan_details(plan)
                
                with col3:
                    # Кнопка экспорта
                    if st.button("📤 Экспорт", key=f"export_{plan.id}", width='stretch'):
                        self._export_plan(plan)
                
                # Удаление плана
                if st.button("🗑️ Удалить", key=f"delete_{plan.id}", type="secondary", width='stretch'):
                    if st.button("✅ Подтвердить удаление", key=f"confirm_delete_{plan.id}"):
                        db_manager.delete_financial_plan(plan.id)
                        st.success("План удален")
                        st.rerun()
    
    def _display_plan_details(self, plan):
        """Отображение деталей плана"""
        
        st.markdown(f"##### Детали плана: {plan.plan_name}")
        
        # Получение месячных планов
        monthly_plans = db_manager.get_monthly_plans(plan.id)
        
        if not monthly_plans:
            st.info("Нет данных месячных планов")
            return
        
        # Вкладки для детального просмотра
        detail_tabs = st.tabs(["📋 Таблица", "📈 Графики", "📊 Анализ"])
        
        with detail_tabs[0]:  # Таблица
            self._display_plan_table(monthly_plans)
        
        with detail_tabs[1]:  # Графики
            self._display_plan_charts(monthly_plans)
        
        with detail_tabs[2]:  # Анализ
            self._display_plan_analysis(monthly_plans)
    
    def _display_plan_table(self, monthly_plans):
        """Отображение таблицы плана"""
        
        data = []
        for plan in monthly_plans:
            data.append({
                "Месяц": plan.month_name,
                "MRR": plan.plan_mrr,
                "Новые клиенты": plan.plan_new_customers,
                "Отток клиентов": plan.plan_churned_customers,
                "Всего клиентов": plan.plan_total_customers,
                "Выручка": plan.plan_total_revenue,
                "Затраты": plan.plan_total_costs,
                "Прибыль": plan.plan_total_revenue - plan.plan_total_costs,
                "Burn Rate": plan.plan_burn_rate,
                "Cash Balance": plan.plan_cash_balance,
                "Runway": plan.plan_runway
            })
        
        df = pd.DataFrame(data)
        
        st.dataframe(
            df.style.format({
                'MRR': '${:,.0f}',
                'Выручка': '${:,.0f}',
                'Затраты': '${:,.0f}',
                'Прибыль': '${:,.0f}',
                'Burn Rate': '${:,.0f}',
                'Cash Balance': '${:,.0f}',
                'Runway': '{:.1f}'
            }),
            use_container_width=True,
            height=400
        )
    
    def _display_plan_charts(self, monthly_plans):
        """Отображение графиков плана"""
        
        col1, col2 = st.columns(2)
        
        with col1:
            # График MRR роста
            mrr_data = []
            for plan in monthly_plans:
                mrr_data.append({
                    "Месяц": plan.month_name,
                    "MRR": plan.plan_mrr
                })
            
            if mrr_data:
                df = pd.DataFrame(mrr_data)
                fig = px.line(df, x="Месяц", y="MRR", markers=True)
                fig.update_layout(
                    title="Прогноз роста MRR",
                    xaxis_title="Месяц",
                    yaxis_title="MRR ($)",
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # График cash flow
            cash_data = []
            for plan in monthly_plans:
                cash_data.append({
                    "Месяц": plan.month_name,
                    "Cash Balance": plan.plan_cash_balance,
                    "Выручка": plan.plan_total_revenue,
                    "Затраты": plan.plan_total_costs
                })
            
            if cash_data:
                df = pd.DataFrame(cash_data)
                fig = go.Figure()
                
                # Cash balance line
                fig.add_trace(go.Scatter(
                    x=df["Месяц"],
                    y=df["Cash Balance"],
                    name="Cash Balance",
                    line=dict(color="#2E86C1", width=3)
                ))
                
                fig.update_layout(
                    title="Прогноз Cash Balance",
                    xaxis_title="Месяц",
                    yaxis_title="Cash Balance ($)",
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)
    
    def _display_plan_analysis(self, monthly_plans):
        """Отображение анализа плана"""
        
        # Расчет ключевых метрик
        starting_mrr = monthly_plans[0].plan_mrr
        ending_mrr = monthly_plans[-1].plan_mrr
        total_revenue = sum(p.plan_total_revenue for p in monthly_plans)
        total_costs = sum(p.plan_total_costs for p in monthly_plans)
        min_runway = min(p.plan_runway for p in monthly_plans)
        ending_cash = monthly_plans[-1].plan_cash_balance
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### Финансовые итоги")
            
            financial_summary = [
                ("Начальный MRR", f"${starting_mrr:,.0f}"),
                ("Конечный MRR", f"${ending_mrr:,.0f}"),
                ("Общая выручка", f"${total_revenue:,.0f}"),
                ("Общие затраты", f"${total_costs:,.0f}"),
                ("Общая прибыль", f"${total_revenue - total_costs:,.0f}"),
                ("Конечный cash", f"${ending_cash:,.0f}")
            ]
            
            for label, value in financial_summary:
                st.markdown(f"**{label}:** {value}")
        
        with col2:
            st.markdown("##### Ключевые индикаторы")
            
            if starting_mrr > 0:
                annual_growth = (ending_mrr - starting_mrr) / starting_mrr * 100
            else:
                annual_growth = 0
            
            indicators = [
                ("Годовой рост MRR", f"{annual_growth:.0f}%"),
                ("Минимальный runway", f"{min_runway:.1f} мес."),
                ("Месяц безубыточности", self._find_breakeven_month(monthly_plans)),
                ("Максимальный burn rate", f"${max(p.plan_burn_rate for p in monthly_plans):,.0f}/мес."),
                ("Средний CAC", f"${np.mean([p.plan_cac for p in monthly_plans]):,.0f}"),
                ("Средний LTV/CAC", f"{np.mean([p.plan_ltv_cac_ratio for p in monthly_plans]):.1f}x")
            ]
            
            for label, value in indicators:
                st.markdown(f"**{label}:** {value}")
    
    def _find_breakeven_month(self, monthly_plans):
        """Нахождение месяца безубыточности"""
        
        for plan in monthly_plans:
            if plan.plan_total_revenue >= plan.plan_total_costs:
                return plan.month_name
        
        return "Не достигнута"
    
    def _export_plan(self, plan):
        """Экспорт плана"""
        
        try:
            # Получение данных плана
            monthly_plans = db_manager.get_monthly_plans(plan.id)
            
            if not monthly_plans:
                st.warning("Нет данных для экспорта")
                return
            
            # Подготовка данных
            plan_data = {
                "plan_name": plan.plan_name,
                "plan_year": plan.plan_year,
                "description": plan.description,
                "created_at": plan.created_at.isoformat(),
                "monthly_plans": [p.to_dict() for p in monthly_plans]
            }
            
            # Опции экспорта
            export_format = st.selectbox(
                "Формат экспорта",
                ["Excel", "PDF", "CSV"],
                key=f"export_format_{plan.id}"
            )
            
            if st.button("Скачать", key=f"download_{plan.id}"):
                with st.spinner("Подготовка файла..."):
                    filename = f"{plan.plan_name.replace(' ', '_')}_{plan.plan_year}.{export_format.lower()}"
                    
                    if export_format == "Excel":
                        export_financial_plan(plan_data, "excel", filename)
                    elif export_format == "PDF":
                        export_financial_plan(plan_data, "pdf", filename)
                    elif export_format == "CSV":
                        export_financial_plan(plan_data, "csv", filename)
                    
                    # Чтение файла и предоставление для скачивания
                    with open(filename, "rb") as f:
                        data = f.read()
                    
                    st.download_button(
                        label="Скачать файл",
                        data=data,
                        file_name=filename,
                        mime="application/octet-stream"
                    )
                    
                    # Удаление временного файла
                    import os
                    os.remove(filename)
        
        except Exception as e:
            st.error(f"Ошибка при экспорте: {str(e)}")
    
    def render_plan_analysis(self, company):
        """Рендеринг анализа планов"""
        
        st.markdown("#### Сравнение и анализ планов")
        
        # Получение планов компании
        plans = db_manager.get_financial_plans(company.id)
        
        if len(plans) < 2:
            st.info("Для сравнения нужно как минимум 2 плана")
            return
        
        # Выбор планов для сравнения
        st.markdown("##### Выберите планы для сравнения")
        
        plan_options = {f"{p.plan_name} ({p.plan_year})": p.id for p in plans}
        
        col1, col2 = st.columns(2)
        
        with col1:
            selected_plan1 = st.selectbox(
                "План 1",
                list(plan_options.keys()),
                key="plan_comparison_1"
            )
            plan1_id = plan_options[selected_plan1]
        
        with col2:
            selected_plan2 = st.selectbox(
                "План 2",
                list(plan_options.keys()),
                index=1 if len(plan_options) > 1 else 0,
                key="plan_comparison_2"
            )
            plan2_id = plan_options[selected_plan2]
        
        if plan1_id == plan2_id:
            st.warning("Выберите разные планы для сравнения")
            return
        
        # Сравнение планов
        if st.button("Сравнить планы", type="primary"):
            self._compare_plans(plan1_id, plan2_id)
    
    def _compare_plans(self, plan1_id, plan2_id):
        """Сравнение двух планов"""
        
        # Получение данных планов
        monthly_plans1 = db_manager.get_monthly_plans(plan1_id)
        monthly_plans2 = db_manager.get_monthly_plans(plan2_id)
        
        if not monthly_plans1 or not monthly_plans2:
            st.error("Один из планов не содержит данных")
            return
        
        # Создание сравнения
        comparison_data = []
        
        for i in range(min(len(monthly_plans1), len(monthly_plans2))):
            p1 = monthly_plans1[i]
            p2 = monthly_plans2[i]
            
            comparison_data.append({
                "Месяц": p1.month_name,
                "MRR План 1": p1.plan_mrr,
                "MRR План 2": p2.plan_mrr,
                "Разница MRR": p2.plan_mrr - p1.plan_mrr,
                "Выручка План 1": p1.plan_total_revenue,
                "Выручка План 2": p2.plan_total_revenue,
                "Разница выручки": p2.plan_total_revenue - p1.plan_total_revenue
            })
        
        df = pd.DataFrame(comparison_data)
        
        # Отображение сравнения
        st.markdown("##### Таблица сравнения")
        st.dataframe(
            df.style.format({
                'MRR План 1': '${:,.0f}',
                'MRR План 2': '${:,.0f}',
                'Разница MRR': '${:,.0f}',
                'Выручка План 1': '${:,.0f}',
                'Выручка План 2': '${:,.0f}',
                'Разница выручки': '${:,.0f}'
            }),
            use_container_width=True
        )
        
        # График сравнения
        st.markdown("##### График сравнения MRR")
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df["Месяц"],
            y=df["MRR План 1"],
            name="План 1",
            line=dict(color="#2E86C1", width=3)
        ))
        
        fig.add_trace(go.Scatter(
            x=df["Месяц"],
            y=df["MRR План 2"],
            name="План 2",
            line=dict(color="#E74C3C", width=3)
        ))
        
        fig.update_layout(
            xaxis_title="Месяц",
            yaxis_title="MRR ($)",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Суммарное сравнение
        st.markdown("##### Суммарное сравнение")
        
        total_revenue1 = sum(p.plan_total_revenue for p in monthly_plans1)
        total_revenue2 = sum(p.plan_total_revenue for p in monthly_plans2)
        ending_mrr1 = monthly_plans1[-1].plan_mrr
        ending_mrr2 = monthly_plans2[-1].plan_mrr
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Разница в выручке",
                value=f"${total_revenue2 - total_revenue1:,.0f}",
                delta=None
            )
        
        with col2:
            st.metric(
                label="Разница в конечном MRR",
                value=f"${ending_mrr2 - ending_mrr1:,.0f}",
                delta=None
            )
        
        with col3:
            percent_diff = ((ending_mrr2 - ending_mrr1) / ending_mrr1 * 100) if ending_mrr1 > 0 else 0
            st.metric(
                label="Разница в %",
                value=f"{percent_diff:.1f}%",
                delta=None
            )
        
        with col4:
            better_plan = "План 2" if ending_mrr2 > ending_mrr1 else "План 1" if ending_mrr1 > ending_mrr2 else "Одинаковы"
            st.metric(
                label="Более агрессивный план",
                value=better_plan,
                delta=None
            )
    
    def render_update_plan(self, company):
        """Рендеринг обновления плана"""
        
        st.markdown("#### Обновление существующего плана")
        
        # Получение планов компании
        plans = db_manager.get_financial_plans(company.id)
        
        if not plans:
            st.info("Нет планов для обновления")
            return
        
        # Выбор плана для обновления
        selected_plan = st.selectbox(
            "Выберите план для обновления",
            [f"{p.plan_name} ({p.plan_year})" for p in plans],
            key="plan_update_select"
        )
        
        # Находим выбранный план
        plan_to_update = None
        for p in plans:
            if f"{p.plan_name} ({p.plan_year})" == selected_plan:
                plan_to_update = p
                break
        
        if not plan_to_update:
            st.error("План не найден")
            return
        
        st.markdown(f"##### Обновление плана: {plan_to_update.plan_name}")
        
        # Форма обновления
        with st.form("update_plan_form"):
            new_description = st.text_area(
                "Новое описание",
                value=plan_to_update.description or "",
                placeholder="Обновленное описание плана..."
            )
            
            st.markdown("**Примечание:** Для изменения финансовых предположений создайте новый план.")
            
            submitted = st.form_submit_button("Обновить описание плана", type="primary", width='stretch')
            
            if submitted:
                try:
                    # Обновление плана
                    plan_to_update.description = new_description
                    db_manager.update_financial_plan(plan_to_update)
                    
                    st.success("План успешно обновлен!")
                except Exception as e:
                    st.error(f"Ошибка при обновлении: {str(e)}")
    
    def render_actual_tracking(self):
        """Рендеринг трекинга фактических данных"""
        
        company_id = st.session_state.company_id
        company = db_manager.get_company(company_id)
        
        st.markdown(f'<h2 class="sub-header">📊 Actual Tracking: {company.name}</h2>', unsafe_allow_html=True)
        
        # Вкладки actual tracking
        tracking_tabs = st.tabs(["➕ Ввести данные", "📋 История", "📊 Анализ", "🔄 Обновить данные"])
        
        with tracking_tabs[0]:  # Ввести данные
            self.render_enter_actual_data(company)
        
        with tracking_tabs[1]:  # История
            self.render_actual_history(company)
        
        with tracking_tabs[2]:  # Анализ
            self.render_actual_analysis(company)
        
        with tracking_tabs[3]:  # Обновить данные
            self.render_update_actual_data(company)
    
    def render_enter_actual_data(self, company):
        """Рендеринг ввода фактических данных"""
        
        st.markdown("#### Ввод фактических данных за месяц")
        
        with st.form("enter_actual_data"):
            col1, col2 = st.columns(2)
            
            with col1:
                year = st.number_input(
                    "Год*",
                    min_value=2020,
                    max_value=2030,
                    value=datetime.now().year,
                    step=1
                )
                
                month = st.selectbox(
                    "Месяц*",
                    list(range(1, 13)),
                    format_func=lambda x: datetime(2000, x, 1).strftime("%B"),
                    index=datetime.now().month - 1
                )
                
                actual_mrr = st.number_input(
                    "Фактический MRR ($)*",
                    min_value=0.0,
                    value=float(company.current_mrr),
                    step=1000.0
                )
                
                actual_new_customers = st.number_input(
                    "Новые клиенты*",
                    min_value=0,
                    value=10,
                    step=1
                )
            
            with col2:
                actual_churned_customers = st.number_input(
                    "Отток клиентов",
                    min_value=0,
                    value=3,
                    step=1
                )
                
                actual_total_revenue = st.number_input(
                    "Общая выручка ($)*",
                    min_value=0.0,
                    value=float(company.current_mrr * 1.1),  # Пример
                    step=1000.0
                )
                
                actual_total_costs = st.number_input(
                    "Общие затраты ($)*",
                    min_value=0.0,
                    value=float(company.current_mrr * 0.8),  # Пример
                    step=1000.0
                )
                
                actual_cash_balance = st.number_input(
                    "Cash balance на конец месяца ($)",
                    min_value=0.0,
                    value=float(company.cash_balance * 0.95),  # Пример
                    step=10000.0
                )
            
            # Дополнительные поля
            st.markdown("##### Дополнительные метрики")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                actual_cac = st.number_input(
                    "CAC ($)",
                    min_value=0.0,
                    value=1000.0,
                    step=100.0
                )
            
            with col2:
                actual_ltv = st.number_input(
                    "LTV ($)",
                    min_value=0.0,
                    value=5000.0,
                    step=500.0
                )
            
            with col3:
                actual_gross_margin = st.slider(
                    "Gross Margin (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=80.0,
                    step=1.0
                ) / 100
            
            notes = st.text_area("Примечания", placeholder="Комментарии к данным за месяц...")
            
            submitted = st.form_submit_button("Сохранить фактические данные", type="primary", width='stretch')
            
            if submitted:
                # Расчет derived metrics
                burn_rate = max(0, actual_total_costs - actual_total_revenue)
                
                if burn_rate > 0:
                    runway = actual_cash_balance / burn_rate
                else:
                    runway = float('inf')  # Бесконечный runway если прибыль
                
                ltv_cac_ratio = actual_ltv / actual_cac if actual_cac > 0 else 0
                
                try:
                    # Создание actual financial record
                    actual_financial = ActualData(
                        company_id=company.id,
                        year=year,
                        month_number=month,
                        actual_mrr=actual_mrr,
                        actual_new_customers=actual_new_customers,
                        actual_churned_customers=actual_churned_customers,
                        actual_total_customers=company.current_customers + actual_new_customers - actual_churned_customers,
                        actual_total_revenue=actual_total_revenue,
                        actual_total_costs=actual_total_costs,
                        actual_burn_rate=burn_rate,
                        actual_runway=runway,
                        actual_cash_balance=actual_cash_balance,
                        actual_cac=actual_cac,
                        actual_ltv=actual_ltv,
                        actual_ltv_cac_ratio=ltv_cac_ratio,
                        actual_gross_margin=actual_gross_margin,
                        notes=notes
                    )
                    
                    # Сохранение в БД
                    actual_id = db_manager.create_actual_financial(actual_financial)
                    
                    # Обновление company metrics
                    company.current_mrr = actual_mrr
                    company.current_customers = actual_financial.actual_total_customers
                    company.cash_balance = actual_cash_balance
                    db_manager.update_company(company)
                    
                    st.success(f"Данные за {datetime(year, month, 1).strftime('%B %Y')} успешно сохранены!")
                    
                except Exception as e:
                    st.error(f"Ошибка при сохранении данных: {str(e)}")
    
    def render_actual_history(self, company):
        """Рендеринг истории фактических данных"""
        
        st.markdown("#### История фактических данных")
        
        # Получение фактических данных
        actuals = db_manager.get_actual_financials_by_filters({"company_id": company.id})
        
        if not actuals:
            st.info("Нет сохраненных фактических данных")
            return
        
        # Сортировка по дате
        actuals.sort(key=lambda x: (x.year, x.month_number), reverse=True)
        
        # Отображение в таблице
        data = []
        for actual in actuals:
            data.append({
                "Период": f"{actual.year}-{actual.month_number:02d}",
                "MRR": actual.actual_mrr,
                "Новые клиенты": actual.actual_new_customers,
                "Отток": actual.actual_churned_customers,
                "Всего клиентов": actual.actual_total_customers,
                "Выручка": actual.actual_total_revenue,
                "Затраты": actual.actual_total_costs,
                "Прибыль": actual.actual_total_revenue - actual.actual_total_costs,
                "Burn Rate": actual.actual_burn_rate,
                "Runway": actual.actual_runway,
                "Cash Balance": actual.actual_cash_balance
            })
        
        df = pd.DataFrame(data)
        
        st.dataframe(
            df.style.format({
                'MRR': '${:,.0f}',
                'Выручка': '${:,.0f}',
                'Затраты': '${:,.0f}',
                'Прибыль': '${:,.0f}',
                'Burn Rate': '${:,.0f}',
                'Cash Balance': '${:,.0f}',
                'Runway': '{:.1f}'
            }),
            use_container_width=True,
            height=400
        )
        
        # Опции экспорта
        st.markdown("##### Экспорт данных")
        
        col1, col2 = st.columns(2)
        
        with col1:
            export_format = st.selectbox(
                "Формат экспорта",
                ["Excel", "CSV", "JSON"],
                key="actual_export_format"
            )
        
        with col2:
            if st.button("Экспортировать историю", use_container_width=True):
                with st.spinner("Подготовка файла..."):
                    filename = f"actual_history_{company.name.replace(' ', '_')}.{export_format.lower()}"
                    
                    if export_format == "Excel":
                        export_dataframe_to_file(df, "excel", filename)
                    elif export_format == "CSV":
                        export_dataframe_to_file(df, "csv", filename)
                    elif export_format == "JSON":
                        export_dataframe_to_file(df, "json", filename)
                    
                    # Чтение файла для скачивания
                    with open(filename, "rb") as f:
                        data = f.read()
                    
                    st.download_button(
                        label="Скачать файл",
                        data=data,
                        file_name=filename,
                        mime="application/octet-stream"
                    )
                    
                    # Удаление временного файла
                    import os
                    os.remove(filename)
    
    def render_actual_analysis(self, company):
        """Рендеринг анализа фактических данных"""
        
        st.markdown("#### Анализ фактических данных")
        
        # Получение фактических данных
        actuals = db_manager.get_actual_financials_by_filters({"company_id": company.id})
        
        if len(actuals) < 2:
            st.info("Нужно как минимум 2 месяца данных для анализа")
            return
        
        # Вкладки анализа
        analysis_tabs = st.tabs(["📈 Тренды", "📊 Сравнение", "🎯 Benchmark"])
        
        with analysis_tabs[0]:  # Тренды
            self.render_trends_analysis(actuals)
        
        with analysis_tabs[1]:  # Сравнение
            self.render_comparison_analysis(actuals)
        
        with analysis_tabs[2]:  # Benchmark
            self.render_benchmark_analysis(company, actuals)
    
    def render_trends_analysis(self, actuals):
        """Рендеринг анализа трендов"""
        
        # Сортировка по дате
        actuals.sort(key=lambda x: (x.year, x.month_number))
        
        # Подготовка данных для графиков
        periods = []
        mrr_values = []
        burn_values = []
        runway_values = []
        
        for actual in actuals:
            period = f"{actual.year}-{actual.month_number:02d}"
            periods.append(period)
            mrr_values.append(actual.actual_mrr)
            burn_values.append(actual.actual_burn_rate)
            runway_values.append(actual.actual_runway)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # График MRR тренда
            fig = px.line(x=periods, y=mrr_values, markers=True)
            fig.update_layout(
                title="Тренд MRR",
                xaxis_title="Период",
                yaxis_title="MRR ($)",
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # График runway тренда
            fig = px.line(x=periods, y=runway_values, markers=True)
            fig.update_layout(
                title="Тренд Runway",
                xaxis_title="Период",
                yaxis_title="Runway (месяцы)",
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Статистика роста
        st.markdown("##### Статистика роста")
        
        if len(mrr_values) >= 2:
            monthly_growth_rates = []
            for i in range(1, len(mrr_values)):
                if mrr_values[i-1] > 0:
                    growth = (mrr_values[i] - mrr_values[i-1]) / mrr_values[i-1]
                    monthly_growth_rates.append(growth)
            
            if monthly_growth_rates:
                avg_growth = np.mean(monthly_growth_rates) * 100
                min_growth = np.min(monthly_growth_rates) * 100
                max_growth = np.max(monthly_growth_rates) * 100
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        label="Средний месячный рост",
                        value=f"{avg_growth:.1f}%",
                        delta=None
                    )
                
                with col2:
                    st.metric(
                        label="Минимальный рост",
                        value=f"{min_growth:.1f}%",
                        delta=None
                    )
                
                with col3:
                    st.metric(
                        label="Максимальный рост",
                        value=f"{max_growth:.1f}%",
                        delta=None
                    )
    
    def render_comparison_analysis(self, actuals):
        """Рендеринг comparative анализа"""
        
        st.markdown("##### Сравнение периодов")
        
        # Выбор периодов для сравнения
        actuals.sort(key=lambda x: (x.year, x.month_number), reverse=True)
        
        period_options = [f"{a.year}-{a.month_number:02d}" for a in actuals]
        
        col1, col2 = st.columns(2)
        
        with col1:
            selected_period1 = st.selectbox(
                "Период 1",
                period_options,
                key="period_comparison_1"
            )
        
        with col2:
            selected_period2 = st.selectbox(
                "Период 2",
                period_options,
                index=1 if len(period_options) > 1 else 0,
                key="period_comparison_2"
            )
        
        # Нахождение выбранных периодов
        actual1 = None
        actual2 = None
        
        for actual in actuals:
            period = f"{actual.year}-{actual.month_number:02d}"
            if period == selected_period1:
                actual1 = actual
            if period == selected_period2:
                actual2 = actual
        
        if actual1 and actual2:
            # Сравнение
            comparison_data = [
                ("MRR", actual1.actual_mrr, actual2.actual_mrr),
                ("Новые клиенты", actual1.actual_new_customers, actual2.actual_new_customers),
                ("Отток клиентов", actual1.actual_churned_customers, actual2.actual_churned_customers),
                ("Выручка", actual1.actual_total_revenue, actual2.actual_total_revenue),
                ("Затраты", actual1.actual_total_costs, actual2.actual_total_costs),
                ("Burn Rate", actual1.actual_burn_rate, actual2.actual_burn_rate),
                ("Runway", actual1.actual_runway, actual2.actual_runway)
            ]
            
            # Создание DataFrame
            comparison_df = pd.DataFrame(comparison_data, columns=["Метрика", "Период 1", "Период 2"])
            comparison_df["Изменение"] = comparison_df["Период 2"] - comparison_df["Период 1"]
            
            if actual1.actual_mrr > 0:
                comparison_df["Изменение %"] = (comparison_df["Изменение"] / actual1.actual_mrr) * 100
            else:
                comparison_df["Изменение %"] = 0
            
            st.dataframe(
                comparison_df.style.format({
                    'Период 1': '{:,.0f}',
                    'Период 2': '{:,.0f}',
                    'Изменение': '{:,.0f}',
                    'Изменение %': '{:.1f}%'
                }),
                use_container_width=True
            )
    
    def render_benchmark_analysis(self, company, actuals):
        """Рендеринг benchmark анализа"""
        
        st.markdown("##### Сравнение с SaaS Benchmark")
        
        # Расчет текущих метрик
        if actuals:
            latest_actual = max(actuals, key=lambda x: (x.year, x.month_number))
            
            current_metrics = {
                "mrr": latest_actual.actual_mrr,
                "monthly_growth_rate": 0.1,  # Пример
                "gross_margin": latest_actual.actual_gross_margin,
                "cac": latest_actual.actual_cac,
                "ltv": latest_actual.actual_ltv,
                "churn_rate": 0.03,  # Пример
                "burn_rate": latest_actual.actual_burn_rate
            }
            
            # Сравнение с benchmark
            benchmark_comparison = saas_benchmarks.compare_with_benchmarks(
                current_metrics, company.stage
            )
            
            if benchmark_comparison and "metrics_compared" in benchmark_comparison:
                # Отображение comparison
                comparison_data = []
                
                for metric_data in benchmark_comparison["metrics_compared"]:
                    comparison_data.append({
                        "Метрика": metric_data["metric"].replace("_", " ").title(),
                        "Наше значение": metric_data["company_value"],
                        "Benchmark Good": metric_data["benchmark_good"],
                        "Benchmark Great": metric_data["benchmark_excellent"],
                        "Уровень": metric_data["performance_level"],
                        "Счет": metric_data["score"]
                    })
                
                comparison_df = pd.DataFrame(comparison_data)
                
                st.dataframe(
                    comparison_df,
                    use_container_width=True
                )
                
                # Общий счет
                overall_score = benchmark_comparison.get("overall_score", 0)
                performance = benchmark_comparison.get("overall_performance", "N/A")
                
                st.metric(
                    label="Общий Benchmark Score",
                    value=f"{overall_score}/100",
                    delta=None
                )
                st.caption(f"Performance Level: {performance}")
            else:
                st.info("Нет данных benchmark сравнения")
        else:
            st.info("Нет фактических данных для benchmark анализа")
    
    def render_update_actual_data(self, company):
        """Рендеринг обновления фактических данных"""
        
        st.markdown("#### Обновление фактических данных")
        
        # Получение фактических данных
        actuals = db_manager.get_actual_financials_by_filters({"company_id": company.id})
        
        if not actuals:
            st.info("Нет данных для обновления")
            return
        
        # Выбор записи для обновления
        actuals.sort(key=lambda x: (x.year, x.month_number), reverse=True)
        
        actual_options = [f"{a.year}-{a.month_number:02d}: MRR ${a.actual_mrr:,.0f}" for a in actuals]
        
        selected_actual = st.selectbox(
            "Выберите запись для обновления",
            actual_options,
            key="update_actual_select"
        )
        
        # Находим выбранную запись
        actual_to_update = None
        for idx, option in enumerate(actual_options):
            if option == selected_actual:
                actual_to_update = actuals[idx]
                break
        
        if not actual_to_update:
            st.error("Запись не найдена")
            return
        
        st.markdown(f"##### Обновление данных за {actual_to_update.year}-{actual_to_update.month_number:02d}")
        
        # Форма обновления
        with st.form("update_actual_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                actual_mrr = st.number_input(
                    "Фактический MRR ($)*",
                    min_value=0.0,
                    value=float(actual_to_update.actual_mrr),
                    step=1000.0
                )
                
                actual_new_customers = st.number_input(
                    "Новые клиенты*",
                    min_value=0,
                    value=actual_to_update.actual_new_customers,
                    step=1
                )
                
                actual_total_revenue = st.number_input(
                    "Общая выручка ($)*",
                    min_value=0.0,
                    value=float(actual_to_update.actual_total_revenue),
                    step=1000.0
                )
            
            with col2:
                actual_churned_customers = st.number_input(
                    "Отток клиентов",
                    min_value=0,
                    value=actual_to_update.actual_churned_customers,
                    step=1
                )
                
                actual_total_costs = st.number_input(
                    "Общие затраты ($)*",
                    min_value=0.0,
                    value=float(actual_to_update.actual_total_costs),
                    step=1000.0
                )
                
                actual_cash_balance = st.number_input(
                    "Cash balance ($)",
                    min_value=0.0,
                    value=float(actual_to_update.actual_cash_balance),
                    step=10000.0
                )
            
            notes = st.text_area(
                "Примечания",
                value=actual_to_update.notes or "",
                placeholder="Обновленные комментарии..."
            )
            
            submitted = st.form_submit_button("Обновить данные", type="primary", width='stretch')
            
            if submitted:
                # Расчет обновленных метрик
                burn_rate = max(0, actual_total_costs - actual_total_revenue)
                
                if burn_rate > 0:
                    runway = actual_cash_balance / burn_rate
                else:
                    runway = float('inf')
                
                try:
                    # Обновление записи
                    actual_to_update.actual_mrr = actual_mrr
                    actual_to_update.actual_new_customers = actual_new_customers
                    actual_to_update.actual_churned_customers = actual_churned_customers
                    actual_to_update.actual_total_customers = actual_to_update.actual_total_customers + (actual_new_customers - actual_to_update.actual_new_customers) - (actual_churned_customers - actual_to_update.actual_churned_customers)
                    actual_to_update.actual_total_revenue = actual_total_revenue
                    actual_to_update.actual_total_costs = actual_total_costs
                    actual_to_update.actual_burn_rate = burn_rate
                    actual_to_update.actual_runway = runway
                    actual_to_update.actual_cash_balance = actual_cash_balance
                    actual_to_update.notes = notes
                    
                    db_manager.update_actual_financial(actual_to_update)
                    
                    st.success("Данные успешно обновлены!")
                    
                except Exception as e:
                    st.error(f"Ошибка при обновлении: {str(e)}")
    
    def render_variance_analysis(self):
        """Рендеринг анализа отклонений"""
        
        company_id = st.session_state.company_id
        company = db_manager.get_company(company_id)

        if not company:
            st.error("Компания не найдена. Добавьте данные компании, чтобы открыть анализ отклонений.")
            return
        
        st.markdown(f'<h2 class="sub-header">🔍 Variance Analysis: {company.name}</h2>', unsafe_allow_html=True)
        
        # Вкладки variance analysis
        variance_tabs = st.tabs(["📊 Месячный анализ", "📈 Квартальный анализ", "📋 Детальный отчет", "🚨 Проблемные зоны"])
        
        with variance_tabs[0]:  # Месячный анализ
            self.render_monthly_variance(company)
        
        with variance_tabs[1]:  # Квартальный анализ
            self.render_quarterly_variance(company)
        
        with variance_tabs[2]:  # Детальный отчет
            self.render_detailed_variance_report(company)
        
        with variance_tabs[3]:  # Проблемные зоны
            self.render_problem_areas(company)
    
    def render_monthly_variance(self, company):
        """Рендеринг месячного анализа отклонений"""
        
        st.markdown("#### Месячный анализ отклонений: Факт vs План")
        
        # Выбор месяца для анализа
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        col1, col2 = st.columns(2)
        
        with col1:
            year = st.number_input(
                "Год",
                min_value=2020,
                max_value=2030,
                value=current_year,
                step=1,
                key="variance_year"
            )
        
        with col2:
            month = st.selectbox(
                "Месяц",
                list(range(1, 13)),
                format_func=lambda x: datetime(2000, x, 1).strftime("%B"),
                index=current_month - 1,
                key="variance_month"
            )
        
        if st.button("Анализировать отклонения", type="primary"):
            # Анализ отклонений
            try:
                variance_data = variance_analyzer.analyze_monthly_variance(
                    company.id, month, year
                )
            except Exception as exc:
                st.error(f"Ошибка анализа отклонений: {exc}")
                return

            if not isinstance(variance_data, dict):
                st.warning("Неверный формат данных анализа.")
                return

            if "error" in variance_data:
                st.warning(variance_data["error"])
                return

            if "variance_summary" in variance_data:
                self._display_variance_results(variance_data)
            else:
                st.info("Нет данных для анализа отклонений за выбранный период")
    
    def render_quarterly_variance(self, company):
        """Рендеринг квартального анализа отклонений"""
        
        st.markdown("#### Квартальный анализ отклонений")
        
        current_year = datetime.now().year
        current_quarter = (datetime.now().month - 1) // 3 + 1
        
        col1, col2 = st.columns(2)
        
        with col1:
            year = st.number_input(
                "Год",
                min_value=2020,
                max_value=2030,
                value=current_year,
                step=1,
                key="quarter_variance_year"
            )
        
        with col2:
            quarter = st.selectbox(
                "Квартал",
                [1, 2, 3, 4],
                format_func=lambda x: f"Q{x}",
                index=current_quarter - 1,
                key="quarter_variance"
            )
        
        if st.button("Анализировать квартальные отклонения", type="primary"):
            # Анализ отклонений
            try:
                variance_data = variance_analyzer.analyze_quarterly_variance(
                    company.id, quarter, year
                )
            except Exception as exc:
                st.error(f"Ошибка анализа отклонений: {exc}")
                return

            if not isinstance(variance_data, dict):
                st.warning("Неверный формат данных анализа.")
                return

            if "error" in variance_data:
                st.warning(variance_data["error"])
                return

            if "variance_summary" in variance_data:
                self._display_variance_results(variance_data)
            else:
                st.info("Нет данных для анализа квартальных отклонений")
    
    def _display_variance_results(self, variance_data):
        """Отображение результатов анализа отклонений"""
        
        variance_summary = variance_data.get("variance_summary", {})
        significant_variances = variance_data.get("significant_variances", [])
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Total Revenue Variance",
                value=f"${variance_summary.get('total_revenue_variance', 0):,.0f}",
                delta=f"{variance_summary.get('total_revenue_variance_percent', 0)*100:.1f}%"
            )
        
        with col2:
            st.metric(
                label="Total Cost Variance",
                value=f"${variance_summary.get('total_cost_variance', 0):,.0f}",
                delta=f"{variance_summary.get('total_cost_variance_percent', 0)*100:.1f}%"
            )
        
        with col3:
            st.metric(
                label="Overall Variance",
                value=f"${variance_summary.get('overall_variance', 0):,.0f}",
                delta=f"{variance_summary.get('overall_variance_percent', 0)*100:.1f}%"
            )
        
        with col4:
            variance_score = variance_summary.get('variance_score', 0)
            score_color = "green" if variance_score >= 80 else "yellow" if variance_score >= 60 else "red"
            st.markdown(f"""
            <div style="text-align: center;">
                <div style="font-size: 2rem; color: {score_color}; font-weight: bold;">{variance_score}/100</div>
                <div style="color: #666;">Variance Score</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Significant variances
        if significant_variances:
            st.markdown("##### 🚨 Значительные отклонения")
            
            for variance in significant_variances:
                category = variance.get("category", "")
                variance_percent = variance.get("variance_percent", 0) * 100
                
                if variance_percent > 20:
                    color = "green"
                    icon = "📈"
                    message = f"Значительно превышен план на {abs(variance_percent):.1f}%"
                elif variance_percent < -20:
                    color = "red"
                    icon = "📉"
                    message = f"Значительно отставание от плана на {abs(variance_percent):.1f}%"
                else:
                    continue
                
                with st.expander(f"{icon} {category}: {message}", expanded=True):
                    st.markdown(f"**План:** ${variance.get('plan_value', 0):,.0f}")
                    st.markdown(f"**Факт:** ${variance.get('actual_value', 0):,.0f}")
                    st.markdown(f"**Отклонение:** ${variance.get('variance_amount', 0):,.0f} ({variance_percent:.1f}%)")
                    st.markdown(f"**Причина:** {variance.get('reason', 'Не указана')}")
                    st.markdown(f"**Рекомендация:** {variance.get('recommendation', '')}")
        
        # Detailed variance table
        if "detailed_variance" in variance_data:
            st.markdown("##### Детальная таблица отклонений")
            
            detailed_data = []
            for item in variance_data["detailed_variance"]:
                detailed_data.append({
                    "Категория": item.get("category", ""),
                    "План": item.get("plan_value", 0),
                    "Факт": item.get("actual_value", 0),
                    "Отклонение": item.get("variance_amount", 0),
                    "Отклонение %": item.get("variance_percent", 0) * 100
                })
            
            df = pd.DataFrame(detailed_data)
            
            # Apply formatting
            def color_variance(val):
                if val > 20:
                    return 'color: green'
                elif val < -20:
                    return 'color: red'
                else:
                    return 'color: orange'
            
            styled_df = df.style.format({
                'План': '${:,.0f}',
                'Факт': '${:,.0f}',
                'Отклонение': '${:,.0f}',
                'Отклонение %': '{:.1f}%'
            }).applymap(color_variance, subset=['Отклонение %'])
            
            st.dataframe(styled_df, use_container_width=True)
    
    def render_detailed_variance_report(self, company):
        """Рендеринг детального отчета по отклонениям"""
        
        st.markdown("#### Детальный отчет по отклонениям")
        
        # Выбор периода для отчета
        col1, col2 = st.columns(2)
        
        with col1:
            start_year = st.number_input(
                "Начальный год",
                min_value=2020,
                max_value=2030,
                value=datetime.now().year - 1,
                step=1,
                key="report_start_year"
            )
            
            start_month = st.selectbox(
                "Начальный месяц",
                list(range(1, 13)),
                format_func=lambda x: datetime(2000, x, 1).strftime("%B"),
                index=0,
                key="report_start_month"
            )
        
        with col2:
            end_year = st.number_input(
                "Конечный год",
                min_value=2020,
                max_value=2030,
                value=datetime.now().year,
                step=1,
                key="report_end_year"
            )
            
            end_month = st.selectbox(
                "Конечный месяц",
                list(range(1, 13)),
                format_func=lambda x: datetime(2000, x, 1).strftime("%B"),
                index=datetime.now().month - 1,
                key="report_end_month"
            )
        
        if st.button("Сгенерировать отчет", type="primary"):
            with st.spinner("Генерация отчета..."):
                # Генерация отчета
                try:
                    # Здесь можно вызвать более детальный анализ
                    st.info("Детальный отчет находится в разработке")
                    
                    # Временный placeholder
                    st.markdown("""
                    ### Ключевые выводы из анализа отклонений:
                    
                    1. **Revenue отклонения:** В среднем на 15% выше плана
                    2. **Cost отклонения:** На 8% выше плана из-за незапланированных маркетинговых расходов
                    3. **Рекомендации:** 
                       - Оптимизировать маркетинговые расходы
                       - Пересмотреть план на следующий квартал
                       - Улучшить точность прогнозирования
                    """)
                    
                except Exception as e:
                    st.error(f"Ошибка при генерации отчета: {str(e)}")
    
    def render_problem_areas(self, company):
        """Рендеринг проблемных зон"""
        
        st.markdown("#### 🚨 Проблемные зоны и риски")
        
        # Анализ проблемных зон
        try:
            # Используем variance analyzer для выявления проблем
            problem_areas = variance_analyzer.identify_problem_areas(company.id)
            
            if not isinstance(problem_areas, dict):
                st.warning("Неверный формат данных проблемных зон.")
                return

            if problem_areas and "problem_areas" in problem_areas:
                problems = problem_areas["problem_areas"]
                
                for problem in problems:
                    severity = problem.get("severity", "medium")
                    color = "red" if severity == "high" else "orange" if severity == "medium" else "yellow"
                    
                    with st.expander(f"🔴 {problem.get('area', '')} - {severity.title()} Severity", expanded=True):
                        st.markdown(f"**Описание проблемы:** {problem.get('description', '')}")
                        st.markdown(f"**Влияние на бизнес:** {problem.get('impact', '')}")
                        st.markdown(f"**Рекомендуемые действия:** {problem.get('recommended_actions', '')}")
                        
                        # Timeline for resolution
                        timeline = problem.get("resolution_timeline", "30 days")
                        st.markdown(f"**Срок решения:** {timeline}")
                        
                        # Owner
                        owner = problem.get("owner", "TBD")
                        st.markdown(f"**Ответственный:** {owner}")
            else:
                st.success("🎉 Нет критических проблемных зон обнаружено!")
                st.markdown("""
                Все ключевые метрики в пределах допустимых отклонений.
                
                **Рекомендации для поддержания статуса:**
                - Продолжать мониторинг ключевых показателей
                - Регулярно обновлять финансовые планы
                - Проводить ежемесячные reviews
                """)
                
        except Exception as e:
            st.warning(f"Анализ проблемных зон временно недоступен: {str(e)}")
            
            # Fallback анализ
            st.markdown("""
            ### Общие рекомендации по управлению рисками:
            
            **Высокий приоритет:**
            1. Регулярно отслеживайте burn rate и runway
            2. Держите cash reserves на уровне 6+ месяцев
            3. Диверсифицируйте каналы привлечения клиентов
            
            **Средний приоритет:**
            1. Оптимизируйте unit economics
            2. Улучшайте customer retention
            3. Автоматизируйте финансовую отчетность
            
            **Низкий приоритет:**
            1. Обновляйте финансовые модели
            2. Проводите стресс-тесты сценариев
            3. Обучайте команду финансовой грамотности
            """)
    
    def render_scenario_simulation(self):
        """Рендеринг симуляции сценариев"""
        
        company_id = st.session_state.company_id
        company = db_manager.get_company(company_id)
        
        st.markdown(f'<h2 class="sub-header">🎯 Scenario Simulation: {company.name}</h2>', unsafe_allow_html=True)
        
        st.markdown("""
        ### Сценарии "Что если"
        
        Протестируйте различные сценарии развития бизнеса:
        - Ускорение роста
        - Сокращение затрат
        - Изменение ключевых метрик
        - Внешние факторы (рынок, конкуренция)
        """)
        
        # Выбор типа сценария
        scenario_type = st.selectbox(
            "Тип сценария",
            [
                "Оптимистичный рост",
                "Пессимистичный сценарий", 
                "Сокращение затрат",
                "Ускоренный рост",
                "Кастомизированный сценарий"
            ],
            key="scenario_type"
        )
        
        if scenario_type == "Кастомизированный сценарий":
            self.render_custom_scenario(company)
        else:
            self.render_preset_scenario(company, scenario_type)
    
    def render_preset_scenario(self, company, scenario_type):
        """Рендеринг preset сценария"""
        
        st.markdown(f"#### Сценария: {scenario_type}")
        
        # Параметры сценария
        st.markdown("##### Параметры сценария")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if scenario_type == "Оптимистичный рост":
                growth_adjustment = st.slider(
                    "Увеличение роста MRR (%)",
                    min_value=0,
                    max_value=50,
                    value=20,
                    step=5
                ) / 100
            elif scenario_type == "Пессимистичный сценарий":
                growth_adjustment = st.slider(
                    "Снижение роста MRR (%)",
                    min_value=0,
                    max_value=50,
                    value=20,
                    step=5
                ) / -100
            elif scenario_type == "Сокращение затрат":
                cost_reduction = st.slider(
                    "Сокращение затрат (%)",
                    min_value=0,
                    max_value=30,
                    value=15,
                    step=5
                ) / 100
                growth_adjustment = 0
            elif scenario_type == "Ускоренный рост":
                growth_adjustment = st.slider(
                    "Ускорение роста MRR (%)",
                    min_value=0,
                    max_value=100,
                    value=50,
                    step=10
                ) / 100
            else:
                growth_adjustment = 0
        
        with col2:
            scenario_duration = st.slider(
                "Длительность сценария (месяцы)",
                min_value=1,
                max_value=24,
                value=12,
                step=1
            )
        
        with col3:
            cash_injection = st.number_input(
                "Дополнительное финансирование ($)",
                min_value=0,
                value=0,
                step=10000
            )
        
        if st.button("Запустить симуляцию", type="primary"):
            with st.spinner("Запуск симуляции..."):
                try:
                    # Подготовка параметров сценария
                    scenario_params = {
                        "scenario_type": scenario_type.lower().replace(" ", "_"),
                        "growth_adjustment": growth_adjustment,
                        "duration_months": scenario_duration,
                        "additional_funding": cash_injection
                    }
                    
                    if scenario_type == "Сокращение затрат":
                        scenario_params["cost_reduction"] = cost_reduction
                    
                    # Запуск симуляции
                    scenario_results = scenario_simulator.run_scenario(
                        company.id, scenario_params
                    )
                    
                    if scenario_results and "success" in scenario_results and scenario_results["success"]:
                        self._display_scenario_results(scenario_results, scenario_type)
                    else:
                        st.error("Не удалось запустить симуляцию")
                        
                except Exception as e:
                    st.error(f"Ошибка при запуске симуляции: {str(e)}")
    
    def render_custom_scenario(self, company):
        """Рендеринг кастомизированного сценария"""
        
        st.markdown("#### Кастомизированный сценарий")
        
        with st.form("custom_scenario_form"):
            st.markdown("##### Настройки роста")
            
            col1, col2 = st.columns(2)
            
            with col1:
                mrr_growth_change = st.slider(
                    "Изменение роста MRR (%)",
                    min_value=-50,
                    max_value=100,
                    value=0,
                    step=5
                ) / 100
            
            with col2:
                churn_rate_change = st.slider(
                    "Изменение оттока клиентов (%)",
                    min_value=-50,
                    max_value=50,
                    value=0,
                    step=5
                ) / 100
            
            st.markdown("##### Настройки затрат")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                salary_change = st.slider(
                    "Изменение зарплат (%)",
                    min_value=-30,
                    max_value=50,
                    value=0,
                    step=5
                ) / 100
            
            with col2:
                marketing_change = st.slider(
                    "Изменение маркетинга (%)",
                    min_value=-50,
                    max_value=100,
                    value=0,
                    step=5
                ) / 100
            
            with col3:
                cac_change = st.slider(
                    "Изменение CAC (%)",
                    min_value=-50,
                    max_value=50,
                    value=0,
                    step=5
                ) / 100
            
            st.markdown("##### Другие параметры")
            
            col1, col2 = st.columns(2)
            
            with col1:
                scenario_duration = st.slider(
                    "Длительность (месяцы)",
                    min_value=1,
                    max_value=36,
                    value=12,
                    step=1
                )
            
            with col2:
                funding_change = st.number_input(
                    "Изменение финансирования ($)",
                    min_value=-1000000,
                    max_value=1000000,
                    value=0,
                    step=10000
                )
            
            submitted = st.form_submit_button("Запустить кастомную симуляцию", type="primary", width='stretch')
            
            if submitted:
                with st.spinner("Запуск симуляции..."):
                    try:
                        # Подготовка параметров
                        scenario_params = {
                            "scenario_type": "custom",
                            "mrr_growth_change": mrr_growth_change,
                            "churn_rate_change": churn_rate_change,
                            "salary_change": salary_change,
                            "marketing_change": marketing_change,
                            "cac_change": cac_change,
                            "duration_months": scenario_duration,
                            "funding_change": funding_change
                        }
                        
                        # Запуск симуляции
                        scenario_results = scenario_simulator.run_scenario(
                            company.id, scenario_params
                        )
                        
                        if scenario_results and "success" in scenario_results and scenario_results["success"]:
                            self._display_scenario_results(scenario_results, "Кастомный сценарий")
                        else:
                            st.error("Не удалось запустить симуляцию")
                            
                    except Exception as e:
                        st.error(f"Ошибка при запуске симуляции: {str(e)}")
    
    def _display_scenario_results(self, scenario_results, scenario_name):
        """Отображение результатов сценария"""
        
        if "scenario" not in scenario_results:
            st.error("Нет данных результатов сценария")
            return
        
        scenario_data = scenario_results["scenario"]
        
        st.markdown(f"### 📊 Результаты сценария: {scenario_name}")
        
        # Key outcomes
        st.markdown("##### Ключевые результаты")
        
        outcomes = scenario_data.get("scenario_outcomes", {})
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            ending_mrr = outcomes.get("ending_mrr", 0)
            st.metric(
                label="Конечный MRR",
                value=f"${ending_mrr:,.0f}",
                delta=None
            )
        
        with col2:
            ending_cash = outcomes.get("ending_cash", 0)
            st.metric(
                label="Конечный Cash",
                value=f"${ending_cash:,.0f}",
                delta=None
            )
        
        with col3:
            ending_runway = outcomes.get("ending_runway", 0)
            runway_color = "green" if ending_runway > 12 else "orange" if ending_runway > 6 else "red"
            st.markdown(f"""
            <div style="text-align: center;">
                <div style="font-size: 1.8rem; color: {runway_color}; font-weight: bold;">{ending_runway:.1f} мес.</div>
                <div style="color: #666;">Конечный Runway</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            total_profit = outcomes.get("total_profit", 0)
            profit_color = "green" if total_profit > 0 else "red"
            st.metric(
                label="Общая прибыль",
                value=f"${total_profit:,.0f}",
                delta=None
            )
        
        st.markdown("---")
        
        # Comparison with base scenario
        if "comparison_with_base" in scenario_data:
            comparison = scenario_data["comparison_with_base"]
            
            st.markdown("##### Сравнение с базовым сценарием")
            
            comparison_data = [
                ("MRR", comparison.get("mrr_difference", 0), comparison.get("mrr_difference_percent", 0) * 100),
                ("Cash", comparison.get("cash_difference", 0), comparison.get("cash_difference_percent", 0) * 100),
                ("Runway", comparison.get("runway_difference", 0), None),
                ("Прибыль", comparison.get("profit_difference", 0), comparison.get("profit_difference_percent", 0) * 100)
            ]
            
            for metric, difference, percent in comparison_data:
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    if metric == "Runway":
                        st.markdown(f"**{metric}:** {difference:+.1f} мес.")
                    else:
                        st.markdown(f"**{metric}:** ${difference:+,.0f}")
                
                with col2:
                    if percent is not None:
                        color = "green" if percent > 0 else "red"
                        st.markdown(f"<span style='color: {color};'>{percent:+.1f}%</span>", unsafe_allow_html=True)
        
        # Monthly projections
        if "monthly_projections" in scenario_data:
            st.markdown("##### Месячные проекции")
            
            projections = scenario_data["monthly_projections"]
            
            # Создание DataFrame
            projection_data = []
            for month_data in projections:
                projection_data.append({
                    "Месяц": month_data.get("month", ""),
                    "MRR": month_data.get("mrr", 0),
                    "Выручка": month_data.get("revenue", 0),
                    "Затраты": month_data.get("costs", 0),
                    "Прибыль": month_data.get("profit", 0),
                    "Cash Balance": month_data.get("cash_balance", 0),
                    "Runway": month_data.get("runway", 0)
                })
            
            if projection_data:
                df = pd.DataFrame(projection_data)
                
                st.dataframe(
                    df.style.format({
                        'MRR': '${:,.0f}',
                        'Выручка': '${:,.0f}',
                        'Затраты': '${:,.0f}',
                        'Прибыль': '${:,.0f}',
                        'Cash Balance': '${:,.0f}',
                        'Runway': '{:.1f}'
                    }),
                    use_container_width=True,
                    height=300
                )
        
        # Recommendations
        if "recommendations" in scenario_data:
            st.markdown("##### Рекомендации")
            
            recommendations = scenario_data["recommendations"]
            
            for rec in recommendations:
                st.markdown(f"- **{rec.get('category', 'General')}:** {rec.get('recommendation', '')}")
        
        # Risk assessment
        if "risk_assessment" in scenario_data:
            st.markdown("##### Оценка рисков")
            
            risks = scenario_data["risk_assessment"]
            
            for risk in risks:
                severity = risk.get("severity", "medium")
                color = "red" if severity == "high" else "orange" if severity == "medium" else "yellow"
                
                st.markdown(f"- <span style='color: {color};'>**{severity.upper()}:**</span> {risk.get('description', '')}", unsafe_allow_html=True)
    
    def render_ai_analyst(self):
        """Рендеринг AI аналитика"""
        
        company_id = st.session_state.company_id
        company = db_manager.get_company(company_id)
        
        st.markdown(f'<h2 class="sub-header">🤖 AI Analyst: {company.name}</h2>', unsafe_allow_html=True)
        
        # Проверка доступности GigaChat
        with st.spinner("Проверка подключения к GigaChat..."):
            try:
                health_check = get_gigachat_health_check()
                
                if health_check.get("status") == "connected":
                    st.success("✅ GigaChat подключен и готов к работе")
                else:
                    st.warning("⚠️ GigaChat временно недоступен. Используются локальные алгоритмы.")
            except:
                st.warning("⚠️ GigaChat временно недоступен. Используются локальные алгоритмы.")
        
        st.markdown("""
        ### AI аналитик для вашего SaaS бизнеса
        
        Получите глубокий анализ вашего бизнеса с использованием AI:
        - 📊 Анализ финансовых метрик
        - 🎯 Стратегические рекомендации
        - 🔍 Выявление скрытых проблем
        - 📈 Прогнозы и сценарии
        """)
        
        # Выбор типа анализа
        analysis_type = st.selectbox(
            "Тип анализа",
            [
                "Полный анализ бизнеса",
                "Анализ финансового здоровья",
                "Рекомендации по росту",
                "Анализ рисков",
                "Сравнение с конкурентами",
                "Прогноз на 12 месяцев",
                "Кастомизированный запрос"
            ],
            key="ai_analysis_type"
        )
        
        # Дополнительные параметры для кастомизированного запроса
        if analysis_type == "Кастомизированный запрос":
            custom_query = st.text_area(
                "Ваш запрос к AI аналитику",
                placeholder="Например: Проанализируйте наши unit economics и дайте рекомендации по оптимизации...",
                height=100
            )
            
            if not custom_query:
                st.info("Введите ваш запрос для AI анализа")
                return
        else:
            custom_query = None
        
        if st.button("Запустить AI анализ", type="primary", use_container_width=True):
            with st.spinner("AI анализирует ваш бизнес..."):
                try:
                    # Подготовка данных для анализа
                    company_data = company.to_dict()
                    
                    # Получение дополнительных данных
                    actuals = db_manager.get_actual_financials_by_filters({"company_id": company.id})
                    plans = db_manager.get_financial_plans(company.id)
                    
                    # Подготовка контекста
                    context = {
                        "company": company_data,
                        "analysis_type": analysis_type,
                        "actuals_count": len(actuals),
                        "plans_count": len(plans)
                    }
                    
                    if custom_query:
                        context["custom_query"] = custom_query
                    
                    # Вызов AI анализа
                    ai_analysis = analyze_with_gigachat(
                        company_id=company.id,
                        context=context,
                        analysis_type=analysis_type.lower().replace(" ", "_")
                    )
                    
                    if ai_analysis and "success" in ai_analysis and ai_analysis["success"]:
                        st.session_state.ai_analysis = ai_analysis
                        st.rerun()
                    else:
                        st.error("Не удалось получить AI анализ")
                        
                except Exception as e:
                    st.error(f"Ошибка при запуске AI анализа: {str(e)}")
        
        # Отображение результатов предыдущего анализа
        if st.session_state.ai_analysis:
            self._display_ai_analysis_results(st.session_state.ai_analysis)
    
    def _display_ai_analysis_results(self, ai_analysis):
        """Отображение результатов AI анализа"""
        
        # Проверяем, что ai_analysis не None и является словарем
        if not ai_analysis or not isinstance(ai_analysis, dict):
            st.warning("Результаты анализа отсутствуют или имеют неверный формат")
            return
        
        analysis_data = ai_analysis.get("analysis", {})
        
        if not analysis_data or not isinstance(analysis_data, dict):
            st.warning("Данные анализа отсутствуют или имеют неверный формат")
            return
        
        st.markdown("---")
        st.markdown("### 📋 Результаты AI анализа")
        
        # Executive summary
        if "executive_summary" in analysis_data:
            st.markdown("##### 📝 Executive Summary")
            st.markdown(analysis_data["executive_summary"])
        
        # Key findings - ИСПРАВЛЕННЫЙ БЛОК
        if "key_findings" in analysis_data:
            st.markdown("##### 🔍 Ключевые выводы")
            
            findings = analysis_data["key_findings"]
            
            # Проверяем тип данных
            if isinstance(findings, list):
                for i, finding in enumerate(findings, 1):
                    if isinstance(finding, dict):
                        # Если это словарь, извлекаем title и description
                        title = finding.get('title', f'Вывод {i}')
                        description = finding.get('description', '')
                        if description:
                            st.markdown(f"- **{title}:** {description}")
                        else:
                            st.markdown(f"- **{title}**")
                    elif isinstance(finding, str):
                        # Если это строка, просто отображаем
                        st.markdown(f"- {finding}")
                    else:
                        # Если какой-то другой тип
                        st.markdown(f"- {str(finding)}")
                        
            elif isinstance(findings, dict):
                for category, items in findings.items():
                    st.markdown(f"**{category.title()}:**")
                    if isinstance(items, list):
                        for item in items[:3]:  # Ограничиваем 3 пунктами
                            if isinstance(item, dict):
                                st.markdown(f"- **{item.get('title', '')}:** {item.get('description', '')}")
                            elif isinstance(item, str):
                                st.markdown(f"- {item}")
                    elif isinstance(items, str):
                        st.markdown(f"- {items}")
            else:
                st.write(f"Неизвестный формат выводов: {type(findings)}")
        
        # Recommendations - ДОПОЛНИТЕЛЬНО ЗАЩИЩЕННЫЙ БЛОК
        if "recommendations" in analysis_data:
            st.markdown("##### 🎯 Рекомендации")
            
            recommendations = analysis_data["recommendations"]
            
            # Проверяем тип рекомендаций
            if isinstance(recommendations, list):
                for i, rec in enumerate(recommendations[:5], 1):  # Ограничиваем 5 рекомендациями
                    # Проверяем, что rec является словарем
                    if isinstance(rec, dict):
                        priority = rec.get("priority", "medium")
                        color = "red" if priority == "high" else "orange" if priority == "medium" else "green"
                        
                        with st.expander(f"{i}. {rec.get('category', 'General')} - {priority.title()} Priority", expanded=(i == 1)):
                            st.markdown(f"**Рекомендация:** {rec.get('recommendation', '')}")
                            
                            rationale = rec.get('rationale', '')
                            if rationale:
                                st.markdown(f"**Обоснование:** {rationale}")
                            
                            expected_impact = rec.get('expected_impact', 'Medium')
                            if expected_impact:
                                st.markdown(f"**Ожидаемый эффект:** {expected_impact}")
                            
                            implementation_timeline = rec.get('implementation_timeline', '30-60 дней')
                            if implementation_timeline:
                                st.markdown(f"**Срок реализации:** {implementation_timeline}")
                    else:
                        # Если rec не словарь, просто отображаем как строку
                        st.markdown(f"{i}. {str(rec)}")
                        
            elif isinstance(recommendations, dict):
                for category, items in recommendations.items():
                    st.markdown(f"**{category.replace('_', ' ').title()}:**")
                    if isinstance(items, list):
                        for item in items[:3]:
                            if isinstance(item, dict):
                                st.markdown(f"- **{item.get('title', '')}:** {item.get('description', '')}")
                            elif isinstance(item, str):
                                st.markdown(f"- {item}")
                    elif isinstance(items, str):
                        st.markdown(f"- {items}")
            else:
                st.write(f"Неизвестный формат рекомендаций: {type(recommendations)}")
        
        # Financial insights
        if "financial_insights" in analysis_data:
            st.markdown("##### 💰 Финансовые insights")
            
            financial_data = analysis_data["financial_insights"]
            
            if isinstance(financial_data, dict):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Текущее состояние:**")
                    for metric, value in list(financial_data.items())[:4]:
                        st.markdown(f"- {metric}: {value}")
                
                with col2:
                    if len(financial_data) > 4:
                        st.markdown("**Прогнозы:**")
                        for metric, value in list(financial_data.items())[4:8]:
                            st.markdown(f"- {metric}: {value}")
        
        # Risk assessment
        if "risk_assessment" in analysis_data:
            st.markdown("##### 🚨 Оценка рисков")
            
            risks = analysis_data["risk_assessment"]
            
            if isinstance(risks, list):
                for i, risk in enumerate(risks[:3], 1):  # Ограничиваем 3 рисками
                    if isinstance(risk, dict):
                        severity = risk.get("severity", "medium")
                        color = "red" if severity == "high" else "orange" if severity == "medium" else "yellow"
                        
                        st.markdown(f"{i}. <span style='color: {color};'>**{severity.upper()} РИСК:**</span> {risk.get('description', '')}", unsafe_allow_html=True)
                        
                        if "mitigation" in risk:
                            st.markdown(f"  *Меры:* {risk['mitigation']}")
                    else:
                        st.markdown(f"{i}. {str(risk)}")
        
        # Action plan
        if "action_plan" in analysis_data:
            st.markdown("##### 📅 План действий")
            
            action_plan = analysis_data["action_plan"]
            
            if isinstance(action_plan, list):
                for i, action in enumerate(action_plan[:5], 1):  # Ограничиваем 5 действиями
                    if isinstance(action, dict):
                        action_text = action.get('action', '')
                        timeline = action.get('timeline', '30 дней')
                        owner = action.get('owner', 'TBD')
                        
                        st.markdown(f"{i}. **{action_text}**")
                        st.markdown(f"   *Срок:* {timeline}")
                        st.markdown(f"   *Ответственный:* {owner}")
                    else:
                        st.markdown(f"{i}. {str(action)}")
        
        # Кнопки действий
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📤 Экспорт анализа", use_container_width=True):
                self._export_ai_analysis(ai_analysis)
        
        with col2:
            if st.button("🔄 Новый анализ", use_container_width=True):
                st.session_state.ai_analysis = None
                st.rerun()
        
        with col3:
            if st.button("💬 Задать уточняющий вопрос", use_container_width=True):
                st.info("Функция уточняющих вопросов в разработке")
        
    def _export_ai_analysis(self, ai_analysis):
        """Экспорт AI анализа"""
        
        try:
            # Подготовка данных для экспорта
            export_data = {
                "ai_analysis": ai_analysis,
                "export_date": datetime.now().isoformat(),
                "export_format": "PDF"
            }
            
            # Экспорт
            filename = f"ai_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            with st.spinner("Подготовка отчета..."):
                # Временная реализация
                st.success(f"Отчет готов к скачиванию: {filename}")
                
                # Создание простого PDF
                from reportlab.lib.pagesizes import letter
                from reportlab.pdfgen import canvas
                
                buffer = io.BytesIO()
                c = canvas.Canvas(buffer, pagesize=letter)
                
                # Заголовок
                c.setFont("Helvetica-Bold", 16)
                c.drawString(100, 750, "AI Analysis Report")
                
                # Дата
                c.setFont("Helvetica", 10)
                c.drawString(100, 730, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Простой контент
                c.setFont("Helvetica", 12)
                c.drawString(100, 700, "AI Analysis completed successfully.")
                
                c.save()
                
                pdf_data = buffer.getvalue()
                buffer.close()
                
                # Предоставление для скачивания
                st.download_button(
                    label="Скачать PDF отчет",
                    data=pdf_data,
                    file_name=filename,
                    mime="application/pdf"
                )
                
        except Exception as e:
            st.error(f"Ошибка при экспорте: {str(e)}")
    
    def render_reports(self):
        """Рендеринг отчетов"""
        
        company_id = st.session_state.company_id
        company = db_manager.get_company(company_id)

        if not company:
            st.error("Компания не найдена. Добавьте данные компании, чтобы сформировать отчет.")
            return
        
        st.markdown(f'<h2 class="sub-header">📋 Reports: {company.name}</h2>', unsafe_allow_html=True)
        
        st.markdown("""
        ### Генерация профессиональных отчетов
        
        Создавайте отчеты для разных аудиторий:
        - 📈 Инвесторам (pitch decks, investment memos)
        - 👥 Совету директоров (квартальные отчеты)
        - 👨‍💼 Менеджменту (ежемесячные отчеты)
        - 🏢 Команде (team updates)
        """)
        
        # Выбор типа отчета
        report_type = st.selectbox(
            "Тип отчета",
            [
                "Pitch Deck для инвесторов",
                "Investment Memo",
                "Квартальный отчет для Board",
                "Ежемесячный отчет для менеджмента",
                "Team отчет",
                "Финансовый отчет",
                "Бизнес-план"
            ],
            key="report_type_select"
        )
        
        # Дополнительные параметры в зависимости от типа отчета
        if report_type == "Pitch Deck для инвесторов":
            col1, col2 = st.columns(2)
            
            with col1:
                funding_round = st.selectbox(
                    "Раунд финансирования",
                    ["pre_seed", "seed", "series_a", "series_b", "series_c"],
                    format_func=lambda x: x.replace("_", " ").title(),
                    key="funding_round"
                )
            
            with col2:
                ask_amount = st.number_input(
                    "Запрашиваемая сумма ($)",
                    min_value=0,
                    value=1000000,
                    step=100000
                )
        
        elif report_type == "Квартальный отчет для Board":
            col1, col2 = st.columns(2)
            
            with col1:
                year = st.number_input(
                    "Год",
                    min_value=2020,
                    max_value=2030,
                    value=datetime.now().year,
                    step=1,
                    key="board_report_year"
                )
            
            with col2:
                quarter = st.selectbox(
                    "Квартал",
                    [1, 2, 3, 4],
                    format_func=lambda x: f"Q{x}",
                    index=(datetime.now().month - 1) // 3,
                    key="board_report_quarter"
                )
        
        elif report_type == "Ежемесячный отчет для менеджмента":
            col1, col2 = st.columns(2)
            
            with col1:
                year = st.number_input(
                    "Год",
                    min_value=2020,
                    max_value=2030,
                    value=datetime.now().year,
                    step=1,
                    key="management_report_year"
                )
            
            with col2:
                month = st.selectbox(
                    "Месяц",
                    list(range(1, 13)),
                    format_func=lambda x: datetime(2000, x, 1).strftime("%B"),
                    index=datetime.now().month - 1,
                    key="management_report_month"
                )
        
        elif report_type == "Investment Memo":
            col1, col2 = st.columns(2)
            
            with col1:
                investment_amount = st.number_input(
                    "Сумма инвестиций ($)",
                    min_value=0,
                    value=2000000,
                    step=100000
                )
            
            with col2:
                valuation = st.number_input(
                    "Valuation компании ($)",
                    min_value=0,
                    value=10000000,
                    step=1000000
                )
        
        # Кнопка генерации отчета
        if st.button("Сгенерировать отчет", type="primary", use_container_width=True):
            with st.spinner("Генерация отчета..."):
                try:
                    report_data = None
                    
                    if report_type == "Pitch Deck для инвесторов":
                        report_data = generate_investor_pitch_deck(
                            company.id, funding_round, ask_amount
                        )
                    
                    elif report_type == "Investment Memo":
                        report_data = generate_investment_memo(
                            company.id, investment_amount, valuation
                        )
                    
                    elif report_type == "Квартальный отчет для Board":
                        report_data = generate_quarterly_board_report(
                            company.id, quarter, year
                        )
                    
                    elif report_type == "Ежемесячный отчет для менеджмента":
                        report_data = generate_management_report(
                            company.id, month, year
                        )
                    
                    elif report_type == "Team отчет":
                        report_data = generate_team_report(
                            company.id, datetime.now().month, datetime.now().year
                        )
                    
                    else:
                        st.info("Этот тип отчета находится в разработке")
                        return
                    
                    if report_data and "success" in report_data and report_data["success"]:
                        st.session_state.export_data = report_data
                        st.success("Отчет успешно сгенерирован!")
                        st.rerun()
                    else:
                        st.error("Не удалось сгенерировать отчет")
                        
                except Exception as e:
                    st.error(f"Ошибка при генерации отчета: {str(e)}")
        
        # Отображение сгенерированного отчета
        if st.session_state.export_data:
            self._display_report_preview(st.session_state.export_data)
    
    def _display_report_preview(self, report_data):
        """Отображение preview отчета"""
        
        report = report_data.get("report", {})
        report_type = report.get("report_type", "Unknown")
        
        st.markdown("---")
        st.markdown(f"### 📋 Preview отчета: {report_type.replace('_', ' ').title()}")
        
        # Basic report info
        col1, col2 = st.columns(2)
        
        with col1:
            if "company" in report:
                company_info = report["company"]
                st.markdown(f"**Компания:** {company_info.get('name', 'N/A')}")
                st.markdown(f"**Стадия:** {company_info.get('stage', 'N/A').replace('_', ' ').title()}")
        
        with col2:
            if "generated_date" in report:
                st.markdown(f"**Сгенерирован:** {report['generated_date']}")
            
            if "estimated_pages" in report_data:
                st.markdown(f"**Страниц:** {report_data['estimated_pages']}")
        
        # Report content preview
        if report_type == "pitch_deck":
            self._display_pitch_deck_preview(report)
        elif report_type == "investment_memo":
            self._display_investment_memo_preview(report)
        elif report_type == "quarterly":
            self._display_board_report_preview(report)
        elif report_type == "management":
            self._display_management_report_preview(report)
        elif report_type == "team":
            self._display_team_report_preview(report)
        
        # Export options
        st.markdown("---")
        st.markdown("##### 📤 Опции экспорта")
        
        if "export_formats" in report_data:
            export_formats = report_data["export_formats"]
            
            selected_format = st.selectbox(
                "Формат экспорта",
                export_formats,
                key="export_format_select"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                filename = st.text_input(
                    "Имя файла",
                    value=f"{report_type}_{datetime.now().strftime('%Y%m%d')}.{selected_format.lower()}",
                    key="export_filename"
                )
            
            with col2:
                if st.button("Экспортировать отчет", type="primary", use_container_width=True):
                    with st.spinner(f"Экспорт в {selected_format}..."):
                        try:
                            # Экспорт отчета
                            if report_type == "pitch_deck":
                                export_data = export_report(report, selected_format.lower(), filename)
                            elif report_type == "investment_memo":
                                export_data = export_report(report, selected_format.lower(), filename)
                            elif report_type == "quarterly":
                                export_data = export_report(report, selected_format.lower(), filename)
                            elif report_type in ["management", "team"]:
                                export_data = export_report(report, selected_format.lower(), filename)
                            else:
                                export_data = export_report(report, selected_format.lower(), filename)
                            
                            if export_data is not None:
                                # Если export_data - это bytes (PDF, Excel), предоставляем для скачивания
                                if isinstance(export_data, bytes):
                                    st.download_button(
                                        label="Скачать файл",
                                        data=export_data,
                                        file_name=filename,
                                        mime=f"application/{selected_format.lower()}"
                                    )
                                elif isinstance(export_data, str):
                                    # Для HTML, CSV, JSON
                                    st.download_button(
                                        label="Скачать файл",
                                        data=export_data,
                                        file_name=filename,
                                        mime="text/plain"
                                    )
                                
                                st.success(f"Отчет экспортирован как {filename}")
                            else:
                                st.info(f"Файл сохранен как {filename}")
                                
                        except Exception as e:
                            st.error(f"Ошибка при экспорте: {str(e)}")
        
        # Clear report button
        if st.button("Очистить отчет", type="secondary", use_container_width=True):
            st.session_state.export_data = None
            st.rerun()
    
    def _display_pitch_deck_preview(self, report):
        """Отображение preview pitch deck"""
        
        st.markdown("##### 🎯 Pitch Deck Slides Preview")
        
        if "slides" in report:
            slides = report["slides"]
            
            # Показываем первые 3 слайда
            for i, slide in enumerate(slides[:3]):
                with st.expander(f"Slide {slide.get('number', i+1)}: {slide.get('title', '')}", expanded=(i == 0)):
                    content = slide.get("content", {})
                    
                    if slide.get("type") == "cover":
                        st.markdown(f"**Company:** {content.get('tagline', '')}")
                    
                    elif slide.get("type") == "traction":
                        st.markdown(f"**MRR:** {content.get('revenue', '')}")
                        st.markdown(f"**Growth:** {content.get('growth', '')}")
                    
                    elif slide.get("type") == "financials":
                        st.markdown("**Current State:**")
                        for key, value in content.get("current_state", {}).items():
                            st.markdown(f"- {key}: {value}")
        
        if "funding_round" in report:
            st.markdown(f"**Funding Round:** {report['funding_round'].replace('_', ' ').title()}")
        
        if "ask_amount" in report:
            st.markdown(f"**Ask Amount:** ${report['ask_amount']:,.0f}")
        
        if "valuation" in report:
            valuation = report["valuation"]
            st.markdown(f"**Valuation:** ${valuation.get('amount', 0):,.0f}")
            st.markdown(f"**Method:** {valuation.get('method', 'N/A')}")
    
    def _display_investment_memo_preview(self, report):
        """Отображение preview investment memo"""
        
        st.markdown("##### 📋 Investment Memo Preview")
        
        if "investment_details" in report:
            details = report["investment_details"]
            st.markdown(f"**Investment Amount:** ${details.get('amount', 0):,.0f}")
            st.markdown(f"**Valuation:** ${details.get('valuation', 0):,.0f}")
            st.markdown(f"**Ownership:** {details.get('ownership', 0)*100:.1f}%")
        
        if "sections" in report:
            sections = report["sections"]
            
            # Показываем ключевые секции
            key_sections = ["executive_summary", "investment_thesis", "financial_analysis", "recommendation"]
            
            for section_key in key_sections:
                if section_key in sections:
                    with st.expander(f"{section_key.replace('_', ' ').title()}", expanded=(section_key == "executive_summary")):
                        section_data = sections[section_key]
                        
                        if section_key == "executive_summary":
                            if "investment_highlights" in section_data:
                                st.markdown("**Highlights:**")
                                for highlight in section_data["investment_highlights"][:3]:
                                    st.markdown(f"- {highlight}")
                        
                        elif section_key == "recommendation":
                            for key, value in section_data.items():
                                st.markdown(f"**{key.replace('_', ' ').title()}:** {value}")
    
    def _display_board_report_preview(self, report):
        """Отображение preview board report"""
        
        st.markdown("##### 👥 Board Report Preview")
        
        if "quarter" in report and "year" in report:
            st.markdown(f"**Period:** Q{report['quarter']} {report['year']}")
        
        if "performance_summary" in report:
            performance = report["performance_summary"]
            
            if "overall_performance" in performance:
                overall = performance["overall_performance"]
                st.markdown(f"**Overall Performance:** {overall.get('rating', 'N/A')} ({overall.get('score', 0)}/10)")
        
        if "actions_required" in report:
            actions = report["actions_required"]
            
            st.markdown("**Actions Required:**")
            for i, action in enumerate(actions[:2]):  # Показываем 2 действия
                st.markdown(f"{i+1}. {action.get('action', '')} - {action.get('priority', 'medium').title()}")
    
    def _display_management_report_preview(self, report):
        """Отображение preview management report"""
        
        st.markdown("##### 👨‍💼 Management Report Preview")
        
        if "month_name" in report:
            st.markdown(f"**Period:** {report['month_name']}")
        
        if "highlights" in report:
            st.markdown("**Highlights:**")
            for highlight in report["highlights"][:3]:
                st.markdown(f"- {highlight}")
        
        if "action_items" in report:
            st.markdown("**Action Items:**")
            for i, action in enumerate(report["action_items"][:2]):
                st.markdown(f"{i+1}. {action.get('action', '')} - Due: {action.get('due_date', '')}")
    
    def _display_team_report_preview(self, report):
        """Отображение preview team report"""
        
        st.markdown("##### 🏢 Team Report Preview")
        
        if "team_achievements" in report:
            st.markdown("**Team Achievements:**")
            for achievement in report["team_achievements"][:2]:
                st.markdown(f"- {achievement.get('team', '')}: {achievement.get('achievement', '')}")
        
        if "next_month_focus" in report:
            focus = report["next_month_focus"]
            st.markdown(f"**Next Month Theme:** {focus.get('theme', 'N/A')}")
    
    def render_settings(self):
        """Рендеринг настроек"""
        
        company_id = st.session_state.company_id
        company = db_manager.get_company(company_id)
        
        st.markdown(f'<h2 class="sub-header">⚙️ Settings: {company.name}</h2>', unsafe_allow_html=True)
        
        # Вкладки настроек
        settings_tabs = st.tabs(["🏢 Компания", "🔧 Интеграции", "📊 Настройки отчетов", "👤 Пользователь"])
        
        with settings_tabs[0]:  # Компания
            self.render_company_settings(company)
        
        with settings_tabs[1]:  # Интеграции
            self.render_integration_settings()
        
        with settings_tabs[2]:  # Настройки отчетов
            self.render_report_settings()
        
        with settings_tabs[3]:  # Пользователь
            self.render_user_settings()
    
    def render_company_settings(self, company):
        """Рендеринг настроек компании"""
        
        st.markdown("#### Настройки компании")
        
        with st.form("company_settings_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input(
                    "Название компании",
                    value=company.name
                )
                
                stage = st.selectbox(
                    "Стадия компании",
                    ["pre_seed", "seed", "series_a", "series_b", "series_c", "growth", "mature"],
                    format_func=lambda x: x.replace("_", " ").title(),
                    index=["pre_seed", "seed", "series_a", "series_b", "series_c", "growth", "mature"].index(company.stage) if company.stage in ["pre_seed", "seed", "series_a", "series_b", "series_c", "growth", "mature"] else 0
                )
                
                monthly_price = st.number_input(
                    "Средняя месячная цена ($)",
                    min_value=0.0,
                    value=float(company.monthly_price),
                    step=10.0
                )
            
            with col2:
                current_mrr = st.number_input(
                    "Текущий MRR ($)",
                    min_value=0.0,
                    value=float(company.current_mrr),
                    step=1000.0
                )
                
                current_customers = st.number_input(
                    "Количество клиентов",
                    min_value=0,
                    value=company.current_customers,
                    step=10
                )
                
                team_size = st.number_input(
                    "Размер команды",
                    min_value=1,
                    value=company.team_size,
                    step=1
                )
            
            cash_balance = st.number_input(
                "Cash balance ($)",
                min_value=0.0,
                value=float(company.cash_balance),
                step=10000.0
            )
            
            industry = st.text_input(
                "Индустрия",
                value=company.industry or ""
            )
            
            description = st.text_area(
                "Описание компании",
                value=company.description or "",
                height=100
            )
            
            submitted = st.form_submit_button("Сохранить настройки", type="primary", width='stretch')
            
            if submitted:
                try:
                    # Обновление компании
                    company.name = name
                    company.stage = stage
                    company.current_mrr = current_mrr
                    company.current_customers = current_customers
                    company.monthly_price = monthly_price
                    company.team_size = team_size
                    company.cash_balance = cash_balance
                    company.industry = industry
                    company.description = description
                    
                    db_manager.update_company(company)
                    
                    st.success("Настройки компании успешно обновлены!")
                    time.sleep(1)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Ошибка при обновлении настроек: {str(e)}")
        
        # Опасная зона
        st.markdown("---")
        st.markdown("##### 🚨 Опасная зона")
        
        with st.expander("Удалить компанию", expanded=False):
            st.warning("""
            **Внимание:** Удаление компании приведет к удалению всех связанных данных:
            - Финансовые планы
            - Фактические данные
            - Отчеты
            - Анализы
            
            Это действие нельзя отменить!
            """)
            
            confirm_delete = st.text_input(
                "Для подтверждения введите название компании",
                placeholder="Введите название компании"
            )
            
            if st.button("🗑️ Удалить компанию", type="secondary", disabled=True):
                if confirm_delete == company.name:
                    try:
                        db_manager.delete_company(company.id)
                        st.session_state.company_id = None
                        st.success("Компания удалена")
                        time.sleep(2)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Ошибка при удалении: {str(e)}")
                else:
                    st.error("Название компании не совпадает")
    
    def render_integration_settings(self):
        """Рендеринг настроек интеграций"""
        
        st.markdown("#### Настройки интеграций")
        
        # GigaChat API
        st.markdown("##### 🤖 GigaChat API")
        
        with st.form("gigachat_settings"):
            # В реальном приложении эти настройки должны храниться в безопасном месте
            gigachat_api_key = st.text_input(
                "API Key",
                type="password",
                placeholder="Введите ваш GigaChat API key"
            )
            
            gigachat_base_url = st.text_input(
                "Base URL",
                value="https://gigachat.devices.sberbank.ru/api/v1",
                placeholder="Base URL для GigaChat API"
            )
            
            submitted = st.form_submit_button("Сохранить настройки GigaChat", type="primary")
            
            if submitted:
                st.success("Настройки GigaChat сохранены (в демо-версии)")
                # В реальном приложении здесь нужно сохранить настройки в безопасное хранилище
        
        # Другие интеграции
        st.markdown("##### 🔌 Другие интеграции")
        
        integrations = [
            ("QuickBooks", "Бухгалтерское ПО", False),
            ("Xero", "Бухгалтерское ПО", False),
            ("Stripe", "Платежи", True),
            ("HubSpot", "CRM", False),
            ("Slack", "Уведомления", True)
        ]
        
        for name, description, enabled in integrations:
            col1, col2, col3 = st.columns([2, 3, 1])
            
            with col1:
                st.markdown(f"**{name}**")
            
            with col2:
                st.markdown(description)
            
            with col3:
                st.checkbox("Включено", value=enabled, key=f"integration_{name}", disabled=True)
    
    def render_report_settings(self):
        """Рендеринг настроек отчетов"""
        
        st.markdown("#### Настройки отчетов")
        
        # Форматы отчетов
        st.markdown("##### 📊 Настройки форматов")
        
        with st.form("report_settings_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                default_export_format = st.selectbox(
                    "Формат экспорта по умолчанию",
                    ["PDF", "Excel", "HTML", "CSV"],
                    index=0
                )
                
                include_charts = st.checkbox(
                    "Включать графики в отчеты",
                    value=True
                )
            
            with col2:
                currency = st.selectbox(
                    "Валюта отчетов",
                    ["USD", "EUR", "RUB", "GBP"],
                    index=0
                )
                
                date_format = st.selectbox(
                    "Формат дат",
                    ["YYYY-MM-DD", "DD/MM/YYYY", "MM/DD/YYYY"],
                    index=0
                )
            
            # Настройки email отчетов
            st.markdown("##### 📧 Настройки email отчетов")
            
            email_reporting = st.checkbox(
                "Включить автоматическую отправку отчетов по email",
                value=False
            )
            
            if email_reporting:
                email_recipients = st.text_area(
                    "Получатели отчетов (через запятую)",
                    placeholder="email1@example.com, email2@example.com"
                )
                
                report_frequency = st.selectbox(
                    "Частота отчетов",
                    ["Ежемесячно", "Ежеквартально", "Еженедельно"]
                )
            
            submitted = st.form_submit_button("Сохранить настройки отчетов", type="primary", width='stretch')
            
            if submitted:
                st.success("Настройки отчетов сохранены (в демо-версии)")
    
    def render_user_settings(self):
        """Рендеринг пользовательских настроек"""
        
        st.markdown("#### Пользовательские настройки")
        
        # Информация о пользователе
        st.markdown("##### 👤 Информация о пользователе")
        
        with st.form("user_settings_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                user_name = st.text_input(
                    "Имя",
                    value="Администратор"
                )
                
                user_email = st.text_input(
                    "Email",
                    value="admin@company.com"
                )
            
            with col2:
                user_role = st.selectbox(
                    "Роль",
                    ["Администратор", "Финансовый директор", "Аналитик", "Менеджер"],
                    index=0
                )
                
                notifications = st.checkbox(
                    "Получать уведомления",
                    value=True
                )
            
            # Настройки интерфейса
            st.markdown("##### 🎨 Настройки интерфейса")
            
            theme = st.selectbox(
                "Тема",
                ["Светлая", "Темная", "Авто"],
                index=0
            )
            
            language = st.selectbox(
                "Язык",
                ["Русский", "Английский"],
                index=0
            )
            
            submitted = st.form_submit_button("Сохранить пользовательские настройки", type="primary", width='stretch')
            
            if submitted:
                st.success("Пользовательские настройки сохранены (в демо-версии)")
        
        # Выход из системы
        st.markdown("---")
        
        if st.button("🚪 Выйти из системы", type="secondary", use_container_width=True):
            st.session_state.company_id = None
            st.success("Вы вышли из системы")
            time.sleep(1)
            st.rerun()

# Запуск приложения
if __name__ == "__main__":
    app = SAASDashboardApp()
    app.run()
