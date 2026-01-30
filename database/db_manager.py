"""
Менеджер базы данных для SaaS Financial Planning System
Обеспечивает единый интерфейс для работы с SQLite
"""

import sqlite3
import json
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Company:
    """Модель компании/стартапа"""
    id: Optional[int] = None
    user_id: Optional[int] = None
    name: str = ""
    description: str = ""
    stage: str = "pre_seed"
    industry: str = ""
    country: str = "Russia"
    currency: str = "RUB"
    current_mrr: float = 0.0
    current_customers: int = 0
    monthly_price: float = 0.0
    team_size: int = 1
    cash_balance: float = 0.0
    fiscal_year_start: int = 1
    reporting_currency: str = "RUB"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: bool = True
    
    # Метод для совместимости с app.py
    def to_dict(self):
        return asdict(self)

@dataclass
class FinancialPlan:
    """Модель финансового плана на год"""
    id: Optional[int] = None
    company_id: int = 0
    plan_name: str = ""
    plan_year: int = datetime.now().year
    version: int = 1
    description: str = ""
    status: str = "draft"
    is_active: bool = False
    assumptions: Optional[Dict] = None
    seasonality_pattern: Optional[Dict] = None
    growth_assumptions: Optional[Dict] = None
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    activated_at: Optional[datetime] = None

@dataclass
class MonthlyPlan:
    """Модель плана на месяц"""
    id: Optional[int] = None
    plan_id: int = 0
    month_number: int = 0
    month_name: str = ""
    year: int = datetime.now().year
    quarter: int = 1
    
    # Revenue
    plan_mrr: float = 0.0
    plan_new_customers: int = 0
    plan_expansion_mrr: float = 0.0
    plan_churn_rate: float = 0.05
    plan_churned_mrr: float = 0.0
    plan_reactivated_mrr: float = 0.0
    
    # CAC
    plan_marketing_budget: float = 0.0
    plan_sales_budget: float = 0.0
    plan_cac_target: float = 0.0
    
    # OPEX
    plan_salaries: float = 0.0
    plan_office_rent: float = 0.0
    plan_cloud_services: float = 0.0
    plan_software_subscriptions: float = 0.0
    plan_legal_accounting: float = 0.0
    plan_marketing_ops: float = 0.0
    plan_other_opex: float = 0.0
    
    # CAPEX
    plan_capex_total: float = 0.0
    plan_capex_equipment: float = 0.0
    plan_capex_software: float = 0.0
    plan_capex_furniture: float = 0.0
    plan_capex_other: float = 0.0
    
    # Calculated Metrics
    plan_total_revenue: float = 0.0
    plan_total_costs: float = 0.0
    plan_burn_rate: float = 0.0
    plan_gross_margin: float = 0.0
    plan_runway: float = 0.0
    plan_ltv_cac_ratio: float = 0.0
    plan_cac_payback_months: float = 0.0
    
    # Дополнительные поля для совместимости с app.py
    plan_total_customers: int = 0
    plan_churned_customers: int = 0
    plan_cash_balance: float = 0.0
    plan_cac: float = 0.0
    plan_ltv: float = 0.0
    plan_ltv_cac_ratio: float = 0.0
    plan_gross_margin: float = 0.0
    
    # Flags
    is_locked: bool = False
    seasonality_factor: float = 1.0
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self):
        return asdict(self)

@dataclass
class ActualData:
    """Модель фактических данных за месяц"""
    id: Optional[int] = None
    monthly_plan_id: Optional[int] = None
    company_id: Optional[int] = None  # Для прямой связи с компанией
    
    # Revenue Actual
    actual_mrr: float = 0.0
    actual_new_customers: int = 0
    actual_expansion_mrr: float = 0.0
    actual_churn_rate: float = 0.0
    actual_churned_mrr: float = 0.0
    
    # CAC Actual
    actual_marketing_spent: float = 0.0
    actual_sales_spent: float = 0.0
    actual_cac: float = 0.0
    
    # OPEX Actual
    actual_salaries: float = 0.0
    actual_office_rent: float = 0.0
    actual_cloud_services: float = 0.0
    actual_software_subscriptions: float = 0.0
    actual_legal_accounting: float = 0.0
    actual_marketing_ops: float = 0.0
    actual_other_opex: float = 0.0
    
    # CAPEX Actual
    actual_capex_spent: float = 0.0
    actual_capex_equipment: float = 0.0
    actual_capex_software: float = 0.0
    actual_capex_furniture: float = 0.0
    actual_capex_other: float = 0.0
    
    # Calculated Metrics
    actual_total_revenue: float = 0.0
    actual_total_costs: float = 0.0
    actual_burn_rate: float = 0.0
    actual_gross_margin: float = 0.0
    actual_runway: float = 0.0
    actual_ltv_cac_ratio: float = 0.0
    actual_cac_payback_months: float = 0.0
    
    # Variance
    variance_mrr: float = 0.0
    variance_burn_rate: float = 0.0
    variance_runway: float = 0.0
    variance_cac: float = 0.0
    variance_new_customers: float = 0.0
    
    # Дополнительные поля для совместимости с app.py
    year: int = datetime.now().year
    month_number: int = datetime.now().month
    actual_churned_customers: int = 0
    actual_total_customers: int = 0
    actual_cash_balance: float = 0.0
    actual_ltv: float = 0.0
    
    # Metadata
    data_source: str = "manual"
    import_file: Optional[str] = None
    notes: str = ""
    is_finalized: bool = False
    is_verified: bool = False
    recorded_by: Optional[int] = None
    recorded_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    verified_by: Optional[int] = None
    
    def to_dict(self):
        return asdict(self)

class DatabaseManager:
    """
    Менеджер базы данных с методами для всех операций
    Реализует паттерн Singleton для единого подключения
    """
    
    _instance = None
    
    def __new__(cls, db_path: str = 'database/saas_finance.db'):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, db_path: str = 'database/saas_finance.db'):
        if not self._initialized:
            self.db_path = db_path
            self._initialized = True
    
    def get_connection(self) -> sqlite3.Connection:
        """Получение соединения с базой данных"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            return conn
        except sqlite3.Error as e:
            logger.error(f"Ошибка подключения к БД: {e}")
            raise
    
    def initialize_database(self):
        """Инициализация базы данных и создание таблиц"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Создание таблицы companies
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS companies (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        name TEXT NOT NULL,
                        description TEXT,
                        stage TEXT DEFAULT 'pre_seed',
                        industry TEXT,
                        country TEXT DEFAULT 'Russia',
                        currency TEXT DEFAULT 'RUB',
                        current_mrr REAL DEFAULT 0.0,
                        current_customers INTEGER DEFAULT 0,
                        monthly_price REAL DEFAULT 0.0,
                        team_size INTEGER DEFAULT 1,
                        cash_balance REAL DEFAULT 0.0,
                        fiscal_year_start INTEGER DEFAULT 1,
                        reporting_currency TEXT DEFAULT 'RUB',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT 1
                    )
                ''')
                
                # Создание таблицы financial_plans
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS financial_plans (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        company_id INTEGER NOT NULL,
                        plan_name TEXT NOT NULL,
                        plan_year INTEGER NOT NULL,
                        version INTEGER DEFAULT 1,
                        description TEXT,
                        status TEXT DEFAULT 'draft',
                        is_active BOOLEAN DEFAULT 0,
                        assumptions TEXT,
                        seasonality_pattern TEXT,
                        growth_assumptions TEXT,
                        created_by INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        activated_at TIMESTAMP,
                        FOREIGN KEY (company_id) REFERENCES companies (id) ON DELETE CASCADE
                    )
                ''')
                
                # Создание таблицы monthly_plans
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS monthly_plans (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        plan_id INTEGER NOT NULL,
                        month_number INTEGER NOT NULL,
                        month_name TEXT NOT NULL,
                        year INTEGER NOT NULL,
                        quarter INTEGER NOT NULL,
                        
                        -- Revenue
                        plan_mrr REAL DEFAULT 0.0,
                        plan_new_customers INTEGER DEFAULT 0,
                        plan_expansion_mrr REAL DEFAULT 0.0,
                        plan_churn_rate REAL DEFAULT 0.05,
                        plan_churned_mrr REAL DEFAULT 0.0,
                        plan_reactivated_mrr REAL DEFAULT 0.0,
                        
                        -- CAC
                        plan_marketing_budget REAL DEFAULT 0.0,
                        plan_sales_budget REAL DEFAULT 0.0,
                        plan_cac_target REAL DEFAULT 0.0,
                        
                        -- OPEX
                        plan_salaries REAL DEFAULT 0.0,
                        plan_office_rent REAL DEFAULT 0.0,
                        plan_cloud_services REAL DEFAULT 0.0,
                        plan_software_subscriptions REAL DEFAULT 0.0,
                        plan_legal_accounting REAL DEFAULT 0.0,
                        plan_marketing_ops REAL DEFAULT 0.0,
                        plan_other_opex REAL DEFAULT 0.0,
                        
                        -- CAPEX
                        plan_capex_total REAL DEFAULT 0.0,
                        plan_capex_equipment REAL DEFAULT 0.0,
                        plan_capex_software REAL DEFAULT 0.0,
                        plan_capex_furniture REAL DEFAULT 0.0,
                        plan_capex_other REAL DEFAULT 0.0,
                        
                        -- Calculated Metrics
                        plan_total_revenue REAL DEFAULT 0.0,
                        plan_total_costs REAL DEFAULT 0.0,
                        plan_burn_rate REAL DEFAULT 0.0,
                        plan_gross_margin REAL DEFAULT 0.0,
                        plan_runway REAL DEFAULT 0.0,
                        plan_ltv_cac_ratio REAL DEFAULT 0.0,
                        plan_cac_payback_months REAL DEFAULT 0.0,
                        
                        -- Дополнительные поля для совместимости
                        plan_total_customers INTEGER DEFAULT 0,
                        plan_churned_customers INTEGER DEFAULT 0,
                        plan_cash_balance REAL DEFAULT 0.0,
                        plan_cac REAL DEFAULT 0.0,
                        plan_ltv REAL DEFAULT 0.0,
                        
                        -- Flags
                        is_locked BOOLEAN DEFAULT 0,
                        seasonality_factor REAL DEFAULT 1.0,
                        
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (plan_id) REFERENCES financial_plans (id) ON DELETE CASCADE
                    )
                ''')
                
                # Создание таблицы actual_data
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS actual_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        monthly_plan_id INTEGER,
                        company_id INTEGER,
                        year INTEGER NOT NULL,
                        month_number INTEGER NOT NULL,
                        
                        -- Revenue Actual
                        actual_mrr REAL DEFAULT 0.0,
                        actual_new_customers INTEGER DEFAULT 0,
                        actual_expansion_mrr REAL DEFAULT 0.0,
                        actual_churn_rate REAL DEFAULT 0.0,
                        actual_churned_mrr REAL DEFAULT 0.0,
                        
                        -- CAC Actual
                        actual_marketing_spent REAL DEFAULT 0.0,
                        actual_sales_spent REAL DEFAULT 0.0,
                        actual_cac REAL DEFAULT 0.0,
                        
                        -- OPEX Actual
                        actual_salaries REAL DEFAULT 0.0,
                        actual_office_rent REAL DEFAULT 0.0,
                        actual_cloud_services REAL DEFAULT 0.0,
                        actual_software_subscriptions REAL DEFAULT 0.0,
                        actual_legal_accounting REAL DEFAULT 0.0,
                        actual_marketing_ops REAL DEFAULT 0.0,
                        actual_other_opex REAL DEFAULT 0.0,
                        
                        -- CAPEX Actual
                        actual_capex_spent REAL DEFAULT 0.0,
                        actual_capex_equipment REAL DEFAULT 0.0,
                        actual_capex_software REAL DEFAULT 0.0,
                        actual_capex_furniture REAL DEFAULT 0.0,
                        actual_capex_other REAL DEFAULT 0.0,
                        
                        -- Calculated Metrics
                        actual_total_revenue REAL DEFAULT 0.0,
                        actual_total_costs REAL DEFAULT 0.0,
                        actual_burn_rate REAL DEFAULT 0.0,
                        actual_gross_margin REAL DEFAULT 0.0,
                        actual_runway REAL DEFAULT 0.0,
                        actual_ltv_cac_ratio REAL DEFAULT 0.0,
                        actual_cac_payback_months REAL DEFAULT 0.0,
                        
                        -- Variance
                        variance_mrr REAL DEFAULT 0.0,
                        variance_burn_rate REAL DEFAULT 0.0,
                        variance_runway REAL DEFAULT 0.0,
                        variance_cac REAL DEFAULT 0.0,
                        variance_new_customers REAL DEFAULT 0.0,
                        
                        -- Дополнительные поля для совместимости
                        actual_churned_customers INTEGER DEFAULT 0,
                        actual_total_customers INTEGER DEFAULT 0,
                        actual_cash_balance REAL DEFAULT 0.0,
                        actual_ltv REAL DEFAULT 0.0,
                        
                        -- Metadata
                        data_source TEXT DEFAULT 'manual',
                        import_file TEXT,
                        notes TEXT,
                        is_finalized BOOLEAN DEFAULT 0,
                        is_verified BOOLEAN DEFAULT 0,
                        recorded_by INTEGER,
                        recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        verified_at TIMESTAMP,
                        verified_by INTEGER,
                        FOREIGN KEY (monthly_plan_id) REFERENCES monthly_plans (id) ON DELETE CASCADE,
                        FOREIGN KEY (company_id) REFERENCES companies (id) ON DELETE CASCADE
                    )
                ''')
                
                # Создание таблицы ai_recommendations
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_recommendations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        monthly_plan_id INTEGER NOT NULL,
                        actual_data_id INTEGER,
                        recommendation_type TEXT,
                        category TEXT,
                        priority TEXT DEFAULT 'medium',
                        title TEXT NOT NULL,
                        description TEXT,
                        actions TEXT,
                        expected_impact TEXT,
                        expected_metric_impact REAL,
                        analysis TEXT,
                        benchmark_comparison TEXT,
                        success_metrics TEXT,
                        status TEXT DEFAULT 'pending',
                        assigned_to INTEGER,
                        due_date TIMESTAMP,
                        feedback TEXT,
                        feedback_by INTEGER,
                        feedback_at TIMESTAMP,
                        completed_at TIMESTAMP,
                        created_by INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (monthly_plan_id) REFERENCES monthly_plans (id) ON DELETE CASCADE,
                        FOREIGN KEY (actual_data_id) REFERENCES actual_data (id) ON DELETE CASCADE
                    )
                ''')
                
                # Создание таблицы benchmark_metrics
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS benchmark_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        metric_name TEXT NOT NULL,
                        metric_category TEXT NOT NULL,
                        stage TEXT NOT NULL,
                        industry TEXT,
                        poor_value REAL,
                        average_value REAL,
                        good_value REAL,
                        excellent_value REAL,
                        min_value REAL,
                        max_value REAL,
                        target_value REAL,
                        calculation_formula TEXT,
                        measurement_unit TEXT,
                        period TEXT,
                        source_name TEXT,
                        description TEXT
                    )
                ''')
                
                # Создание индексов для улучшения производительности
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_companies_user_id ON companies(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_companies_is_active ON companies(is_active)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_financial_plans_company_id ON financial_plans(company_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_financial_plans_is_active ON financial_plans(is_active)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_monthly_plans_plan_id ON monthly_plans(plan_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_actual_data_company_id ON actual_data(company_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_actual_data_month_year ON actual_data(year, month_number)')
                
                conn.commit()
                logger.info("База данных инициализирована")
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка инициализации БД: {e}")
            raise
    
    # ==================== COMPANY METHODS ====================
    
    def create_company(self, company: Company) -> int:
        """Создание новой компании"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                created_at = company.created_at or datetime.now()
                updated_at = company.updated_at or datetime.now()
                
                cursor.execute('''
                    INSERT INTO companies (
                        user_id, name, description, stage, industry, country,
                        currency, current_mrr, current_customers, monthly_price,
                        team_size, cash_balance, fiscal_year_start,
                        reporting_currency, created_at, updated_at, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    company.user_id, company.name, company.description,
                    company.stage, company.industry, company.country,
                    company.currency, company.current_mrr, company.current_customers,
                    company.monthly_price, company.team_size, company.cash_balance,
                    company.fiscal_year_start, company.reporting_currency,
                    created_at.isoformat(), updated_at.isoformat(), company.is_active
                ))
                
                company_id = cursor.lastrowid
                conn.commit()
                logger.info(f"Создана компания: {company.name} (ID: {company_id})")
                return company_id
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка создания компании: {e}")
            raise
    
    def get_company(self, company_id: int) -> Optional[Company]:
        """Получение компании по ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM companies WHERE id = ?', (company_id,))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_company(row)
                return None
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения компании: {e}")
            return None
    
    def get_company_by_user(self, user_id: int) -> Optional[Company]:
        """Получение компании пользователя"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM companies WHERE user_id = ? AND is_active = 1', (user_id,))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_company(row)
                return None
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения компании пользователя: {e}")
            return None
    
    def get_all_companies(self) -> List[Company]:
        """Получение всех активных компаний"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM companies WHERE is_active = 1 ORDER BY name')
                
                companies = []
                for row in cursor.fetchall():
                    companies.append(self._row_to_company(row))
                return companies
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения всех компаний: {e}")
            return []
    
    def update_company(self, company: Company) -> bool:
        """Обновление компании"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                updated_at = datetime.now().isoformat()
                
                cursor.execute('''
                    UPDATE companies SET
                        name = ?, description = ?, stage = ?, industry = ?,
                        country = ?, currency = ?, current_mrr = ?,
                        current_customers = ?, monthly_price = ?, team_size = ?,
                        cash_balance = ?, fiscal_year_start = ?,
                        reporting_currency = ?, updated_at = ?, is_active = ?
                    WHERE id = ?
                ''', (
                    company.name, company.description, company.stage,
                    company.industry, company.country, company.currency,
                    company.current_mrr, company.current_customers,
                    company.monthly_price, company.team_size, company.cash_balance,
                    company.fiscal_year_start, company.reporting_currency,
                    updated_at, company.is_active, company.id
                ))
                
                conn.commit()
                logger.info(f"Обновлена компания ID: {company.id}")
                return cursor.rowcount > 0
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка обновления компании: {e}")
            return False
    
    def delete_company(self, company_id: int) -> bool:
        """Удаление компании (мягкое удаление)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE companies SET is_active = 0 WHERE id = ?', (company_id,))
                conn.commit()
                logger.info(f"Удалена компания ID: {company_id}")
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Ошибка удаления компании: {e}")
            return False
    
    # ==================== FINANCIAL PLAN METHODS ====================
    
    def create_financial_plan(self, plan: FinancialPlan) -> int:
        """Создание нового финансового плана"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Сериализуем JSON поля
                assumptions_json = json.dumps(plan.assumptions) if plan.assumptions else None
                seasonality_json = json.dumps(plan.seasonality_pattern) if plan.seasonality_pattern else None
                growth_json = json.dumps(plan.growth_assumptions) if plan.growth_assumptions else None
                
                created_at = plan.created_at or datetime.now()
                updated_at = plan.updated_at or datetime.now()
                
                cursor.execute('''
                    INSERT INTO financial_plans (
                        company_id, plan_name, plan_year, version, description,
                        status, is_active, assumptions, seasonality_pattern,
                        growth_assumptions, created_by, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    plan.company_id, plan.plan_name, plan.plan_year, plan.version,
                    plan.description, plan.status, plan.is_active,
                    assumptions_json, seasonality_json, growth_json,
                    plan.created_by, created_at.isoformat(), updated_at.isoformat()
                ))
                
                plan_id = cursor.lastrowid
                conn.commit()
                logger.info(f"Создан финансовый план: {plan.plan_name} (ID: {plan_id})")
                return plan_id
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка создания финансового плана: {e}")
            raise
    
    def get_financial_plan(self, plan_id: int) -> Optional[FinancialPlan]:
        """Получение финансового плана по ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM financial_plans WHERE id = ?', (plan_id,))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_financial_plan(row)
                return None
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения финансового плана: {e}")
            return None
    
    def get_financial_plans(self, company_id: int) -> List[FinancialPlan]:
        """Получение всех финансовых планов компании (alias для совместимости)"""
        return self.get_all_financial_plans(company_id)
    
    def get_all_financial_plans(self, company_id: int) -> List[FinancialPlan]:
        """Получение всех финансовых планов компании"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM financial_plans 
                    WHERE company_id = ? 
                    ORDER BY plan_year DESC, version DESC
                ''', (company_id,))
                
                plans = []
                for row in cursor.fetchall():
                    plans.append(self._row_to_financial_plan(row))
                return plans
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения планов компании: {e}")
            return []
    
    def get_active_financial_plan(self, company_id: int) -> Optional[FinancialPlan]:
        """Получение активного финансового плана компании"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM financial_plans 
                    WHERE company_id = ? AND is_active = 1 AND status = 'active'
                    ORDER BY plan_year DESC, version DESC 
                    LIMIT 1
                ''', (company_id,))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_financial_plan(row)
                return None
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения активного плана: {e}")
            return None
    
    def activate_financial_plan(self, plan_id: int) -> bool:
        """Активация финансового плана"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Деактивируем все другие планы компании
                cursor.execute('''
                    UPDATE financial_plans SET is_active = 0 
                    WHERE company_id = (
                        SELECT company_id FROM financial_plans WHERE id = ?
                    )
                ''', (plan_id,))
                
                # Активируем выбранный план
                activated_at = datetime.now().isoformat()
                cursor.execute('''
                    UPDATE financial_plans SET 
                        is_active = 1, 
                        status = 'active',
                        activated_at = ?,
                        updated_at = ?
                    WHERE id = ?
                ''', (activated_at, activated_at, plan_id))
                
                conn.commit()
                logger.info(f"Активирован план ID: {plan_id}")
                return cursor.rowcount > 0
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка активации плана: {e}")
            return False
    
    def update_financial_plan(self, plan: FinancialPlan) -> bool:
        """Обновление финансового плана"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Сериализуем JSON поля
                assumptions_json = json.dumps(plan.assumptions) if plan.assumptions else None
                seasonality_json = json.dumps(plan.seasonality_pattern) if plan.seasonality_pattern else None
                growth_json = json.dumps(plan.growth_assumptions) if plan.growth_assumptions else None
                
                updated_at = datetime.now().isoformat()
                
                cursor.execute('''
                    UPDATE financial_plans SET
                        plan_name = ?, description = ?, status = ?,
                        is_active = ?, assumptions = ?, seasonality_pattern = ?,
                        growth_assumptions = ?, updated_at = ?
                    WHERE id = ?
                ''', (
                    plan.plan_name, plan.description, plan.status,
                    plan.is_active, assumptions_json, seasonality_json,
                    growth_json, updated_at, plan.id
                ))
                
                conn.commit()
                logger.info(f"Обновлен финансовый план ID: {plan.id}")
                return cursor.rowcount > 0
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка обновления финансового плана: {e}")
            return False
    
    def delete_financial_plan(self, plan_id: int) -> bool:
        """Удаление финансового плана"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM financial_plans WHERE id = ?', (plan_id,))
                conn.commit()
                logger.info(f"Удален финансовый план ID: {plan_id}")
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Ошибка удаления финансового плана: {e}")
            return False
    
    # ==================== MONTHLY PLAN METHODS ====================
    
    def create_monthly_plan(self, plan: MonthlyPlan) -> int:
        """Создание плана на месяц"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                created_at = plan.created_at or datetime.now()
                updated_at = plan.updated_at or datetime.now()
                
                cursor.execute('''
                    INSERT INTO monthly_plans (
                        plan_id, month_number, month_name, year, quarter,
                        plan_mrr, plan_new_customers, plan_expansion_mrr,
                        plan_churn_rate, plan_churned_mrr, plan_reactivated_mrr,
                        plan_marketing_budget, plan_sales_budget, plan_cac_target,
                        plan_salaries, plan_office_rent, plan_cloud_services,
                        plan_software_subscriptions, plan_legal_accounting,
                        plan_marketing_ops, plan_other_opex,
                        plan_capex_total, plan_capex_equipment, plan_capex_software,
                        plan_capex_furniture, plan_capex_other,
                        plan_total_revenue, plan_total_costs, plan_burn_rate,
                        plan_gross_margin, plan_runway, plan_ltv_cac_ratio,
                        plan_cac_payback_months, plan_total_customers,
                        plan_churned_customers, plan_cash_balance, plan_cac,
                        plan_ltv, is_locked, seasonality_factor,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                             ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                             ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    plan.plan_id, plan.month_number, plan.month_name, plan.year,
                    plan.quarter, plan.plan_mrr, plan.plan_new_customers,
                    plan.plan_expansion_mrr, plan.plan_churn_rate,
                    plan.plan_churned_mrr, plan.plan_reactivated_mrr,
                    plan.plan_marketing_budget, plan.plan_sales_budget,
                    plan.plan_cac_target, plan.plan_salaries, plan.plan_office_rent,
                    plan.plan_cloud_services, plan.plan_software_subscriptions,
                    plan.plan_legal_accounting, plan.plan_marketing_ops,
                    plan.plan_other_opex, plan.plan_capex_total,
                    plan.plan_capex_equipment, plan.plan_capex_software,
                    plan.plan_capex_furniture, plan.plan_capex_other,
                    plan.plan_total_revenue, plan.plan_total_costs,
                    plan.plan_burn_rate, plan.plan_gross_margin, plan.plan_runway,
                    plan.plan_ltv_cac_ratio, plan.plan_cac_payback_months,
                    plan.plan_total_customers, plan.plan_churned_customers,
                    plan.plan_cash_balance, plan.plan_cac, plan.plan_ltv,
                    plan.is_locked, plan.seasonality_factor,
                    created_at.isoformat(), updated_at.isoformat()
                ))
                
                plan_id = cursor.lastrowid
                conn.commit()
                logger.info(f"Создан месячный план: {plan.month_name} {plan.year}")
                return plan_id
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка создания месячного плана: {e}")
            raise
    
    def get_monthly_plan(self, monthly_plan_id: int) -> Optional[MonthlyPlan]:
        """Получение месячного плана по ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM monthly_plans WHERE id = ?', (monthly_plan_id,))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_monthly_plan(row)
                return None
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения месячного плана: {e}")
            return None
    
    def get_monthly_plans(self, plan_id: int) -> List[MonthlyPlan]:
        """Получение всех месячных планов для финансового плана (alias для совместимости)"""
        return self.get_all_monthly_plans(plan_id)
    
    def get_all_monthly_plans(self, plan_id: int) -> List[MonthlyPlan]:
        """Получение всех месячных планов для финансового плана"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM monthly_plans 
                    WHERE plan_id = ? 
                    ORDER BY year, month_number
                ''', (plan_id,))
                
                plans = []
                for row in cursor.fetchall():
                    plans.append(self._row_to_monthly_plan(row))
                return plans
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения месячных планов: {e}")
            return []
    
    def get_monthly_plan_by_month(self, plan_id: int, month_number: int, year: int) -> Optional[MonthlyPlan]:
        """Получение месячного плана по месяцу и году"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM monthly_plans 
                    WHERE plan_id = ? AND month_number = ? AND year = ?
                ''', (plan_id, month_number, year))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_monthly_plan(row)
                return None
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения месячного плана: {e}")
            return None
    
    def update_monthly_plan(self, plan: MonthlyPlan) -> bool:
        """Обновление месячного плана"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                updated_at = datetime.now().isoformat()
                
                cursor.execute('''
                    UPDATE monthly_plans SET
                        month_name = ?, quarter = ?,
                        plan_mrr = ?, plan_new_customers = ?, plan_expansion_mrr = ?,
                        plan_churn_rate = ?, plan_churned_mrr = ?, plan_reactivated_mrr = ?,
                        plan_marketing_budget = ?, plan_sales_budget = ?, plan_cac_target = ?,
                        plan_salaries = ?, plan_office_rent = ?, plan_cloud_services = ?,
                        plan_software_subscriptions = ?, plan_legal_accounting = ?,
                        plan_marketing_ops = ?, plan_other_opex = ?,
                        plan_capex_total = ?, plan_capex_equipment = ?, plan_capex_software = ?,
                        plan_capex_furniture = ?, plan_capex_other = ?,
                        plan_total_revenue = ?, plan_total_costs = ?, plan_burn_rate = ?,
                        plan_gross_margin = ?, plan_runway = ?, plan_ltv_cac_ratio = ?,
                        plan_cac_payback_months = ?, plan_total_customers = ?,
                        plan_churned_customers = ?, plan_cash_balance = ?, plan_cac = ?,
                        plan_ltv = ?, is_locked = ?, seasonality_factor = ?,
                        updated_at = ?
                    WHERE id = ?
                ''', (
                    plan.month_name, plan.quarter,
                    plan.plan_mrr, plan.plan_new_customers, plan.plan_expansion_mrr,
                    plan.plan_churn_rate, plan.plan_churned_mrr, plan.plan_reactivated_mrr,
                    plan.plan_marketing_budget, plan.plan_sales_budget, plan.plan_cac_target,
                    plan.plan_salaries, plan.plan_office_rent, plan.plan_cloud_services,
                    plan.plan_software_subscriptions, plan.plan_legal_accounting,
                    plan.plan_marketing_ops, plan.plan_other_opex,
                    plan.plan_capex_total, plan.plan_capex_equipment, plan.plan_capex_software,
                    plan.plan_capex_furniture, plan.plan_capex_other,
                    plan.plan_total_revenue, plan.plan_total_costs, plan.plan_burn_rate,
                    plan.plan_gross_margin, plan.plan_runway, plan.plan_ltv_cac_ratio,
                    plan.plan_cac_payback_months, plan.plan_total_customers,
                    plan.plan_churned_customers, plan.plan_cash_balance, plan.plan_cac,
                    plan.plan_ltv, plan.is_locked, plan.seasonality_factor,
                    updated_at, plan.id
                ))
                
                conn.commit()
                logger.info(f"Обновлен месячный план ID: {plan.id}")
                return cursor.rowcount > 0
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка обновления месячного плана: {e}")
            return False
    
    def lock_monthly_plan(self, monthly_plan_id: int, lock: bool = True) -> bool:
        """Блокировка/разблокировка месячного плана"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE monthly_plans SET is_locked = ? WHERE id = ?', (lock, monthly_plan_id))
                conn.commit()
                logger.info(f"План ID {monthly_plan_id} {'заблокирован' if lock else 'разблокирован'}")
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Ошибка блокировки плана: {e}")
            return False
    
    # ==================== ACTUAL DATA METHODS ====================
    
    def save_actual_data(self, data: ActualData) -> int:
        """Сохранение фактических данных"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                recorded_at = data.recorded_at or datetime.now()
                
                # Проверяем, существует ли уже запись для этой компании и месяца
                if data.company_id and data.month_number and data.year:
                    cursor.execute('''
                        SELECT id FROM actual_data 
                        WHERE company_id = ? AND month_number = ? AND year = ?
                    ''', (data.company_id, data.month_number, data.year))
                    
                    existing = cursor.fetchone()
                elif data.monthly_plan_id:
                    cursor.execute('SELECT id FROM actual_data WHERE monthly_plan_id = ?', (data.monthly_plan_id,))
                    existing = cursor.fetchone()
                else:
                    existing = None
                
                if existing:
                    # Обновляем существующие данные
                    actual_id = existing['id']
                    
                    cursor.execute('''
                        UPDATE actual_data SET
                            actual_mrr = ?, actual_new_customers = ?, actual_expansion_mrr = ?,
                            actual_churn_rate = ?, actual_churned_mrr = ?,
                            actual_marketing_spent = ?, actual_sales_spent = ?, actual_cac = ?,
                            actual_salaries = ?, actual_office_rent = ?, actual_cloud_services = ?,
                            actual_software_subscriptions = ?, actual_legal_accounting = ?,
                            actual_marketing_ops = ?, actual_other_opex = ?,
                            actual_capex_spent = ?, actual_capex_equipment = ?,
                            actual_capex_software = ?, actual_capex_furniture = ?, actual_capex_other = ?,
                            actual_total_revenue = ?, actual_total_costs = ?, actual_burn_rate = ?,
                            actual_gross_margin = ?, actual_runway = ?, actual_ltv_cac_ratio = ?,
                            actual_cac_payback_months = ?,
                            variance_mrr = ?, variance_burn_rate = ?, variance_runway = ?,
                            variance_cac = ?, variance_new_customers = ?,
                            actual_churned_customers = ?, actual_total_customers = ?,
                            actual_cash_balance = ?, actual_ltv = ?,
                            data_source = ?, import_file = ?, notes = ?,
                            is_finalized = ?, is_verified = ?, recorded_by = ?,
                            recorded_at = ?
                        WHERE id = ?
                    ''', (
                        data.actual_mrr, data.actual_new_customers, data.actual_expansion_mrr,
                        data.actual_churn_rate, data.actual_churned_mrr,
                        data.actual_marketing_spent, data.actual_sales_spent, data.actual_cac,
                        data.actual_salaries, data.actual_office_rent, data.actual_cloud_services,
                        data.actual_software_subscriptions, data.actual_legal_accounting,
                        data.actual_marketing_ops, data.actual_other_opex,
                        data.actual_capex_spent, data.actual_capex_equipment,
                        data.actual_capex_software, data.actual_capex_furniture, data.actual_capex_other,
                        data.actual_total_revenue, data.actual_total_costs, data.actual_burn_rate,
                        data.actual_gross_margin, data.actual_runway, data.actual_ltv_cac_ratio,
                        data.actual_cac_payback_months,
                        data.variance_mrr, data.variance_burn_rate, data.variance_runway,
                        data.variance_cac, data.variance_new_customers,
                        data.actual_churned_customers, data.actual_total_customers,
                        data.actual_cash_balance, data.actual_ltv,
                        data.data_source, data.import_file, data.notes,
                        data.is_finalized, data.is_verified, data.recorded_by,
                        recorded_at.isoformat(), actual_id
                    ))
                    
                    logger.info(f"Обновлены фактические данные ID: {actual_id}")
                    
                else:
                    # Создаем новые данные
                    cursor.execute('''
                        INSERT INTO actual_data (
                            monthly_plan_id, company_id, year, month_number,
                            actual_mrr, actual_new_customers, actual_expansion_mrr,
                            actual_churn_rate, actual_churned_mrr,
                            actual_marketing_spent, actual_sales_spent, actual_cac,
                            actual_salaries, actual_office_rent, actual_cloud_services,
                            actual_software_subscriptions, actual_legal_accounting,
                            actual_marketing_ops, actual_other_opex,
                            actual_capex_spent, actual_capex_equipment,
                            actual_capex_software, actual_capex_furniture, actual_capex_other,
                            actual_total_revenue, actual_total_costs, actual_burn_rate,
                            actual_gross_margin, actual_runway, actual_ltv_cac_ratio,
                            actual_cac_payback_months,
                            variance_mrr, variance_burn_rate, variance_runway,
                            variance_cac, variance_new_customers,
                            actual_churned_customers, actual_total_customers,
                            actual_cash_balance, actual_ltv,
                            data_source, import_file, notes,
                            is_finalized, is_verified, recorded_by, recorded_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                                 ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                                 ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        data.monthly_plan_id, data.company_id, data.year, data.month_number,
                        data.actual_mrr, data.actual_new_customers, data.actual_expansion_mrr,
                        data.actual_churn_rate, data.actual_churned_mrr,
                        data.actual_marketing_spent, data.actual_sales_spent, data.actual_cac,
                        data.actual_salaries, data.actual_office_rent, data.actual_cloud_services,
                        data.actual_software_subscriptions, data.actual_legal_accounting,
                        data.actual_marketing_ops, data.actual_other_opex,
                        data.actual_capex_spent, data.actual_capex_equipment,
                        data.actual_capex_software, data.actual_capex_furniture, data.actual_capex_other,
                        data.actual_total_revenue, data.actual_total_costs, data.actual_burn_rate,
                        data.actual_gross_margin, data.actual_runway, data.actual_ltv_cac_ratio,
                        data.actual_cac_payback_months,
                        data.variance_mrr, data.variance_burn_rate, data.variance_runway,
                        data.variance_cac, data.variance_new_customers,
                        data.actual_churned_customers, data.actual_total_customers,
                        data.actual_cash_balance, data.actual_ltv,
                        data.data_source, data.import_file, data.notes,
                        data.is_finalized, data.is_verified, data.recorded_by,
                        recorded_at.isoformat()
                    ))
                    
                    actual_id = cursor.lastrowid
                    logger.info(f"Созданы фактические данные ID: {actual_id}")
                
                conn.commit()
                return actual_id if 'actual_id' in locals() else existing['id']
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка сохранения фактических данных: {e}")
            raise
    
    def create_actual_financial(self, actual_financial: ActualData) -> int:
        """Создание фактических данных (alias для save_actual_data для совместимости)"""
        return self.save_actual_data(actual_financial)
    
    def get_actual_data(self, monthly_plan_id: int) -> Optional[ActualData]:
        """Получение фактических данных по ID месячного плана"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM actual_data WHERE monthly_plan_id = ?', (monthly_plan_id,))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_actual_data(row)
                return None
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения фактических данных: {e}")
            return None
    
    def get_actual_data_by_id(self, actual_data_id: int) -> Optional[ActualData]:
        """Получение фактических данных по ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM actual_data WHERE id = ?', (actual_data_id,))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_actual_data(row)
                return None
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения фактических данных: {e}")
            return None
    
    def get_actual_financials_by_filters(self, filters: Dict) -> List[ActualData]:
        """Получение фактических данных по фильтрам"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = '''
                SELECT ad.* FROM actual_data ad
                WHERE 1=1
                '''
                params = []
                
                if 'company_id' in filters:
                    query += ' AND ad.company_id = ?'
                    params.append(filters['company_id'])
                
                if 'year' in filters:
                    query += ' AND ad.year = ?'
                    params.append(filters['year'])
                
                if 'month_number' in filters:
                    query += ' AND ad.month_number = ?'
                    params.append(filters['month_number'])
                
                if 'is_finalized' in filters:
                    query += ' AND ad.is_finalized = ?'
                    params.append(filters['is_finalized'])
                
                query += ' ORDER BY ad.year DESC, ad.month_number DESC'
                
                cursor.execute(query, params)
                
                actuals = []
                for row in cursor.fetchall():
                    actuals.append(self._row_to_actual_data(row))
                return actuals
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения фактических данных: {e}")
            return []
    
    def update_actual_financial(self, actual_financial: ActualData) -> bool:
        """Обновление фактических данных"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                updated_at = datetime.now().isoformat()
                
                cursor.execute('''
                    UPDATE actual_data SET
                        actual_mrr = ?, actual_new_customers = ?, 
                        actual_expansion_mrr = ?, actual_churn_rate = ?,
                        actual_churned_mrr = ?, actual_marketing_spent = ?,
                        actual_sales_spent = ?, actual_cac = ?,
                        actual_salaries = ?, actual_office_rent = ?,
                        actual_cloud_services = ?, actual_software_subscriptions = ?,
                        actual_legal_accounting = ?, actual_marketing_ops = ?,
                        actual_other_opex = ?, actual_capex_spent = ?,
                        actual_capex_equipment = ?, actual_capex_software = ?,
                        actual_capex_furniture = ?, actual_capex_other = ?,
                        actual_total_revenue = ?, actual_total_costs = ?,
                        actual_burn_rate = ?, actual_gross_margin = ?,
                        actual_runway = ?, actual_ltv_cac_ratio = ?,
                        actual_cac_payback_months = ?, variance_mrr = ?,
                        variance_burn_rate = ?, variance_runway = ?,
                        variance_cac = ?, variance_new_customers = ?,
                        actual_churned_customers = ?, actual_total_customers = ?,
                        actual_cash_balance = ?, actual_ltv = ?,
                        data_source = ?, import_file = ?, notes = ?,
                        is_finalized = ?, is_verified = ?, recorded_by = ?,
                        recorded_at = ?, verified_at = ?, verified_by = ?
                    WHERE id = ?
                ''', (
                    actual_financial.actual_mrr, actual_financial.actual_new_customers,
                    actual_financial.actual_expansion_mrr, actual_financial.actual_churn_rate,
                    actual_financial.actual_churned_mrr, actual_financial.actual_marketing_spent,
                    actual_financial.actual_sales_spent, actual_financial.actual_cac,
                    actual_financial.actual_salaries, actual_financial.actual_office_rent,
                    actual_financial.actual_cloud_services, actual_financial.actual_software_subscriptions,
                    actual_financial.actual_legal_accounting, actual_financial.actual_marketing_ops,
                    actual_financial.actual_other_opex, actual_financial.actual_capex_spent,
                    actual_financial.actual_capex_equipment, actual_financial.actual_capex_software,
                    actual_financial.actual_capex_furniture, actual_financial.actual_capex_other,
                    actual_financial.actual_total_revenue, actual_financial.actual_total_costs,
                    actual_financial.actual_burn_rate, actual_financial.actual_gross_margin,
                    actual_financial.actual_runway, actual_financial.actual_ltv_cac_ratio,
                    actual_financial.actual_cac_payback_months, actual_financial.variance_mrr,
                    actual_financial.variance_burn_rate, actual_financial.variance_runway,
                    actual_financial.variance_cac, actual_financial.variance_new_customers,
                    actual_financial.actual_churned_customers, actual_financial.actual_total_customers,
                    actual_financial.actual_cash_balance, actual_financial.actual_ltv,
                    actual_financial.data_source, actual_financial.import_file,
                    actual_financial.notes, actual_financial.is_finalized,
                    actual_financial.is_verified, actual_financial.recorded_by,
                    actual_financial.recorded_at.isoformat() if actual_financial.recorded_at else None,
                    actual_financial.verified_at.isoformat() if actual_financial.verified_at else None,
                    actual_financial.verified_by, actual_financial.id
                ))
                
                conn.commit()
                logger.info(f"Обновлены фактические данные ID: {actual_financial.id}")
                return cursor.rowcount > 0
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка обновления фактических данных: {e}")
            return False
    
    def finalize_actual_data(self, monthly_plan_id: int) -> bool:
        """Финализация фактических данных за месяц"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                finalized_at = datetime.now().isoformat()
                cursor.execute('''
                    UPDATE actual_data SET 
                        is_finalized = 1,
                        recorded_at = ?
                    WHERE monthly_plan_id = ?
                ''', (finalized_at, monthly_plan_id))
                conn.commit()
                logger.info(f"Финализированы данные для плана ID: {monthly_plan_id}")
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Ошибка финализации данных: {e}")
            return False
    
    # ==================== ANALYTICS METHODS ====================
    
    def get_plan_vs_actual_summary(self, plan_id: int) -> pd.DataFrame:
        """Сводка план vs факт для всех месяцев плана"""
        try:
            with self.get_connection() as conn:
                query = '''
                SELECT 
                    mp.month_number,
                    mp.month_name,
                    mp.year,
                    mp.plan_mrr,
                    ad.actual_mrr,
                    mp.plan_burn_rate,
                    ad.actual_burn_rate,
                    mp.plan_runway,
                    ad.actual_runway,
                    mp.plan_cac_target,
                    ad.actual_cac,
                    mp.plan_new_customers,
                    ad.actual_new_customers,
                    ad.variance_mrr,
                    ad.variance_burn_rate,
                    ad.variance_runway,
                    ad.variance_cac,
                    ad.variance_new_customers,
                    CASE 
                        WHEN ad.actual_mrr IS NULL THEN 'planned'
                        WHEN ad.is_finalized = 1 THEN 'finalized'
                        ELSE 'in_progress'
                    END as status
                FROM monthly_plans mp
                LEFT JOIN actual_data ad ON mp.id = ad.monthly_plan_id
                WHERE mp.plan_id = ?
                ORDER BY mp.year, mp.month_number
                '''
                
                df = pd.read_sql_query(query, conn, params=(plan_id,))
                return df
                
        except Exception as e:
            logger.error(f"Ошибка получения сводки: {e}")
            return pd.DataFrame()
    
    def get_financial_health_score(self, company_id: int) -> Dict:
        """Расчет оценки финансового здоровья компании"""
        try:
            # Получаем активный план
            active_plan = self.get_active_financial_plan(company_id)
            if not active_plan:
                return {'score': 0, 'level': 'no_data', 'message': 'Нет активного плана'}
            
            # Получаем все месячные данные
            monthly_plans = self.get_all_monthly_plans(active_plan.id)
            if not monthly_plans:
                return {'score': 0, 'level': 'no_data', 'message': 'Нет данных по месяцам'}
            
            # Получаем последние фактические данные
            latest_actual = None
            for mp in reversed(monthly_plans):
                actual = self.get_actual_data(mp.id)
                if actual and actual.is_finalized:
                    latest_actual = actual
                    break
            
            if not latest_actual:
                return {'score': 0, 'level': 'no_data', 'message': 'Нет фактических данных'}
            
            # Рассчитываем score
            score = 100
            issues = []
            strengths = []
            
            # 1. Оценка по Runway (30%)
            if latest_actual.actual_runway < 3:
                score -= 30
                issues.append('⚠️ Критически низкий runway (<3 месяцев)')
            elif latest_actual.actual_runway < 6:
                score -= 20
                issues.append('⚠️ Низкий runway (<6 месяцев)')
            elif latest_actual.actual_runway < 12:
                score -= 10
                issues.append('⚠️ Умеренный runway (<12 месяцев)')
            elif latest_actual.actual_runway >= 18:
                score += 10
                strengths.append('✅ Отличный runway (≥18 месяцев)')
            
            # 2. Оценка по отклонению MRR (25%)
            if latest_actual.variance_mrr < -0.3:
                score -= 25
                issues.append(f'⚠️ Сильное отставание по MRR ({latest_actual.variance_mrr*100:.1f}%)')
            elif latest_actual.variance_mrr < -0.2:
                score -= 15
                issues.append(f'⚠️ Значительное отставание по MRR ({latest_actual.variance_mrr*100:.1f}%)')
            elif latest_actual.variance_mrr < -0.1:
                score -= 5
                issues.append(f'⚠️ Небольшое отставание по MRR ({latest_actual.variance_mrr*100:.1f}%)')
            elif latest_actual.variance_mrr > 0.2:
                score += 10
                strengths.append(f'✅ Значительное опережение по MRR (+{latest_actual.variance_mrr*100:.1f}%)')
            
            # 3. Оценка по Burn Rate (20%)
            if latest_actual.variance_burn_rate > 0.3:
                score -= 20
                issues.append(f'⚠️ Сильное превышение burn rate ({latest_actual.variance_burn_rate*100:.1f}%)')
            elif latest_actual.variance_burn_rate > 0.2:
                score -= 10
                issues.append(f'⚠️ Значительное превышение burn rate ({latest_actual.variance_burn_rate*100:.1f}%)')
            elif latest_actual.variance_burn_rate < -0.2:
                score += 5
                strengths.append(f'✅ Экономия по burn rate ({latest_actual.variance_burn_rate*100:.1f}%)')
            
            # 4. Оценка по CAC (15%)
            if latest_actual.variance_cac > 0.4:
                score -= 15
                issues.append(f'⚠️ Высокий CAC относительно цели ({latest_actual.variance_cac*100:.1f}%)')
            elif latest_actual.variance_cac > 0.2:
                score -= 8
                issues.append(f'⚠️ CAC выше цели ({latest_actual.variance_cac*100:.1f}%)')
            elif latest_actual.variance_cac < -0.2:
                score += 5
                strengths.append(f'✅ Низкий CAC относительно цели ({latest_actual.variance_cac*100:.1f}%)')
            
            # 5. Оценка по новым клиентам (10%)
            if latest_actual.variance_new_customers < -0.3:
                score -= 10
                issues.append(f'⚠️ Сильное отставание по новым клиентам ({latest_actual.variance_new_customers*100:.1f}%)')
            elif latest_actual.variance_new_customers < -0.1:
                score -= 5
                issues.append(f'⚠️ Отставание по новым клиентам ({latest_actual.variance_new_customers*100:.1f}%)')
            elif latest_actual.variance_new_customers > 0.2:
                score += 5
                strengths.append(f'✅ Превышение по новым клиентам (+{latest_actual.variance_new_customers*100:.1f}%)')
            
            # Ограничиваем score
            score = max(0, min(100, score))
            
            # Определяем уровень
            if score >= 80:
                level = 'excellent'
                level_text = 'Отлично'
                color = 'green'
            elif score >= 60:
                level = 'good'
                level_text = 'Хорошо'
                color = 'blue'
            elif score >= 40:
                level = 'fair'
                level_text = 'Удовлетворительно'
                color = 'orange'
            else:
                level = 'poor'
                level_text = 'Требует внимания'
                color = 'red'
            
            return {
                'score': round(score, 1),
                'level': level,
                'level_text': level_text,
                'color': color,
                'issues': issues,
                'strengths': strengths,
                'last_month_analyzed': latest_actual.recorded_at.date() if latest_actual.recorded_at else None,
                'runway': latest_actual.actual_runway,
                'mrr_variance': latest_actual.variance_mrr,
                'burn_rate_variance': latest_actual.variance_burn_rate,
                'cac_variance': latest_actual.variance_cac,
                'calculated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Ошибка расчета health score: {e}")
            return {'score': 0, 'level': 'error', 'message': str(e)}
    
    # ==================== UTILITY METHODS ====================
    
    def export_to_excel(self, plan_id: int, file_path: str) -> bool:
        """Экспорт всех данных плана в Excel"""
        try:
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                # 1. Company Information
                plan = self.get_financial_plan(plan_id)
                if plan:
                    company = self.get_company(plan.company_id)
                    if company:
                        company_df = pd.DataFrame([asdict(company)])
                        company_df.to_excel(writer, sheet_name='Компания', index=False)
                
                # 2. Plan Summary
                summary_df = self.get_plan_vs_actual_summary(plan_id)
                if not summary_df.empty:
                    summary_df.to_excel(writer, sheet_name='Сводка', index=False)
                
                # 3. Monthly Plans
                monthly_plans = self.get_all_monthly_plans(plan_id)
                if monthly_plans:
                    monthly_df = pd.DataFrame([asdict(mp) for mp in monthly_plans])
                    monthly_df.to_excel(writer, sheet_name='Планы', index=False)
                
                logger.info(f"Экспорт завершен: {file_path}")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка экспорта в Excel: {e}")
            return False
    
    def backup_database(self, backup_path: str) -> bool:
        """Создание резервной копии базы данных"""
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Резервная копия создана: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Ошибка создания резервной копии: {e}")
            return False
    
    # ==================== HELPER METHODS ====================
    
    def _row_to_company(self, row) -> Company:
        """Преобразование строки БД в объект Company"""
        return Company(
            id=row['id'],
            user_id=row['user_id'],
            name=row['name'],
            description=row['description'],
            stage=row['stage'],
            industry=row['industry'],
            country=row['country'],
            currency=row['currency'],
            current_mrr=row['current_mrr'],
            current_customers=row['current_customers'],
            monthly_price=row['monthly_price'],
            team_size=row['team_size'],
            cash_balance=row['cash_balance'],
            fiscal_year_start=row['fiscal_year_start'],
            reporting_currency=row['reporting_currency'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None,
            is_active=bool(row['is_active'])
        )
    
    def _row_to_financial_plan(self, row) -> FinancialPlan:
        """Преобразование строки БД в объект FinancialPlan"""
        return FinancialPlan(
            id=row['id'],
            company_id=row['company_id'],
            plan_name=row['plan_name'],
            plan_year=row['plan_year'],
            version=row['version'],
            description=row['description'],
            status=row['status'],
            is_active=bool(row['is_active']),
            assumptions=json.loads(row['assumptions']) if row['assumptions'] else None,
            seasonality_pattern=json.loads(row['seasonality_pattern']) if row['seasonality_pattern'] else None,
            growth_assumptions=json.loads(row['growth_assumptions']) if row['growth_assumptions'] else None,
            created_by=row['created_by'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None,
            activated_at=datetime.fromisoformat(row['activated_at']) if row['activated_at'] else None
        )
    
    def _row_to_monthly_plan(self, row) -> MonthlyPlan:
        """Преобразование строки БД в объект MonthlyPlan"""
        row_keys = set(row.keys())
        return MonthlyPlan(
            id=row['id'],
            plan_id=row['plan_id'],
            month_number=row['month_number'],
            month_name=row['month_name'],
            year=row['year'],
            quarter=row['quarter'],
            plan_mrr=row['plan_mrr'],
            plan_new_customers=row['plan_new_customers'],
            plan_expansion_mrr=row['plan_expansion_mrr'],
            plan_churn_rate=row['plan_churn_rate'],
            plan_churned_mrr=row['plan_churned_mrr'],
            plan_reactivated_mrr=row['plan_reactivated_mrr'],
            plan_marketing_budget=row['plan_marketing_budget'],
            plan_sales_budget=row['plan_sales_budget'],
            plan_cac_target=row['plan_cac_target'],
            plan_salaries=row['plan_salaries'],
            plan_office_rent=row['plan_office_rent'],
            plan_cloud_services=row['plan_cloud_services'],
            plan_software_subscriptions=row['plan_software_subscriptions'],
            plan_legal_accounting=row['plan_legal_accounting'],
            plan_marketing_ops=row['plan_marketing_ops'],
            plan_other_opex=row['plan_other_opex'],
            plan_capex_total=row['plan_capex_total'],
            plan_capex_equipment=row['plan_capex_equipment'],
            plan_capex_software=row['plan_capex_software'],
            plan_capex_furniture=row['plan_capex_furniture'],
            plan_capex_other=row['plan_capex_other'],
            plan_total_revenue=row['plan_total_revenue'],
            plan_total_costs=row['plan_total_costs'],
            plan_burn_rate=row['plan_burn_rate'],
            plan_gross_margin=row['plan_gross_margin'],
            plan_runway=row['plan_runway'],
            plan_ltv_cac_ratio=row['plan_ltv_cac_ratio'],
            plan_cac_payback_months=row['plan_cac_payback_months'],
            plan_total_customers=row['plan_total_customers'] if 'plan_total_customers' in row_keys else 0,
            plan_churned_customers=row['plan_churned_customers'] if 'plan_churned_customers' in row_keys else 0,
            plan_cash_balance=row['plan_cash_balance'] if 'plan_cash_balance' in row_keys else 0.0,
            plan_cac=row['plan_cac'] if 'plan_cac' in row_keys else 0.0,
            plan_ltv=row['plan_ltv'] if 'plan_ltv' in row_keys else 0.0,
            is_locked=bool(row['is_locked']),
            seasonality_factor=row['seasonality_factor'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
        )
    
    def _row_to_actual_data(self, row) -> ActualData:
        """Преобразование строки БД в объект ActualData"""
        row_keys = set(row.keys())
        return ActualData(
            id=row['id'],
            monthly_plan_id=row['monthly_plan_id'],
            company_id=row['company_id'],
            year=row['year'],
            month_number=row['month_number'],
            actual_mrr=row['actual_mrr'],
            actual_new_customers=row['actual_new_customers'],
            actual_expansion_mrr=row['actual_expansion_mrr'],
            actual_churn_rate=row['actual_churn_rate'],
            actual_churned_mrr=row['actual_churned_mrr'],
            actual_marketing_spent=row['actual_marketing_spent'],
            actual_sales_spent=row['actual_sales_spent'],
            actual_cac=row['actual_cac'],
            actual_salaries=row['actual_salaries'],
            actual_office_rent=row['actual_office_rent'],
            actual_cloud_services=row['actual_cloud_services'],
            actual_software_subscriptions=row['actual_software_subscriptions'],
            actual_legal_accounting=row['actual_legal_accounting'],
            actual_marketing_ops=row['actual_marketing_ops'],
            actual_other_opex=row['actual_other_opex'],
            actual_capex_spent=row['actual_capex_spent'],
            actual_capex_equipment=row['actual_capex_equipment'],
            actual_capex_software=row['actual_capex_software'],
            actual_capex_furniture=row['actual_capex_furniture'],
            actual_capex_other=row['actual_capex_other'],
            actual_total_revenue=row['actual_total_revenue'],
            actual_total_costs=row['actual_total_costs'],
            actual_burn_rate=row['actual_burn_rate'],
            actual_gross_margin=row['actual_gross_margin'],
            actual_runway=row['actual_runway'],
            actual_ltv_cac_ratio=row['actual_ltv_cac_ratio'],
            actual_cac_payback_months=row['actual_cac_payback_months'],
            variance_mrr=row['variance_mrr'],
            variance_burn_rate=row['variance_burn_rate'],
            variance_runway=row['variance_runway'],
            variance_cac=row['variance_cac'],
            variance_new_customers=row['variance_new_customers'],
            actual_churned_customers=row['actual_churned_customers'] if 'actual_churned_customers' in row_keys else 0,
            actual_total_customers=row['actual_total_customers'] if 'actual_total_customers' in row_keys else 0,
            actual_cash_balance=row['actual_cash_balance'] if 'actual_cash_balance' in row_keys else 0.0,
            actual_ltv=row['actual_ltv'] if 'actual_ltv' in row_keys else 0.0,
            data_source=row['data_source'],
            import_file=row['import_file'],
            notes=row['notes'],
            is_finalized=bool(row['is_finalized']),
            is_verified=bool(row['is_verified']),
            recorded_by=row['recorded_by'],
            recorded_at=datetime.fromisoformat(row['recorded_at']) if row['recorded_at'] else None,
            verified_at=datetime.fromisoformat(row['verified_at']) if row['verified_at'] else None,
            verified_by=row['verified_by']
        )
@dataclass
class VarianceAnalysisResult:
    """Результат анализа отклонений для совместимости с app.py"""
    variance_summary: Dict = None
    significant_variances: List[Dict] = None
    detailed_variance: List[Dict] = None
    variance_score: float = 0.0
    overall_performance: str = "unknown"
    
    def __post_init__(self):
        if self.variance_summary is None:
            self.variance_summary = {}
        if self.significant_variances is None:
            self.significant_variances = []
        if self.detailed_variance is None:
            self.detailed_variance = []
    
    def to_dict(self):
        return {
            'variance_summary': self.variance_summary,
            'significant_variances': self.significant_variances,
            'detailed_variance': self.detailed_variance,
            'variance_score': self.variance_score,
            'overall_performance': self.overall_performance
        }

# Создаем глобальный экземпляр менеджера БД
db_manager = DatabaseManager()

# Алиас для обратной совместимости
ActualFinancial = ActualData
