"""
Трекинг фактических данных для сравнения с планом
Учет реальных показателей, интеграция с внешними системами
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import json
from enum import Enum

# Импорты из database
try:
    from database.db_manager import ActualData, MonthlyPlan, VarianceAnalysisResult, db_manager
    # Создаем алиас для совместимости с существующим кодом
    ActualFinancial = ActualData
except ImportError as e:
    print(f"Warning: Could not import database modules: {e}")
    # Создаем заглушки для разработки
    class ActualFinancial:
        pass
    class MonthlyPlan:
        pass
    class VarianceAnalysisResult:
        pass
    class DBMock:
        def create_actual_financial(self, *args, **kwargs): return 1
        def get_monthly_plan_by_period(self, *args, **kwargs): return None
        def create_variance_analysis(self, *args, **kwargs): return None
        def get_actual_financials_by_filters(self, *args, **kwargs): return []
        def get_actual_financial_by_id(self, *args, **kwargs): return None
        def update_actual_financial(self, *args, **kwargs): return None
    db_manager = DBMock()

class DataSource(Enum):
    """Источники данных"""
    MANUAL_ENTRY = "manual"
    STRIPE = "stripe"
    CHARGEBEE = "chargebee"
    QUICKBOOKS = "quickbooks"
    XERO = "xero"
    GOOGLE_ANALYTICS = "google_analytics"
    METABASE = "metabase"
    CUSTOM_API = "custom_api"

@dataclass
class ActualFinancialData:
    """Фактические финансовые данные"""
    company_id: int
    year: int
    month_number: int
    month_name: str
    
    # Revenue
    actual_mrr: float = 0
    actual_new_customers: int = 0
    actual_churned_customers: int = 0
    actual_expansion_mrr: float = 0
    actual_reactivated_mrr: float = 0
    
    # Costs
    actual_marketing_spend: float = 0
    actual_salaries: float = 0
    actual_office_rent: float = 0
    actual_cloud_services: float = 0
    actual_software_subscriptions: float = 0
    actual_legal_accounting: float = 0
    actual_other_opex: float = 0
    
    # CAPEX
    actual_capex_equipment: float = 0
    actual_capex_software: float = 0
    actual_capex_furniture: float = 0
    actual_capex_other: float = 0
    
    # Calculated fields
    actual_total_revenue: float = 0
    actual_total_costs: float = 0
    actual_burn_rate: float = 0
    actual_runway: float = 0
    
    # Metadata
    data_source: str = DataSource.MANUAL_ENTRY.value
    last_updated: datetime = field(default_factory=datetime.now)
    is_verified: bool = False
    verification_notes: str = ""
    
class MonthlyTracker:
    """
    Трекинг фактических данных для SaaS компании
    Интеграция с платежными системами, учетными системами, BI-инструментами
    """
    
    def __init__(self):
        self.data_sources_config = {
            DataSource.STRIPE.value: {
                "revenue_fields": ["mrr", "new_customers", "churn"],
                "cost_fields": [],
                "api_key_required": True
            },
            DataSource.CHARGEBEE.value: {
                "revenue_fields": ["mrr", "new_customers", "churn", "expansion"],
                "cost_fields": [],
                "api_key_required": True
            },
            DataSource.QUICKBOOKS.value: {
                "revenue_fields": ["total_revenue"],
                "cost_fields": ["salaries", "rent", "software"],
                "oauth_required": True
            }
        }
        
    def record_monthly_actuals(self, data: ActualFinancialData) -> Dict[str, Any]:
        """
        Запись фактических данных за месяц
        
        Args:
            data: Фактические данные
        
        Returns:
            Dict с результатом записи
        """
        
        # Валидация данных
        validation_result = self._validate_actual_data(data)
        if not validation_result["valid"]:
            return {
                "success": False,
                "error": "Data validation failed",
                "validation_errors": validation_result["errors"]
            }
        
        # Автоматический расчет полей
        self._calculate_derived_fields(data)
        
        # Сохранение в базу данных
        try:
            # Используем ActualFinancial (который является алиасом для ActualData)
            actual_record = ActualFinancial(
                company_id=data.company_id,
                year=data.year,
                month_number=data.month_number,
                actual_mrr=data.actual_mrr,
                actual_new_customers=data.actual_new_customers,
                actual_churned_customers=data.actual_churned_customers,
                actual_expansion_mrr=data.actual_expansion_mrr,
                actual_reactivated_mrr=data.actual_reactivated_mrr,
                actual_marketing_spend=data.actual_marketing_spend,
                actual_salaries=data.actual_salaries,
                actual_office_rent=data.actual_office_rent,
                actual_cloud_services=data.actual_cloud_services,
                actual_software_subscriptions=data.actual_software_subscriptions,
                actual_legal_accounting=data.actual_legal_accounting,
                actual_other_opex=data.actual_other_opex,
                actual_capex_equipment=data.actual_capex_equipment,
                actual_capex_software=data.actual_capex_software,
                actual_capex_furniture=data.actual_capex_furniture,
                actual_capex_other=data.actual_capex_other,
                actual_total_revenue=data.actual_total_revenue,
                actual_total_costs=data.actual_total_costs,
                actual_burn_rate=data.actual_burn_rate,
                actual_runway=data.actual_runway,
                data_source=data.data_source,
                is_verified=data.is_verified,
                verification_notes=data.verification_notes
            )
            
            record_id = db_manager.create_actual_financial(actual_record)
            
            # Анализ отклонений если есть соответствующий план
            self._trigger_variance_analysis(data)
            
            return {
                "success": True,
                "record_id": record_id,
                "message": "Actual data recorded successfully",
                "calculated_fields": {
                    "total_revenue": data.actual_total_revenue,
                    "total_costs": data.actual_total_costs,
                    "burn_rate": data.actual_burn_rate
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _validate_actual_data(self, data: ActualFinancialData) -> Dict[str, Any]:
        """Валидация фактических данных"""
        
        errors = []
        warnings = []
        
        # Проверка обязательных полей
        if data.year < 2020 or data.year > 2030:
            errors.append("Некорректный год")
        
        if data.month_number < 1 or data.month_number > 12:
            errors.append("Некорректный номер месяца")
        
        # Проверка числовых полей на отрицательные значения
        numeric_fields = [
            ('actual_mrr', 'MRR'),
            ('actual_new_customers', 'New Customers'),
            ('actual_marketing_spend', 'Marketing Spend'),
            ('actual_salaries', 'Salaries')
        ]
        
        for field_name, field_label in numeric_fields:
            value = getattr(data, field_name)
            if value < 0:
                warnings.append(f"{field_label} имеет отрицательное значение")
        
        # Проверка consistency
        if data.actual_new_customers < 0 and data.actual_churned_customers < 0:
            warnings.append("И new customers и churned customers отрицательные")
        
        # Проверка data source
        if data.data_source not in [ds.value for ds in DataSource]:
            warnings.append(f"Неизвестный источник данных: {data.data_source}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def _calculate_derived_fields(self, data: ActualFinancialData):
        """Автоматический расчет производных полей"""
        
        # Total Revenue (если не задано вручную)
        if data.actual_total_revenue == 0:
            # Расчет на основе MRR и expansion
            data.actual_total_revenue = data.actual_mrr + data.actual_expansion_mrr + data.actual_reactivated_mrr
        
        # Total Costs
        opex_fields = [
            data.actual_marketing_spend,
            data.actual_salaries,
            data.actual_office_rent,
            data.actual_cloud_services,
            data.actual_software_subscriptions,
            data.actual_legal_accounting,
            data.actual_other_opex
        ]
        
        capex_fields = [
            data.actual_capex_equipment,
            data.actual_capex_software,
            data.actual_capex_furniture,
            data.actual_capex_other
        ]
        
        data.actual_total_costs = sum(opex_fields) + sum(capex_fields)
        
        # Burn Rate
        data.actual_burn_rate = max(0, data.actual_total_costs - data.actual_total_revenue)
        
        # Runway будет рассчитан позже с учетом cash balance
        data.actual_runway = 0
    
    def _trigger_variance_analysis(self, data: ActualFinancialData):
        """Триггер анализа отклонений при записи данных"""
        
        try:
            # Получаем соответствующий плановый месяц
            monthly_plan = db_manager.get_monthly_plan_by_period(
                data.company_id, data.year, data.month_number
            )
            
            if monthly_plan:
                # Анализируем variance
                try:
                    from services.financial_system.variance_analyzer import variance_analyzer
                    
                    variance_result = variance_analyzer.analyze_variance(
                        [monthly_plan.to_dict()],
                        [data.__dict__],
                        "pre_seed"  # Stage будет получен из компании
                    )
                    
                    # Сохраняем результаты анализа
                    self._save_variance_results(data.company_id, data.year, 
                                              data.month_number, variance_result)
                    
                except ImportError:
                    print("Variance analyzer not available")
                
        except Exception as e:
            print(f"Error triggering variance analysis: {e}")
    
    def _save_variance_results(self, company_id: int, year: int, 
                              month_number: int, variance_result: Dict[str, Any]):
        """Сохранение результатов анализа отклонений"""
        
        try:
            result = VarianceAnalysisResult(
                company_id=company_id,
                year=year,
                month_number=month_number,
                analysis_date=datetime.now(),
                variance_summary=json.dumps(variance_result.get("variance_summary", {})),
                significant_variances_count=len(variance_result.get("significant_variances", [])),
                has_critical_issues=any(
                    v.get("significance") == "critical" 
                    for v in variance_result.get("significant_variances", [])
                ),
                recommendations=json.dumps(variance_result.get("recommendations", {}))
            )
            
            db_manager.create_variance_analysis(result)
            
        except Exception as e:
            print(f"Error saving variance results: {e}")
    
    def sync_with_external_system(self, company_id: int, 
                                 data_source: str, 
                                 period_start: datetime,
                                 period_end: datetime) -> Dict[str, Any]:
        """
        Синхронизация с внешней системой
        
        Args:
            company_id: ID компании
            data_source: Источник данных (stripe, chargebee, etc.)
            period_start: Начало периода
            period_end: Конец периода
        
        Returns:
            Dict с результатами синхронизации
        """
        
        # Проверка конфигурации источника данных
        if data_source not in self.data_sources_config:
            return {
                "success": False,
                "error": f"Unsupported data source: {data_source}"
            }
        
        source_config = self.data_sources_config[data_source]
        
        # Получение данных в зависимости от источника
        if data_source == DataSource.STRIPE.value:
            data = self._sync_with_stripe(company_id, period_start, period_end)
        elif data_source == DataSource.CHARGEBEE.value:
            data = self._sync_with_chargebee(company_id, period_start, period_end)
        elif data_source == DataSource.QUICKBOOKS.value:
            data = self._sync_with_quickbooks(company_id, period_start, period_end)
        else:
            return {
                "success": False,
                "error": f"Sync not implemented for: {data_source}"
            }
        
        if data.get("success", False):
            # Обработка полученных данных
            processed_data = self._process_external_data(data["raw_data"], data_source)
            
            # Сохранение в базу данных
            for month_data in processed_data:
                month_data.company_id = company_id  # Устанавливаем правильный company_id
                self.record_monthly_actuals(month_data)
            
            return {
                "success": True,
                "records_processed": len(processed_data),
                "period": f"{period_start.date()} to {period_end.date()}",
                "data_source": data_source,
                "summary": self._create_sync_summary(processed_data)
            }
        else:
            return data
    
    def _sync_with_stripe(self, company_id: int, 
                         period_start: datetime,
                         period_end: datetime) -> Dict[str, Any]:
        """Синхронизация с Stripe"""
        
        try:
            # Здесь будет реальная интеграция со Stripe API
            # Пока возвращаем mock данные
            
            try:
                from database.db_manager import Company
                company = db_manager.get_company(company_id)
                if not company:
                    return {"success": False, "error": "Company not found"}
                
                base_mrr = company.current_mrr
                base_customers = company.current_customers
            except:
                # Если не можем получить компанию, используем defaults
                base_mrr = 10000
                base_customers = 100
            
            # Mock данные для демонстрации
            mock_data = []
            current_date = period_start
            
            while current_date <= period_end:
                # Создаем mock данные для каждого месяца
                month_data = {
                    "period": current_date.strftime("%Y-%m"),
                    "mrr": base_mrr * (1 + np.random.uniform(0.05, 0.15)),
                    "new_customers": int(base_customers * np.random.uniform(0.05, 0.1)),
                    "churned_customers": int(base_customers * np.random.uniform(0.02, 0.04)),
                    "expansion_mrr": base_mrr * np.random.uniform(0.01, 0.03),
                    "total_revenue": base_mrr * (1 + np.random.uniform(0.08, 0.12))
                }
                
                mock_data.append(month_data)
                
                # Переход к следующему месяцу
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1)
            
            return {
                "success": True,
                "raw_data": mock_data,
                "source": "stripe",
                "api_version": "mock"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Stripe sync failed: {str(e)}"
            }
    
    def _sync_with_chargebee(self, company_id: int,
                            period_start: datetime,
                            period_end: datetime) -> Dict[str, Any]:
        """Синхронизация с Chargebee"""
        
        # Аналогично Stripe, но с другой структурой данных
        # Возвращаем mock данные для демонстрации
        
        return {
            "success": True,
            "raw_data": [],
            "source": "chargebee",
            "api_version": "mock",
            "note": "Chargebee integration not implemented"
        }
    
    def _sync_with_quickbooks(self, company_id: int,
                             period_start: datetime,
                             period_end: datetime) -> Dict[str, Any]:
        """Синхронизация с QuickBooks"""
        
        # Возвращаем mock данные для демонстрации
        
        return {
            "success": True,
            "raw_data": [],
            "source": "quickbooks",
            "api_version": "mock",
            "note": "QuickBooks integration not implemented"
        }
    
    def _process_external_data(self, raw_data: List[Dict], 
                              data_source: str) -> List[ActualFinancialData]:
        """Обработка данных из внешней системы"""
        
        processed_data = []
        
        for raw in raw_data:
            # Извлекаем год и месяц из периода
            period = raw.get("period", "")
            if "-" in period:
                year_str, month_str = period.split("-")
                year = int(year_str)
                month_number = int(month_str)
            else:
                year = datetime.now().year
                month_number = datetime.now().month
            
            # Создаем объект ActualFinancialData
            actual_data = ActualFinancialData(
                company_id=1,  # Будет заменено на реальный company_id позже
                year=year,
                month_number=month_number,
                month_name=self._get_month_name(month_number),
                data_source=data_source,
                is_verified=True  # Данные из API считаются верифицированными
            )
            
            # Маппинг полей в зависимости от источника данных
            if data_source == DataSource.STRIPE.value:
                actual_data.actual_mrr = raw.get("mrr", 0)
                actual_data.actual_new_customers = raw.get("new_customers", 0)
                actual_data.actual_churned_customers = raw.get("churned_customers", 0)
                actual_data.actual_expansion_mrr = raw.get("expansion_mrr", 0)
                actual_data.actual_total_revenue = raw.get("total_revenue", 0)
            
            elif data_source == DataSource.QUICKBOOKS.value:
                actual_data.actual_salaries = raw.get("salaries", 0)
                actual_data.actual_office_rent = raw.get("rent", 0)
                actual_data.actual_software_subscriptions = raw.get("software", 0)
                actual_data.actual_total_costs = raw.get("total_costs", 0)
            
            # Автоматический расчет остальных полей
            self._calculate_derived_fields(actual_data)
            
            processed_data.append(actual_data)
        
        return processed_data
    
    def _get_month_name(self, month_number: int) -> str:
        """Получение названия месяца по номеру"""
        
        month_names = {
            1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель',
            5: 'Май', 6: 'Июнь', 7: 'Июль', 8: 'Август',
            9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'
        }
        
        return month_names.get(month_number, f"Месяц {month_number}")
    
    def _create_sync_summary(self, processed_data: List[ActualFinancialData]) -> Dict[str, Any]:
        """Создание summary синхронизации"""
        
        if not processed_data:
            return {"no_data": True}
        
        total_revenue = sum(d.actual_total_revenue for d in processed_data)
        total_costs = sum(d.actual_total_costs for d in processed_data)
        total_customers = sum(d.actual_new_customers for d in processed_data)
        
        return {
            "periods_processed": len(processed_data),
            "total_revenue": total_revenue,
            "total_costs": total_costs,
            "total_profit": total_revenue - total_costs,
            "total_customers": total_customers,
            "avg_mrr": np.mean([d.actual_mrr for d in processed_data]),
            "avg_burn_rate": np.mean([d.actual_burn_rate for d in processed_data])
        }
    
    def get_monthly_actuals(self, company_id: int, 
                           year: Optional[int] = None,
                           month_number: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Получение фактических данных
        
        Args:
            company_id: ID компании
            year: Год (опционально)
            month_number: Месяц (опционально)
        
        Returns:
            List фактических данных
        """
        
        filters = {"company_id": company_id}
        if year:
            filters["year"] = year
        if month_number:
            filters["month_number"] = month_number
        
        actuals = db_manager.get_actual_financials_by_filters(filters)
        
        # Конвертация в dict
        result = []
        for actual in actuals:
            # Проверяем, есть ли метод to_dict()
            if hasattr(actual, 'to_dict'):
                actual_dict = actual.to_dict()
            else:
                # Если нет, создаем dict из атрибутов
                actual_dict = {}
                for attr in dir(actual):
                    if not attr.startswith('_') and not callable(getattr(actual, attr)):
                        actual_dict[attr] = getattr(actual, attr)
            
            # Добавляем calculated metrics
            actual_dict["net_profit"] = actual_dict.get("actual_total_revenue", 0) - actual_dict.get("actual_total_costs", 0)
            revenue = actual_dict.get("actual_total_revenue", 0)
            actual_dict["profit_margin"] = (actual_dict["net_profit"] / revenue if revenue > 0 else 0)
            
            # Добавляем completion status
            actual_dict["completion_status"] = self._calculate_completion_status(actual)
            
            result.append(actual_dict)
        
        return result
    
    def _calculate_completion_status(self, actual: ActualFinancial) -> Dict[str, Any]:
        """Расчет статуса заполненности данных"""
        
        # Проверяем заполненность ключевых полей
        required_fields = [
            ("actual_mrr", "MRR"),
            ("actual_new_customers", "New Customers"),
            ("actual_total_revenue", "Total Revenue"),
            ("actual_total_costs", "Total Costs")
        ]
        
        completed_fields = 0
        total_fields = len(required_fields)
        
        for field_name, field_label in required_fields:
            if hasattr(actual, field_name):
                value = getattr(actual, field_name)
                if value is not None and value != 0:
                    completed_fields += 1
        
        completion_percent = (completed_fields / total_fields) * 100 if total_fields > 0 else 0
        
        if completion_percent >= 90:
            status = "complete"
            color = "green"
        elif completion_percent >= 70:
            status = "mostly_complete"
            color = "yellow"
        elif completion_percent >= 50:
            status = "partial"
            color = "orange"
        else:
            status = "incomplete"
            color = "red"
        
        return {
            "percent": completion_percent,
            "status": status,
            "color": color,
            "completed_fields": completed_fields,
            "total_fields": total_fields
        }
    
    def update_runway_calculation(self, company_id: int, 
                                 cash_balance: float) -> Dict[str, Any]:
        """
        Обновление расчета runway на основе фактических данных
        
        Args:
            company_id: ID компании
            cash_balance: Текущий баланс денежных средств
        
        Returns:
            Dict с обновленным runway
        """
        
        # Получаем последние фактические данные
        actuals = self.get_monthly_actuals(company_id)
        
        if not actuals:
            return {
                "success": False,
                "error": "No actual data found"
            }
        
        # Сортируем по дате
        actuals.sort(key=lambda x: (x.get("year", 0), x.get("month_number", 0)))
        
        # Рассчитываем average burn rate
        recent_actuals = actuals[-3:] if len(actuals) >= 3 else actuals
        avg_burn_rate = np.mean([a.get("actual_burn_rate", 0) for a in recent_actuals])
        
        # Расчет runway
        if avg_burn_rate > 0:
            runway_months = cash_balance / avg_burn_rate
        else:
            runway_months = float('inf')
        
        # Обновляем runway в последней записи (если можем)
        if actuals and hasattr(db_manager, 'update_actual_financial'):
            last_actual = actuals[-1]
            actual_id = last_actual.get("id")
            if actual_id:
                try:
                    actual_obj = db_manager.get_actual_financial_by_id(actual_id)
                    if actual_obj:
                        actual_obj.actual_runway = runway_months
                        db_manager.update_actual_financial(actual_obj)
                except:
                    pass  # Если не можем обновить, продолжаем
        
        return {
            "success": True,
            "cash_balance": cash_balance,
            "avg_burn_rate": avg_burn_rate,
            "runway_months": runway_months,
            "runway_category": self._categorize_runway(runway_months),
            "calculation_date": datetime.now().isoformat()
        }
    
    def _categorize_runway(self, runway_months: float) -> Dict[str, Any]:
        """Категоризация runway"""
        
        if runway_months == float('inf'):
            return {
                "category": "infinite",
                "color": "green",
                "label": "💰 Positive Cash Flow",
                "description": "Компания генерирует positive cash flow"
            }
        elif runway_months >= 24:
            return {
                "category": "excellent",
                "color": "green",
                "label": "✅ Excellent (>24 месяцев)",
                "description": "Более 2 лет runway, отличная позиция"
            }
        elif runway_months >= 18:
            return {
                "category": "very_good",
                "color": "blue",
                "label": "👍 Very Good (18-24 месяца)",
                "description": "Более 1.5 лет runway, очень хорошая позиция"
            }
        elif runway_months >= 12:
            return {
                "category": "good",
                "color": "lightblue",
                "label": "👌 Good (12-18 месяцев)",
                "description": "1+ год runway, хорошая позиция для роста"
            }
        elif runway_months >= 9:
            return {
                "category": "warning",
                "color": "yellow",
                "label": "⚠️ Warning (9-12 месяцев)",
                "description": "Менее года runway, начинать планирование fundraising"
            }
        elif runway_months >= 6:
            return {
                "category": "concerning",
                "color": "orange",
                "label": "🔶 Concerning (6-9 месяцев)",
                "description": "Менее 9 месяцев runway, срочно начинать fundraising"
            }
        elif runway_months >= 3:
            return {
                "category": "critical",
                "color": "red",
                "label": "🚨 Critical (3-6 месяцев)",
                "description": "Менее 6 месяцев runway, emergency меры нужны"
            }
        else:
            return {
                "category": "emergency",
                "color": "darkred",
                "label": "💀 Emergency (<3 месяцев)",
                "description": "Критически мало времени, emergency план нужен"
            }
    
    def create_monthly_report(self, company_id: int, 
                             year: int, month_number: int) -> Dict[str, Any]:
        """
        Создание месячного отчета
        
        Args:
            company_id: ID компании
            year: Год
            month_number: Месяц
        
        Returns:
            Dict с месячным отчетом
        """
        
        # Получаем фактические данные
        actuals = self.get_monthly_actuals(company_id, year, month_number)
        
        if not actuals:
            return {
                "success": False,
                "error": "No actual data found for specified period"
            }
        
        actual_data = actuals[0]
        
        # Получаем плановые данные
        monthly_plan = db_manager.get_monthly_plan_by_period(
            company_id, year, month_number
        )
        
        # Анализ отклонений
        variance_result = None
        if monthly_plan:
            try:
                from services.financial_system.variance_analyzer import variance_analyzer
                variance_result = variance_analyzer.analyze_variance(
                    [monthly_plan.to_dict()] if hasattr(monthly_plan, 'to_dict') else monthly_plan,
                    [actual_data],
                    "pre_seed"  # Stage будет получен из компании
                )
            except ImportError:
                variance_result = {"error": "Variance analyzer not available"}
        
        # Ключевые метрики
        key_metrics = self._calculate_key_metrics(actual_data, monthly_plan)
        
        # Рекомендации
        recommendations = self._generate_monthly_recommendations(actual_data, monthly_plan)
        
        # Создание отчета
        report = {
            "period": {
                "year": year,
                "month": month_number,
                "month_name": self._get_month_name(month_number)
            },
            "actual_data": actual_data,
            "plan_data": monthly_plan.to_dict() if monthly_plan and hasattr(monthly_plan, 'to_dict') else None,
            "variance_analysis": variance_result,
            "key_metrics": key_metrics,
            "recommendations": recommendations,
            "next_steps": self._suggest_next_steps(actual_data, variance_result),
            "report_date": datetime.now().isoformat()
        }
        
        return report
    
    def _calculate_key_metrics(self, actual_data: Dict, 
                              monthly_plan: Optional[Any]) -> Dict[str, Any]:
        """Расчет ключевых метрик для отчета"""
        
        metrics = {
            "revenue_metrics": {},
            "cost_metrics": {},
            "efficiency_metrics": {},
            "cash_metrics": {}
        }
        
        # Revenue metrics
        metrics["revenue_metrics"] = {
            "mrr": actual_data.get("actual_mrr", 0),
            "new_customers": actual_data.get("actual_new_customers", 0),
            "churned_customers": actual_data.get("actual_churned_customers", 0),
            "net_new_customers": actual_data.get("actual_new_customers", 0) - 
                               actual_data.get("actual_churned_customers", 0),
            "expansion_mrr": actual_data.get("actual_expansion_mrr", 0)
        }
        
        # Cost metrics
        total_costs = actual_data.get("actual_total_costs", 0)
        metrics["cost_metrics"] = {
            "total_costs": total_costs,
            "salaries_percent": (actual_data.get("actual_salaries", 0) / total_costs * 100 
                               if total_costs > 0 else 0),
            "marketing_percent": (actual_data.get("actual_marketing_spend", 0) / total_costs * 100 
                                if total_costs > 0 else 0),
            "cloud_services_percent": (actual_data.get("actual_cloud_services", 0) / total_costs * 100 
                                     if total_costs > 0 else 0)
        }
        
        # Efficiency metrics
        revenue = actual_data.get("actual_total_revenue", 0)
        metrics["efficiency_metrics"] = {
            "gross_margin": ((revenue - actual_data.get("actual_cloud_services", 0) * 0.2) / revenue 
                           if revenue > 0 else 0),
            "burn_rate": actual_data.get("actual_burn_rate", 0),
            "profit_margin": ((revenue - total_costs) / revenue if revenue > 0 else 0)
        }
        
        # Cash metrics
        metrics["cash_metrics"] = {
            "runway": actual_data.get("actual_runway", 0),
            "net_cash_flow": revenue - total_costs
        }
        
        # Добавляем vs plan если есть план
        if monthly_plan and hasattr(monthly_plan, 'to_dict'):
            plan_dict = monthly_plan.to_dict()
            
            # Revenue vs plan
            planned_revenue = plan_dict.get("plan_total_revenue", 0)
            actual_revenue = actual_data.get("actual_total_revenue", 0)
            revenue_variance = ((actual_revenue - planned_revenue) / planned_revenue * 100 
                              if planned_revenue > 0 else 0)
            
            metrics["revenue_metrics"]["vs_plan_percent"] = revenue_variance
            
            # Cost vs plan
            planned_costs = plan_dict.get("plan_total_costs", 0)
            cost_variance = ((total_costs - planned_costs) / planned_costs * 100 
                           if planned_costs > 0 else 0)
            
            metrics["cost_metrics"]["vs_plan_percent"] = cost_variance
        
        return metrics
    
    def _generate_monthly_recommendations(self, actual_data: Dict,
                                         monthly_plan: Optional[Any]) -> Dict[str, List[str]]:
        """Генерация рекомендаций на основе месячных данных"""
        
        recommendations = {
            "immediate": [],
            "short_term": [],
            "long_term": []
        }
        
        # Анализ burn rate
        burn_rate = actual_data.get("actual_burn_rate", 0)
        if burn_rate > 0:
            # Проверяем runway
            runway = actual_data.get("actual_runway", 0)
            if runway < 6:
                recommendations["immediate"].append(
                    f"Runway всего {runway:.1f} месяцев. Необходимо сократить burn rate или начать fundraising"
                )
            elif runway < 12:
                recommendations["short_term"].append(
                    "Начать подготовку к следующему раунду финансирования"
                )
        
        # Анализ revenue growth
        revenue = actual_data.get("actual_total_revenue", 0)
        new_customers = actual_data.get("actual_new_customers", 0)
        
        if monthly_plan and hasattr(monthly_plan, 'to_dict'):
            plan_dict = monthly_plan.to_dict()
            planned_revenue = plan_dict.get("plan_total_revenue", 0)
            planned_customers = plan_dict.get("plan_new_customers", 0)
            
            if revenue < planned_revenue * 0.8:
                recommendations["immediate"].append(
                    "Выручка значительно ниже плана. Пересмотреть sales и marketing стратегии"
                )
            
            if new_customers < planned_customers * 0.7:
                recommendations["short_term"].append(
                    "Новые клиенты ниже плана. Оптимизировать customer acquisition"
                )
        
        # Анализ costs
        marketing_spend = actual_data.get("actual_marketing_spend", 0)
        if marketing_spend > 0 and new_customers > 0:
            cac = marketing_spend / new_customers
            if cac > 1000:  # Пример threshold
                recommendations["short_term"].append(
                    f"CAC ${cac:.0f} высокий. Оптимизировать маркетинговые каналы"
                )
        
        # Общие рекомендации
        recommendations["long_term"].extend([
            "Регулярно пересматривать и обновлять финансовый план",
            "Автоматизировать сбор данных из всех источников",
            "Создать систему alerts для critical deviations"
        ])
        
        return recommendations
    
    def _suggest_next_steps(self, actual_data: Dict, 
                           variance_result: Optional[Dict]) -> List[str]:
        """Предложение следующих шагов"""
        
        next_steps = []
        
        # Проверка completeness данных
        completion = actual_data.get("completion_status", {})
        if completion.get("status") != "complete":
            next_steps.append(f"Заполнить недостающие данные ({completion.get('percent', 0):.0f}% complete)")
        
        # Если есть значимые отклонения
        if variance_result and variance_result.get("significant_variances"):
            next_steps.append("Проанализировать и принять меры по significant variances")
        
        # Проверка необходимости обновления плана
        if actual_data.get("actual_total_revenue", 0) > 0:
            # Если факт сильно отличается от плана
            next_steps.append("Рассмотреть обновление финансового плана на основе фактических данных")
        
        # Регулярные задачи
        next_steps.extend([
            "Запланировать monthly review meeting",
            "Обновить cash balance для точного расчета runway",
            "Подготовить данные для следующего месяца"
        ])
        
        return next_steps

# Создаем глобальный экземпляр трекера
monthly_tracker = MonthlyTracker()

# Экспортируем полезные функции
def record_actual_financials(company_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    """Публичная функция для записи фактических данных"""
    
    # Конвертация dict в ActualFinancialData
    actual_data = ActualFinancialData(
        company_id=company_id,
        year=data.get("year", datetime.now().year),
        month_number=data.get("month_number", datetime.now().month),
        month_name=data.get("month_name", ""),
        actual_mrr=data.get("actual_mrr", 0),
        actual_new_customers=data.get("actual_new_customers", 0),
        actual_churned_customers=data.get("actual_churned_customers", 0),
        actual_expansion_mrr=data.get("actual_expansion_mrr", 0),
        actual_marketing_spend=data.get("actual_marketing_spend", 0),
        actual_salaries=data.get("actual_salaries", 0),
        actual_office_rent=data.get("actual_office_rent", 0),
        actual_cloud_services=data.get("actual_cloud_services", 0),
        actual_software_subscriptions=data.get("actual_software_subscriptions", 0),
        actual_legal_accounting=data.get("actual_legal_accounting", 0),
        actual_other_opex=data.get("actual_other_opex", 0),
        data_source=data.get("data_source", DataSource.MANUAL_ENTRY.value)
    )
    
    return monthly_tracker.record_monthly_actuals(actual_data)

def get_monthly_report(company_id: int, year: int, month: int) -> Dict[str, Any]:
    """Публичная функция для получения месячного отчета"""
    return monthly_tracker.create_monthly_report(company_id, year, month)

def sync_external_data(company_id: int, data_source: str, 
                      start_date: str, end_date: str) -> Dict[str, Any]:
    """Публичная функция для синхронизации с внешней системой"""
    return monthly_tracker.sync_with_external_system(
        company_id, data_source,
        datetime.fromisoformat(start_date),
        datetime.fromisoformat(end_date)
    )