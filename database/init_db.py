"""
Инициализация базы данных SQLite для SaaS Financial Planning System
"""

import sqlite3
import os
import json
from datetime import datetime
from pathlib import Path

def init_database(db_path: str = 'database/saas_finance.db'):
    """Инициализация базы данных с созданием всех таблиц"""

    from database.path_utils import resolve_db_path

    resolved_path = resolve_db_path(db_path)

    # Создаем директорию если не существует
    os.makedirs(resolved_path.parent, exist_ok=True)

    conn = sqlite3.connect(resolved_path)
    cursor = conn.cursor()
    
    # Включаем foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # Таблица пользователей (для будущей аутентификации)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE,
        role TEXT DEFAULT 'user',  -- user, admin, viewer
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Таблица компаний/стартапов
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT NOT NULL,
        description TEXT,
        stage TEXT NOT NULL,  -- pre_seed, seed, series_a, series_b
        industry TEXT,
        country TEXT,
        currency TEXT DEFAULT 'RUB',
        
        -- Текущие метрики
        current_mrr REAL DEFAULT 0,
        current_customers INTEGER DEFAULT 0,
        monthly_price REAL DEFAULT 0,
        team_size INTEGER DEFAULT 1,
        cash_balance REAL DEFAULT 0,
        
        -- Настройки
        fiscal_year_start INTEGER DEFAULT 1,  -- 1 = Январь
        reporting_currency TEXT DEFAULT 'RUB',
        
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT 1,
        
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Таблица финансовых планов (годовые планы)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS financial_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        plan_name TEXT NOT NULL,
        plan_year INTEGER NOT NULL,
        version INTEGER DEFAULT 1,
        description TEXT,
        
        -- Статус
        status TEXT DEFAULT 'draft',  -- draft, active, archived, completed
        is_active BOOLEAN DEFAULT 0,
        
        -- Метаданные
        assumptions TEXT,  -- JSON с допущениями
        seasonality_pattern TEXT,  -- JSON с сезонностью
        growth_assumptions TEXT,  -- JSON с допущениями роста
        
        created_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        activated_at TIMESTAMP,
        
        FOREIGN KEY (company_id) REFERENCES companies (id),
        FOREIGN KEY (created_by) REFERENCES users (id),
        UNIQUE(company_id, plan_year, version)
    )
    ''')
    
    # Таблица месячных планов
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS monthly_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plan_id INTEGER NOT NULL,
        
        -- Идентификация месяца
        month_number INTEGER NOT NULL,  -- 1-12
        month_name TEXT,
        year INTEGER NOT NULL,
        quarter INTEGER,
        
        -- REVENUE (ВЫРУЧКА)
        plan_mrr REAL DEFAULT 0,
        plan_new_customers INTEGER DEFAULT 0,
        plan_expansion_mrr REAL DEFAULT 0,  -- Upsell/Cross-sell
        plan_churn_rate REAL DEFAULT 0.05,  -- 5% по умолчанию
        plan_churned_mrr REAL DEFAULT 0,
        plan_reactivated_mrr REAL DEFAULT 0,
        
        -- CAC (Customer Acquisition Cost)
        plan_marketing_budget REAL DEFAULT 0,
        plan_sales_budget REAL DEFAULT 0,
        plan_cac_target REAL DEFAULT 0,
        
        -- OPEX (Операционные расходы)
        plan_salaries REAL DEFAULT 0,
        plan_office_rent REAL DEFAULT 0,
        plan_cloud_services REAL DEFAULT 0,
        plan_software_subscriptions REAL DEFAULT 0,
        plan_legal_accounting REAL DEFAULT 0,
        plan_marketing_ops REAL DEFAULT 0,
        plan_other_opex REAL DEFAULT 0,
        
        -- CAPEX (Капитальные расходы)
        plan_capex_total REAL DEFAULT 0,
        plan_capex_equipment REAL DEFAULT 0,
        plan_capex_software REAL DEFAULT 0,
        plan_capex_furniture REAL DEFAULT 0,
        plan_capex_other REAL DEFAULT 0,
        
        -- ИТОГОВЫЕ МЕТРИКИ
        plan_total_revenue REAL DEFAULT 0,
        plan_total_costs REAL DEFAULT 0,
        plan_burn_rate REAL DEFAULT 0,
        plan_gross_margin REAL DEFAULT 0,
        plan_runway REAL DEFAULT 0,
        plan_ltv_cac_ratio REAL DEFAULT 0,
        plan_cac_payback_months REAL DEFAULT 0,

        -- Дополнительные поля для совместимости
        plan_total_customers INTEGER DEFAULT 0,
        plan_churned_customers INTEGER DEFAULT 0,
        plan_cash_balance REAL DEFAULT 0,
        plan_cac REAL DEFAULT 0,
        plan_ltv REAL DEFAULT 0,
        
        -- ФЛАГИ И СТАТУСЫ
        is_locked BOOLEAN DEFAULT 0,  -- Заблокирован для изменений
        seasonality_factor REAL DEFAULT 1.0,
        
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        FOREIGN KEY (plan_id) REFERENCES financial_plans (id),
        UNIQUE(plan_id, month_number, year)
    )
    ''')
    
    # Таблица фактических данных
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS actual_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        monthly_plan_id INTEGER,
        company_id INTEGER,
        year INTEGER NOT NULL,
        month_number INTEGER NOT NULL,
        
        -- REVENUE ACTUAL
        actual_mrr REAL DEFAULT 0,
        actual_new_customers INTEGER DEFAULT 0,
        actual_expansion_mrr REAL DEFAULT 0,
        actual_churn_rate REAL DEFAULT 0,
        actual_churned_mrr REAL DEFAULT 0,
        
        -- CAC ACTUAL
        actual_marketing_spent REAL DEFAULT 0,
        actual_sales_spent REAL DEFAULT 0,
        actual_cac REAL DEFAULT 0,
        
        -- OPEX ACTUAL
        actual_salaries REAL DEFAULT 0,
        actual_office_rent REAL DEFAULT 0,
        actual_cloud_services REAL DEFAULT 0,
        actual_software_subscriptions REAL DEFAULT 0,
        actual_legal_accounting REAL DEFAULT 0,
        actual_marketing_ops REAL DEFAULT 0,
        actual_other_opex REAL DEFAULT 0,
        
        -- CAPEX ACTUAL
        actual_capex_spent REAL DEFAULT 0,
        actual_capex_equipment REAL DEFAULT 0,
        actual_capex_software REAL DEFAULT 0,
        actual_capex_furniture REAL DEFAULT 0,
        actual_capex_other REAL DEFAULT 0,
        
        -- CALCULATED METRICS
        actual_total_revenue REAL DEFAULT 0,
        actual_total_costs REAL DEFAULT 0,
        actual_burn_rate REAL DEFAULT 0,
        actual_gross_margin REAL DEFAULT 0,
        actual_runway REAL DEFAULT 0,
        actual_ltv_cac_ratio REAL DEFAULT 0,
        actual_cac_payback_months REAL DEFAULT 0,
        
        -- VARIANCE CALCULATIONS
        variance_mrr REAL DEFAULT 0,
        variance_burn_rate REAL DEFAULT 0,
        variance_runway REAL DEFAULT 0,
        variance_cac REAL DEFAULT 0,
        variance_new_customers REAL DEFAULT 0,

        -- Дополнительные поля для совместимости
        actual_churned_customers INTEGER DEFAULT 0,
        actual_total_customers INTEGER DEFAULT 0,
        actual_cash_balance REAL DEFAULT 0,
        actual_ltv REAL DEFAULT 0,
        
        -- МЕТАДАННЫЕ
        data_source TEXT DEFAULT 'manual',  -- manual, excel, api
        import_file TEXT,
        notes TEXT,
        is_finalized BOOLEAN DEFAULT 0,
        is_verified BOOLEAN DEFAULT 0,
        
        recorded_by INTEGER,
        recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        verified_at TIMESTAMP,
        verified_by INTEGER,
        
        FOREIGN KEY (monthly_plan_id) REFERENCES monthly_plans (id),
        FOREIGN KEY (company_id) REFERENCES companies (id),
        FOREIGN KEY (recorded_by) REFERENCES users (id),
        FOREIGN KEY (verified_by) REFERENCES users (id)
    )
    ''')
    
    # Таблица AI рекомендаций
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ai_recommendations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        monthly_plan_id INTEGER,
        actual_data_id INTEGER,
        
        -- Классификация рекомендации
        recommendation_type TEXT NOT NULL,  -- revenue, cost, team, fundraising, product
        category TEXT,  -- acquisition, retention, monetization, efficiency
        priority TEXT NOT NULL,  -- critical, high, medium, low
        
        -- Содержание рекомендации
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        actions TEXT NOT NULL,  -- JSON список действий
        expected_impact TEXT,
        expected_metric_impact TEXT,  -- e.g., "Reduce CAC by 20%"
        
        -- Контекст и анализ
        analysis TEXT,  -- JSON с анализом ситуации
        benchmark_comparison TEXT,  -- Сравнение с эталонами
        success_metrics TEXT,  -- Метрики для оценки успеха
        
        -- Статус выполнения
        status TEXT DEFAULT 'pending',  -- pending, in_progress, completed, rejected, deferred
        assigned_to INTEGER,
        due_date DATE,
        completed_at TIMESTAMP,
        
        -- Обратная связь
        feedback TEXT,
        feedback_by INTEGER,
        feedback_at TIMESTAMP,
        
        created_by INTEGER,  -- AI system или пользователь
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        FOREIGN KEY (monthly_plan_id) REFERENCES monthly_plans (id),
        FOREIGN KEY (actual_data_id) REFERENCES actual_data (id),
        FOREIGN KEY (assigned_to) REFERENCES users (id),
        FOREIGN KEY (created_by) REFERENCES users (id),
        FOREIGN KEY (feedback_by) REFERENCES users (id)
    )
    ''')
    
    # Таблица эталонных метрик SaaS
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS benchmark_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        
        -- Классификация
        metric_name TEXT NOT NULL,
        metric_category TEXT NOT NULL,  -- growth, efficiency, profitability, etc.
        stage TEXT NOT NULL,  -- pre_seed, seed, series_a, etc.
        industry TEXT,  -- Optional: specific industry
        
        -- Значения метрик
        poor_value REAL,
        average_value REAL,
        good_value REAL,
        excellent_value REAL,
        
        -- Дополнительные диапазоны
        min_value REAL,
        max_value REAL,
        target_value REAL,
        
        -- Методология
        calculation_formula TEXT,
        measurement_unit TEXT,
        period TEXT DEFAULT 'monthly',  -- monthly, quarterly, annually
        
        -- Источники
        source_name TEXT NOT NULL,
        source_url TEXT,
        publication_year INTEGER,
        
        -- Метаданные
        description TEXT,
        notes TEXT,
        is_active BOOLEAN DEFAULT 1,
        
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_by TEXT DEFAULT 'system',
        
        UNIQUE(metric_name, stage, industry, source_name)
    )
    ''')
    
    # Таблица Capex Items
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS capex_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        monthly_plan_id INTEGER,
        company_id INTEGER,
        
        -- Основная информация
        item_name TEXT NOT NULL,
        description TEXT,
        category TEXT NOT NULL,  -- equipment, software, furniture, vehicle, other
        subcategory TEXT,
        
        -- Финансовые данные
        purchase_cost REAL NOT NULL,
        purchase_date DATE NOT NULL,
        estimated_useful_life INTEGER NOT NULL,  -- в месяцах
        residual_value REAL DEFAULT 0,
        
        -- Амортизация
        depreciation_method TEXT DEFAULT 'straight_line',  -- straight_line, declining_balance
        monthly_depreciation REAL,
        accumulated_depreciation REAL DEFAULT 0,
        net_book_value REAL,
        
        -- Логистика
        vendor TEXT,
        warranty_period INTEGER,  -- в месяцах
        location TEXT,
        
        -- Статус
        status TEXT DEFAULT 'planned',  -- planned, ordered, received, in_use, disposed
        disposal_date DATE,
        disposal_value REAL,
        
        -- Привязка к сотруднику/отделу
        assigned_to TEXT,
        department TEXT,
        
        notes TEXT,
        attachments TEXT,  -- JSON с путями к файлам
        
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        FOREIGN KEY (monthly_plan_id) REFERENCES monthly_plans (id),
        FOREIGN KEY (company_id) REFERENCES companies (id)
    )
    ''')
    
    # Таблица сценариев "Что если"
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS scenarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        plan_id INTEGER,
        
        -- Информация о сценарии
        scenario_name TEXT NOT NULL,
        description TEXT,
        scenario_type TEXT NOT NULL,  -- optimistic, pessimistic, base, custom
        base_scenario_id INTEGER,  -- На основе какого сценария
        
        -- Изменения параметров
        changes TEXT NOT NULL,  -- JSON с изменениями параметров
        assumptions TEXT,  -- JSON с допущениями
        
        -- Результаты симуляции
        results TEXT,  -- JSON с результатами
        summary_metrics TEXT,  -- Ключевые метрики сценария
        
        -- Метаданные
        created_by INTEGER,
        is_shared BOOLEAN DEFAULT 0,
        shared_with TEXT,  -- JSON с пользователями
        
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        FOREIGN KEY (company_id) REFERENCES companies (id),
        FOREIGN KEY (plan_id) REFERENCES financial_plans (id),
        FOREIGN KEY (created_by) REFERENCES users (id),
        FOREIGN KEY (base_scenario_id) REFERENCES scenarios (id)
    )
    ''')
    
    # Таблица отчетов
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        
        -- Информация об отчете
        report_name TEXT NOT NULL,
        report_type TEXT NOT NULL,  -- monthly, quarterly, annual, investor, board
        period_start DATE,
        period_end DATE,
        
        -- Контент отчета
        data_snapshot TEXT,  -- JSON с данными на момент создания
        analysis TEXT,  -- JSON с анализом
        recommendations TEXT,  -- JSON с рекомендациями
        
        -- Форматирование и вывод
        template_used TEXT,
        format TEXT DEFAULT 'pdf',  -- pdf, excel, html
        file_path TEXT,
        
        -- Статус
        status TEXT DEFAULT 'draft',  -- draft, generated, published, archived
        version INTEGER DEFAULT 1,
        
        -- Метаданные
        generated_by INTEGER,
        generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        published_at TIMESTAMP,
        viewed_count INTEGER DEFAULT 0,
        
        FOREIGN KEY (company_id) REFERENCES companies (id),
        FOREIGN KEY (generated_by) REFERENCES users (id)
    )
    ''')
    
    # Таблица активности пользователей (логи)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_activity (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        company_id INTEGER,
        
        activity_type TEXT NOT NULL,  -- login, plan_created, data_entered, etc.
        activity_details TEXT,  -- JSON с деталями
        ip_address TEXT,
        user_agent TEXT,
        
        performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (company_id) REFERENCES companies (id)
    )
    ''')
    
    # Таблица настроек приложения
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS app_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        setting_key TEXT UNIQUE NOT NULL,
        setting_value TEXT,
        setting_type TEXT DEFAULT 'string',  -- string, integer, float, boolean, json
        category TEXT DEFAULT 'general',
        description TEXT,
        is_editable BOOLEAN DEFAULT 1,
        
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Создаем индексы для производительности
    print("Создание индексов для производительности...")
    
    # Индексы для monthly_plans
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_monthly_plans_plan_id ON monthly_plans(plan_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_monthly_plans_month_year ON monthly_plans(year, month_number)')
    
    # Индексы для actual_data
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_actual_data_monthly_plan_id ON actual_data(monthly_plan_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_actual_data_recorded_at ON actual_data(recorded_at)')
    
    # Индексы для ai_recommendations
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_ai_recommendations_monthly_plan_id ON ai_recommendations(monthly_plan_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_ai_recommendations_status ON ai_recommendations(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_ai_recommendations_priority ON ai_recommendations(priority)')
    
    # Индексы для финансовых планов
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_financial_plans_company_id ON financial_plans(company_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_financial_plans_status ON financial_plans(status)')
    
    # Индексы для компаний
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_companies_user_id ON companies(user_id)')
    
    # Вставляем начальные данные
    print("Вставка начальных данных...")
    
    # Настройки приложения по умолчанию
    default_settings = [
        ('app_name', 'SaaS Financial Planner', 'string', 'general', 'Название приложения'),
        ('default_currency', 'RUB', 'string', 'financial', 'Валюта по умолчанию'),
        ('fiscal_year_start', '1', 'integer', 'financial', 'Начало финансового года (1=Январь)'),
        ('default_growth_rate', '0.2', 'float', 'planning', 'Стандартная скорость роста'),
        ('default_cac_target', '15000', 'float', 'metrics', 'Целевой CAC'),
        ('default_runway_target', '18', 'float', 'metrics', 'Целевой Runway в месяцах'),
        ('enable_ai_recommendations', 'true', 'boolean', 'features', 'Включить AI рекомендации'),
        ('enable_email_notifications', 'false', 'boolean', 'features', 'Включить email уведомления'),
        ('data_retention_months', '36', 'integer', 'data', 'Срок хранения данных в месяцах'),
        ('max_export_size_mb', '50', 'integer', 'export', 'Максимальный размер экспорта в MB'),
    ]
    
    cursor.executemany('''
    INSERT OR IGNORE INTO app_settings 
    (setting_key, setting_value, setting_type, category, description)
    VALUES (?, ?, ?, ?, ?)
    ''', default_settings)
    
    # Вставляем эталонные метрики SaaS
    insert_benchmark_data(cursor)
    
    # Создаем демо-пользователя если нет пользователей
    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
        INSERT INTO users (username, email, role) 
        VALUES ('demo', 'demo@example.com', 'admin')
        ''')
        demo_user_id = cursor.lastrowid
        
        # Создаем демо-компанию
        cursor.execute('''
        INSERT INTO companies (user_id, name, description, stage, industry, country, 
                              current_mrr, current_customers, monthly_price, team_size, cash_balance)
        VALUES (?, 'Demo SaaS Startup', 'Демонстрационная компания для тестирования', 
                'pre_seed', 'B2B SaaS', 'Russia', 25000, 5, 5000, 3, 2000000)
        ''', (demo_user_id,))
    
    table_count = get_table_count(conn)
    conn.commit()
    conn.close()

    print(f"✅ База данных успешно инициализирована: {resolved_path}")
    print(f"📊 Создано таблиц: {table_count}")
    print(f"📈 Загружено эталонных метрик: {get_benchmark_count(str(resolved_path))}")

def insert_benchmark_data(cursor):
    """Вставка эталонных метрик SaaS из реальных исследований"""
    
    benchmarks = [
        # Pre-Seed Stage Metrics
        ('mrr_growth_monthly', 'growth', 'pre_seed', None, 0.10, 0.20, 0.30, 0.50, 0.0, 2.0, 0.25, 
         '(Current MRR - Previous MRR) / Previous MRR', 'percentage', 'monthly',
         'Bessemer Cloud Index', 'https://www.bvp.com/atlas/cloud-index', 2023,
         'Monthly Recurring Revenue Growth Rate', 'Для pre-seed важно показывать быстрый рост', 1),
        
        ('cac_payback_months', 'efficiency', 'pre_seed', None, 24.0, 18.0, 12.0, 9.0, 3.0, 36.0, 12.0,
         'CAC / (MRR per Customer)', 'months', 'monthly',
         'OpenView SaaS Benchmarks', 'https://openviewpartners.com/saas-benchmarks', 2023,
         'CAC Payback Period', 'Время окупаемости стоимости привлечения клиента', 1),
        
        ('ltv_cac_ratio', 'profitability', 'pre_seed', None, 1.5, 3.0, 4.0, 5.0, 1.0, 10.0, 3.5,
         'LTV / CAC', 'ratio', 'lifetime',
         'SaaS Capital Metrics', 'https://www.saas-capital.com/saas-metrics/', 2023,
         'LTV to CAC Ratio', 'Соотношение пожизненной ценности клиента к стоимости его привлечения', 1),
        
        ('gross_margin', 'profitability', 'pre_seed', None, 0.60, 0.75, 0.85, 0.90, 0.50, 0.95, 0.80,
         '(Revenue - COGS) / Revenue', 'percentage', 'monthly',
         'Pacific Crest Survey', 'https://www.meritechcapital.com/benchmarks', 2023,
         'Gross Margin', 'Валовая маржа после вычета прямых затрат', 1),
        
        ('monthly_churn_rate', 'retention', 'pre_seed', None, 0.10, 0.05, 0.03, 0.01, 0.0, 0.20, 0.03,
         'Churned Customers / Total Customers at Start of Month', 'percentage', 'monthly',
         'Bessemer Cloud Index', 'https://www.bvp.com/atlas/cloud-index', 2023,
         'Monthly Customer Churn Rate', 'Месячный процент оттока клиентов', 1),
        
        ('burn_to_mrr_ratio', 'efficiency', 'pre_seed', None, 2.0, 1.5, 1.0, 0.8, 0.5, 3.0, 1.2,
         'Monthly Burn Rate / MRR', 'ratio', 'monthly',
         'OpenView SaaS Benchmarks', 'https://openviewpartners.com/saas-benchmarks', 2023,
         'Burn to MRR Ratio', 'Соотношение месячных расходов к MRR', 1),
        
        # Seed Stage Metrics (более агрессивные)
        ('mrr_growth_monthly', 'growth', 'seed', None, 0.15, 0.25, 0.40, 0.60, 0.0, 2.0, 0.30,
         '(Current MRR - Previous MRR) / Previous MRR', 'percentage', 'monthly',
         'Bessemer Cloud Index', 'https://www.bvp.com/atlas/cloud-index', 2023,
         'Monthly Recurring Revenue Growth Rate', 'Для seed стадии ожидается ускорение роста', 1),
        
        ('cac_payback_months', 'efficiency', 'seed', None, 18.0, 12.0, 9.0, 6.0, 3.0, 24.0, 9.0,
         'CAC / (MRR per Customer)', 'months', 'monthly',
         'OpenView SaaS Benchmarks', 'https://openviewpartners.com/saas-benchmarks', 2023,
         'CAC Payback Period', 'Seed компании должны быстрее окупать CAC', 1),
        
        # Industry Specific Benchmarks (B2B SaaS)
        ('sales_cycle_days', 'efficiency', 'pre_seed', 'B2B SaaS', 60.0, 45.0, 30.0, 15.0, 7.0, 90.0, 30.0,
         'Average days from first contact to closed deal', 'days', 'monthly',
         'Sales Benchmark Index', 'https://salesbenchmarkindex.com', 2023,
         'Sales Cycle Length', 'Средняя длина цикла продаж в днях', 1),
        
        ('website_conversion_rate', 'acquisition', 'pre_seed', 'B2B SaaS', 0.01, 0.02, 0.03, 0.05, 0.0, 0.10, 0.025,
         'Leads / Website Visitors', 'percentage', 'monthly',
         'Marketing Benchmark Report', 'https://www.marketingsherpa.com', 2023,
         'Website Conversion Rate', 'Конверсия посетителей сайта в лиды', 1),
    ]
    
    cursor.executemany('''
    INSERT OR REPLACE INTO benchmark_metrics 
    (metric_name, metric_category, stage, industry, poor_value, average_value, 
     good_value, excellent_value, min_value, max_value, target_value, 
     calculation_formula, measurement_unit, period, source_name, source_url, 
     publication_year, description, notes, is_active)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', benchmarks)

def get_benchmark_count(db_path: str) -> int:
    """Получение количества эталонных метрик в базе"""
    try:
        from database.path_utils import resolve_db_path

        resolved_path = resolve_db_path(db_path)
        conn = sqlite3.connect(resolved_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM benchmark_metrics')
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except:
        return 0

def get_table_count(conn: sqlite3.Connection) -> int:
    """Получение количества таблиц в базе"""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        return cursor.fetchone()[0]
    except Exception:
        return 0

def reset_database(db_path: str = 'database/saas_finance.db'):
    """Сброс базы данных (использовать с осторожностью!)"""

    from database.path_utils import resolve_db_path

    resolved_path = resolve_db_path(db_path)

    confirmation = input(
        f"⚠️  ВНИМАНИЕ: Это удалит ВСЕ данные в {resolved_path}\nВведите 'DELETE' для подтверждения: "
    )
    
    if confirmation == 'DELETE':
        if resolved_path.exists():
            os.remove(resolved_path)
            print(f"🗑️  База данных удалена: {resolved_path}")

        init_database(str(resolved_path))
        print("✅ База данных пересоздана с начальными данными")
    else:
        print("❌ Отменено пользователем")

def backup_database(db_path: str = 'database/saas_finance.db'):
    """Создание резервной копии базы данных"""

    from database.path_utils import resolve_db_path

    resolved_path = resolve_db_path(db_path)
    backup_dir = resolved_path.parent / "backups"
    os.makedirs(backup_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = backup_dir / f"saas_finance_backup_{timestamp}.db"

    import shutil
    shutil.copy2(resolved_path, backup_path)

    print(f"✅ Резервная копия создана: {backup_path}")
    return str(backup_path)

if __name__ == "__main__":
    print("🚀 Инициализация базы данных SaaS Financial Planning System")
    print("=" * 60)
    
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'init':
            init_database()
        elif command == 'reset':
            reset_database()
        elif command == 'backup':
            backup_database()
        elif command == 'benchmarks':
            init_database()
            count = get_benchmark_count('database/saas_finance.db')
            print(f"📊 Загружено эталонных метрик: {count}")
        else:
            print(f"❌ Неизвестная команда: {command}")
            print("Доступные команды: init, reset, backup, benchmarks")
    else:
        # По умолчанию инициализируем базу
        init_database()
