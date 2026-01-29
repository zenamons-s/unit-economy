"""
Валидатор данных для SaaS метрик
Проверка корректности входных данных и расчетных показателей
"""

import re
import pandas as pd
import numpy as np
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from enum import Enum

class ValidationLevel(Enum):
    """Уровни валидации"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ValidationRule(Enum):
    """Правила валидации"""
    REQUIRED = "required"
    POSITIVE = "positive"
    NON_NEGATIVE = "non_negative"
    WITHIN_RANGE = "within_range"
    VALID_DATE = "valid_date"
    VALID_EMAIL = "valid_email"
    VALID_PERCENTAGE = "valid_percentage"
    CONSISTENT = "consistent"
    BUSINESS_LOGIC = "business_logic"

@dataclass
class ValidationResult:
    """Результат валидации"""
    field: str
    rule: ValidationRule
    level: ValidationLevel
    message: str
    value: Any
    expected: Optional[Any] = None
    actual: Optional[Any] = None
    is_valid: bool = True

class DataValidator:
    """
    Валидатор данных для SaaS метрик и финансовых показателей
    """
    
    def __init__(self):
        # Определяем правила валидации для разных типов данных
        self.validation_rules = {
            # Company data
            "company_name": [ValidationRule.REQUIRED],
            "stage": [ValidationRule.REQUIRED],
            "current_mrr": [ValidationRule.REQUIRED, ValidationRule.NON_NEGATIVE],
            "current_customers": [ValidationRule.REQUIRED, ValidationRule.NON_NEGATIVE],
            "monthly_price": [ValidationRule.REQUIRED, ValidationRule.POSITIVE],
            "team_size": [ValidationRule.REQUIRED, ValidationRule.POSITIVE],
            "cash_balance": [ValidationRule.NON_NEGATIVE],
            
            # Financial metrics
            "mrr": [ValidationRule.NON_NEGATIVE],
            "arr": [ValidationRule.NON_NEGATIVE],
            "cac": [ValidationRule.NON_NEGATIVE],
            "ltv": [ValidationRule.NON_NEGATIVE],
            "churn_rate": [ValidationRule.WITHIN_RANGE],  # 0-100%
            "growth_rate": [ValidationRule.WITHIN_RANGE],  # -100% - 500%
            "burn_rate": [ValidationRule.NON_NEGATIVE],
            "runway": [ValidationRule.NON_NEGATIVE],
            
            # Percentages
            "gross_margin": [ValidationRule.VALID_PERCENTAGE],
            "net_margin": [ValidationRule.VALID_PERCENTAGE],
            "expansion_rate": [ValidationRule.VALID_PERCENTAGE],
            
            # Dates
            "founding_date": [ValidationRule.VALID_DATE],
            "last_funding_date": [ValidationRule.VALID_DATE],
            "plan_start_date": [ValidationRule.VALID_DATE],
            "plan_end_date": [ValidationRule.VALID_DATE]
        }
        
        # Диапазоны значений для разных метрик
        self.value_ranges = {
            "churn_rate": (0, 100),  # 0-100%
            "growth_rate": (-100, 500),  # -100% to 500%
            "gross_margin": (0, 100),  # 0-100%
            "net_margin": (-100, 100),  # -100% to 100%
            "expansion_rate": (0, 100),  # 0-100%
            "team_size": (1, 1000),  # 1-1000 человек
            "monthly_price": (1, 100000),  # $1 - $100k
            "cac": (0, 1000000),  # $0 - $1M
            "ltv": (0, 10000000)  # $0 - $10M
        }
        
        # Business logic rules
        self.business_rules = [
            ("ltv_cac_ratio", lambda data: data.get("ltv", 0) / max(data.get("cac", 1), 1) >= 1.0,
             "LTV should be at least equal to CAC"),
            ("burn_rate_check", lambda data: data.get("burn_rate", 0) <= data.get("cash_balance", 0) * 12,
             "Burn rate too high relative to cash balance"),
            ("growth_sustainability", lambda data: data.get("growth_rate", 0) <= 100 if data.get("current_mrr", 0) < 10000 else data.get("growth_rate", 0) <= 50,
             "Growth rate may not be sustainable")
        ]
    
    def validate_company_data(self, company_data: Dict[str, Any]) -> List[ValidationResult]:
        """
        Валидация данных компании
        
        Args:
            company_data: Данные компании
        
        Returns:
            List результатов валидации
        """
        
        results = []
        
        # Проверка обязательных полей
        required_fields = ["company_name", "stage", "current_mrr", 
                          "current_customers", "monthly_price", "team_size"]
        
        for field in required_fields:
            if field not in company_data or company_data[field] is None:
                results.append(ValidationResult(
                    field=field,
                    rule=ValidationRule.REQUIRED,
                    level=ValidationLevel.ERROR,
                    message=f"Обязательное поле {field} отсутствует",
                    value=None,
                    is_valid=False
                ))
        
        # Проверка числовых полей
        numeric_fields = ["current_mrr", "current_customers", "monthly_price", 
                         "team_size", "cash_balance"]
        
        for field in numeric_fields:
            if field in company_data and company_data[field] is not None:
                value = company_data[field]
                
                # Проверка что значение числовое
                if not isinstance(value, (int, float)):
                    results.append(ValidationResult(
                        field=field,
                        rule=ValidationRule.REQUIRED,
                        level=ValidationLevel.ERROR,
                        message=f"Поле {field} должно быть числом",
                        value=value,
                        is_valid=False
                    ))
                    continue
                
                # Проверка на отрицательные значения
                if field in ["current_mrr", "current_customers", "monthly_price", 
                            "team_size"] and value <= 0:
                    results.append(ValidationResult(
                        field=field,
                        rule=ValidationRule.POSITIVE,
                        level=ValidationLevel.ERROR,
                        message=f"Поле {field} должно быть положительным",
                        value=value,
                        is_valid=False
                    ))
                
                # Проверка диапазона
                if field in self.value_ranges:
                    min_val, max_val = self.value_ranges[field]
                    if value < min_val or value > max_val:
                        results.append(ValidationResult(
                            field=field,
                            rule=ValidationRule.WITHIN_RANGE,
                            level=ValidationLevel.WARNING,
                            message=f"Поле {field} вне ожидаемого диапазона ({min_val} - {max_val})",
                            value=value,
                            expected=f"{min_val} - {max_val}",
                            actual=value
                        ))
        
        # Проверка stage
        if "stage" in company_data:
            valid_stages = ["pre_seed", "seed", "series_a", "series_b", 
                           "series_c", "growth", "mature", "public"]
            
            if company_data["stage"] not in valid_stages:
                results.append(ValidationResult(
                    field="stage",
                    rule=ValidationRule.REQUIRED,
                    level=ValidationLevel.WARNING,
                    message=f"Стадия компании должна быть одной из: {', '.join(valid_stages)}",
                    value=company_data["stage"],
                    expected=valid_stages
                ))
        
        # Проверка business logic
        results.extend(self._validate_business_logic(company_data))
        
        return results
    
    def validate_financial_metrics(self, metrics: Dict[str, Any]) -> List[ValidationResult]:
        """
        Валидация финансовых метрик
        
        Args:
            metrics: Финансовые метрики
        
        Returns:
            List результатов валидации
        """
        
        results = []
        
        # Проверка основных метрик
        core_metrics = ["mrr", "arr", "cac", "ltv", "churn_rate", 
                       "growth_rate", "burn_rate", "runway"]
        
        for metric in core_metrics:
            if metric in metrics and metrics[metric] is not None:
                value = metrics[metric]
                
                # Проверка типа данных
                if not isinstance(value, (int, float)):
                    results.append(ValidationResult(
                        field=metric,
                        rule=ValidationRule.REQUIRED,
                        level=ValidationLevel.ERROR,
                        message=f"Метрика {metric} должна быть числом",
                        value=value,
                        is_valid=False
                    ))
                    continue
                
                # Проверка на отрицательные значения
                if metric in ["mrr", "arr", "cac", "ltv", "burn_rate", "runway"] and value < 0:
                    results.append(ValidationResult(
                        field=metric,
                        rule=ValidationRule.NON_NEGATIVE,
                        level=ValidationLevel.ERROR,
                        message=f"Метрика {metric} не может быть отрицательной",
                        value=value,
                        is_valid=False
                    ))
                
                # Проверка диапазона для процентов
                if metric in ["churn_rate", "growth_rate"]:
                    if value < 0 or value > 1000:  # До 1000% для growth
                        results.append(ValidationResult(
                            field=metric,
                            rule=ValidationRule.WITHIN_RANGE,
                            level=ValidationLevel.WARNING,
                            message=f"Метрика {metric} имеет необычное значение",
                            value=value,
                            expected="0-100% (growth до 1000%)",
                            actual=f"{value}%"
                        ))
        
        # Проверка процентных метрик
        percentage_metrics = ["gross_margin", "net_margin", "expansion_rate"]
        
        for metric in percentage_metrics:
            if metric in metrics and metrics[metric] is not None:
                value = metrics[metric]
                
                if not 0 <= value <= 100:
                    results.append(ValidationResult(
                        field=metric,
                        rule=ValidationRule.VALID_PERCENTAGE,
                        level=ValidationLevel.ERROR,
                        message=f"Процентная метрика {metric} должна быть между 0 и 100",
                        value=value,
                        expected="0-100%",
                        actual=f"{value}%"
                    ))
        
        # Проверка consistency между связанными метриками
        results.extend(self._validate_metric_consistency(metrics))
        
        return results
    
    def _validate_business_logic(self, data: Dict[str, Any]) -> List[ValidationResult]:
        """Валидация business logic"""
        
        results = []
        
        for rule_name, rule_func, message in self.business_rules:
            try:
                if not rule_func(data):
                    results.append(ValidationResult(
                        field="business_logic",
                        rule=ValidationRule.BUSINESS_LOGIC,
                        level=ValidationLevel.WARNING,
                        message=message,
                        value=data,
                        is_valid=False
                    ))
            except Exception as e:
                results.append(ValidationResult(
                    field="business_logic",
                    rule=ValidationRule.BUSINESS_LOGIC,
                    level=ValidationLevel.INFO,
                    message=f"Не удалось проверить правило {rule_name}: {str(e)}",
                    value=data
                ))
        
        # Дополнительные business logic правила
        if "current_mrr" in data and "current_customers" in data:
            mrr = data["current_mrr"]
            customers = data["current_customers"]
            
            if customers > 0:
                arpu = mrr / customers
                
                if arpu < 10:  # Less than $10 per customer
                    results.append(ValidationResult(
                        field="arpu",
                        rule=ValidationRule.BUSINESS_LOGIC,
                        level=ValidationLevel.WARNING,
                        message=f"Средний доход на клиента (${arpu:.2f}) очень низкий",
                        value=arpu,
                        expected="> $10",
                        actual=f"${arpu:.2f}"
                    ))
        
        if "cash_balance" in data and "burn_rate" in data:
            cash = data["cash_balance"]
            burn = data.get("burn_rate", 0)
            
            if burn > 0:
                runway = cash / burn
                
                if runway < 6:
                    results.append(ValidationResult(
                        field="runway",
                        rule=ValidationRule.BUSINESS_LOGIC,
                        level=ValidationLevel.CRITICAL,
                        message=f"Runway всего {runway:.1f} месяцев",
                        value=runway,
                        expected="> 6 месяцев",
                        actual=f"{runway:.1f} месяцев"
                    ))
        
        return results
    
    def _validate_metric_consistency(self, metrics: Dict[str, Any]) -> List[ValidationResult]:
        """Валидация consistency между метриками"""
        
        results = []
        
        # Проверка MRR и ARR
        if "mrr" in metrics and "arr" in metrics:
            mrr = metrics["mrr"]
            arr = metrics["arr"]
            
            expected_arr = mrr * 12
            tolerance = 0.1  # 10% tolerance
            
            if abs(arr - expected_arr) / max(expected_arr, 1) > tolerance:
                results.append(ValidationResult(
                    field="arr_consistency",
                    rule=ValidationRule.CONSISTENT,
                    level=ValidationLevel.WARNING,
                    message=f"ARR (${arr:,.0f}) значительно отличается от MRR * 12 (${expected_arr:,.0f})",
                    value=arr,
                    expected=f"${expected_arr:,.0f}",
                    actual=f"${arr:,.0f}"
                ))
        
        # Проверка LTV и CAC
        if "ltv" in metrics and "cac" in metrics:
            ltv = metrics["ltv"]
            cac = metrics["cac"]
            
            if cac > 0:
                ltv_cac_ratio = ltv / cac
                
                if ltv_cac_ratio < 1.0:
                    results.append(ValidationResult(
                        field="ltv_cac_ratio",
                        rule=ValidationRule.CONSISTENT,
                        level=ValidationLevel.CRITICAL,
                        message=f"LTV/CAC ratio {ltv_cac_ratio:.1f}x ниже 1.0x",
                        value=ltv_cac_ratio,
                        expected=">= 1.0x",
                        actual=f"{ltv_cac_ratio:.1f}x"
                    ))
                elif ltv_cac_ratio < 3.0:
                    results.append(ValidationResult(
                        field="ltv_cac_ratio",
                        rule=ValidationRule.CONSISTENT,
                        level=ValidationLevel.WARNING,
                        message=f"LTV/CAC ratio {ltv_cac_ratio:.1f}x ниже оптимального 3.0x",
                        value=ltv_cac_ratio,
                        expected=">= 3.0x",
                        actual=f"{ltv_cac_ratio:.1f}x"
                    ))
        
        # Проверка churn rate и growth rate
        if "churn_rate" in metrics and "growth_rate" in metrics:
            churn = metrics["churn_rate"]
            growth = metrics["growth_rate"]
            
            if churn > growth and churn > 5:  # Churn превышает growth
                results.append(ValidationResult(
                    field="growth_churn_balance",
                    rule=ValidationRule.CONSISTENT,
                    level=ValidationLevel.WARNING,
                    message=f"Churn rate ({churn:.1f}%) превышает growth rate ({growth:.1f}%)",
                    value={"churn": churn, "growth": growth},
                    expected="Growth > Churn",
                    actual=f"Churn: {churn:.1f}%, Growth: {growth:.1f}%"
                ))
        
        return results
    
    def validate_financial_plan(self, plan_data: Dict[str, Any]) -> List[ValidationResult]:
        """
        Валидация финансового плана
        
        Args:
            plan_data: Данные финансового плана
        
        Returns:
            List результатов валидации
        """
        
        results = []
        
        # Проверка обязательных полей плана
        required_fields = ["plan_name", "plan_year", "company_id"]
        
        for field in required_fields:
            if field not in plan_data or plan_data[field] is None:
                results.append(ValidationResult(
                    field=field,
                    rule=ValidationRule.REQUIRED,
                    level=ValidationLevel.ERROR,
                    message=f"Обязательное поле плана {field} отсутствует",
                    value=None,
                    is_valid=False
                ))
        
        # Проверка дат
        date_fields = ["plan_start_date", "plan_end_date"]
        
        for field in date_fields:
            if field in plan_data and plan_data[field] is not None:
                try:
                    if isinstance(plan_data[field], str):
                        datetime.fromisoformat(plan_data[field].replace('Z', '+00:00'))
                    elif isinstance(plan_data[field], (datetime, date)):
                        pass  # Уже валидная дата
                    else:
                        raise ValueError("Invalid date format")
                except (ValueError, TypeError) as e:
                    results.append(ValidationResult(
                        field=field,
                        rule=ValidationRule.VALID_DATE,
                        level=ValidationLevel.ERROR,
                        message=f"Неверный формат даты для {field}",
                        value=plan_data[field],
                        is_valid=False
                    ))
        
        # Проверка предположений роста
        if "growth_assumptions" in plan_data:
            assumptions = plan_data["growth_assumptions"]
            
            if isinstance(assumptions, dict):
                # Проверка growth rates
                for rate_field in ["mrr_growth_rate", "customer_growth_rate"]:
                    if rate_field in assumptions:
                        rate = assumptions[rate_field]
                        if not 0 <= rate <= 5:  # 0-500%
                            results.append(ValidationResult(
                                field=f"assumptions.{rate_field}",
                                rule=ValidationRule.WITHIN_RANGE,
                                level=ValidationLevel.WARNING,
                                message=f"Rate {rate_field} имеет необычное значение {rate:.1%}",
                                value=rate,
                                expected="0-500%",
                                actual=f"{rate:.1%}"
                            ))
                
                # Проверка churn rate
                if "churn_rate" in assumptions:
                    churn = assumptions["churn_rate"]
                    if not 0 <= churn <= 1:  # 0-100%
                        results.append(ValidationResult(
                            field="assumptions.churn_rate",
                            rule=ValidationRule.WITHIN_RANGE,
                            level=ValidationLevel.ERROR,
                            message=f"Churn rate {churn:.1%} вне диапазона 0-100%",
                            value=churn,
                            expected="0-100%",
                            actual=f"{churn:.1%}"
                        ))
        
        # Проверка месячных планов если есть
        if "monthly_plans" in plan_data and isinstance(plan_data["monthly_plans"], list):
            for i, monthly_plan in enumerate(plan_data["monthly_plans"]):
                if isinstance(monthly_plan, dict):
                    # Проверка ключевых полей месячного плана
                    month_results = self._validate_monthly_plan(monthly_plan, i)
                    results.extend(month_results)
        
        return results
    
    def _validate_monthly_plan(self, monthly_plan: Dict[str, Any], 
                              month_index: int) -> List[ValidationResult]:
        """Валидация месячного плана"""
        
        results = []
        
        # Проверка обязательных полей
        required_fields = ["month_number", "plan_mrr", "plan_total_costs"]
        
        for field in required_fields:
            if field not in monthly_plan or monthly_plan[field] is None:
                results.append(ValidationResult(
                    field=f"monthly_plans[{month_index}].{field}",
                    rule=ValidationRule.REQUIRED,
                    level=ValidationLevel.ERROR,
                    message=f"Обязательное поле {field} отсутствует в месячном плане",
                    value=None,
                    is_valid=False
                ))
        
        # Проверка числовых полей
        if "month_number" in monthly_plan:
            month_num = monthly_plan["month_number"]
            if not 1 <= month_num <= 12:
                results.append(ValidationResult(
                    field=f"monthly_plans[{month_index}].month_number",
                    rule=ValidationRule.WITHIN_RANGE,
                    level=ValidationLevel.ERROR,
                    message=f"Номер месяца должен быть от 1 до 12",
                    value=month_num,
                    expected="1-12",
                    actual=month_num
                ))
        
        # Проверка financial consistency
        if "plan_mrr" in monthly_plan and "plan_total_costs" in monthly_plan:
            mrr = monthly_plan["plan_mrr"]
            costs = monthly_plan["plan_total_costs"]
            
            if mrr < 0 or costs < 0:
                results.append(ValidationResult(
                    field=f"monthly_plans[{month_index}].financials",
                    rule=ValidationRule.NON_NEGATIVE,
                    level=ValidationLevel.ERROR,
                    message="MRR и затраты не могут быть отрицательными",
                    value={"mrr": mrr, "costs": costs},
                    is_valid=False
                ))
            
            # Проверка profit margin
            if mrr > 0:
                profit_margin = (mrr - costs) / mrr
                if profit_margin < -0.5:  # Больше 50% убытков
                    results.append(ValidationResult(
                        field=f"monthly_plans[{month_index}].profit_margin",
                        rule=ValidationRule.BUSINESS_LOGIC,
                        level=ValidationLevel.WARNING,
                        message=f"Profit margin {profit_margin:.1%} очень низкий",
                        value=profit_margin,
                        expected="> -50%",
                        actual=f"{profit_margin:.1%}"
                    ))
        
        return results
    
    def validate_actual_financials(self, actual_data: Dict[str, Any]) -> List[ValidationResult]:
        """
        Валидация фактических финансовых данных
        
        Args:
            actual_data: Фактические данные
        
        Returns:
            List результатов валидации
        """
        
        results = []
        
        # Проверка обязательных полей
        required_fields = ["year", "month_number", "actual_mrr", 
                          "actual_total_revenue", "actual_total_costs"]
        
        for field in required_fields:
            if field not in actual_data or actual_data[field] is None:
                results.append(ValidationResult(
                    field=field,
                    rule=ValidationRule.REQUIRED,
                    level=ValidationLevel.ERROR,
                    message=f"Обязательное поле {field} отсутствует в фактических данных",
                    value=None,
                    is_valid=False
                ))
        
        # Проверка дат
        if "year" in actual_data:
            year = actual_data["year"]
            current_year = datetime.now().year
            
            if not 2020 <= year <= current_year + 5:  # Разумный диапазон
                results.append(ValidationResult(
                    field="year",
                    rule=ValidationRule.WITHIN_RANGE,
                    level=ValidationLevel.WARNING,
                    message=f"Год {year} вне ожидаемого диапазона",
                    value=year,
                    expected=f"2020-{current_year + 5}",
                    actual=year
                ))
        
        if "month_number" in actual_data:
            month_num = actual_data["month_number"]
            if not 1 <= month_num <= 12:
                results.append(ValidationResult(
                    field="month_number",
                    rule=ValidationRule.WITHIN_RANGE,
                    level=ValidationLevel.ERROR,
                    message=f"Номер месяца должен быть от 1 до 12",
                    value=month_num,
                    expected="1-12",
                    actual=month_num
                ))
        
        # Проверка финансовых данных
        financial_fields = ["actual_mrr", "actual_total_revenue", "actual_total_costs",
                          "actual_burn_rate", "actual_runway"]
        
        for field in financial_fields:
            if field in actual_data and actual_data[field] is not None:
                value = actual_data[field]
                
                if isinstance(value, (int, float)):
                    if value < 0 and field != "actual_burn_rate":  # burn_rate может быть отрицательным (прибыль)
                        results.append(ValidationResult(
                            field=field,
                            rule=ValidationRule.NON_NEGATIVE,
                            level=ValidationLevel.ERROR,
                            message=f"Поле {field} не может быть отрицательным",
                            value=value,
                            is_valid=False
                        ))
        
        # Проверка consistency между revenue и costs
        if "actual_total_revenue" in actual_data and "actual_total_costs" in actual_data:
            revenue = actual_data["actual_total_revenue"]
            costs = actual_data["actual_total_costs"]
            
            if revenue > 0 and costs > revenue * 10:  # Costs в 10 раз больше revenue
                results.append(ValidationResult(
                    field="cost_revenue_ratio",
                    rule=ValidationRule.BUSINESS_LOGIC,
                    level=ValidationLevel.WARNING,
                    message="Затраты значительно превышают выручку",
                    value={"revenue": revenue, "costs": costs},
                    expected="Costs < 10x Revenue",
                    actual=f"Costs/Revenue: {costs/revenue:.1f}x"
                ))
        
        return results
    
    def validate_email(self, email: str) -> ValidationResult:
        """
        Валидация email адреса
        
        Args:
            email: Email адрес
        
        Returns:
            Результат валидации
        """
        
        # Простой regex для валидации email
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not email or not isinstance(email, str):
            return ValidationResult(
                field="email",
                rule=ValidationRule.VALID_EMAIL,
                level=ValidationLevel.ERROR,
                message="Email не может быть пустым",
                value=email,
                is_valid=False
            )
        
        if not re.match(email_regex, email):
            return ValidationResult(
                field="email",
                rule=ValidationRule.VALID_EMAIL,
                level=ValidationLevel.ERROR,
                message="Неверный формат email",
                value=email,
                is_valid=False
            )
        
        return ValidationResult(
            field="email",
            rule=ValidationRule.VALID_EMAIL,
            level=ValidationLevel.INFO,
            message="Email валиден",
            value=email,
            is_valid=True
        )
    
    def validate_date_range(self, start_date: Union[str, datetime, date],
                           end_date: Union[str, datetime, date]) -> List[ValidationResult]:
        """
        Валидация диапазона дат
        
        Args:
            start_date: Начальная дата
            end_date: Конечная дата
        
        Returns:
            List результатов валидации
        """
        
        results = []
        
        # Конвертация дат если необходимо
        try:
            if isinstance(start_date, str):
                start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            elif isinstance(start_date, (datetime, date)):
                start = start_date if isinstance(start_date, datetime) else datetime.combine(start_date, datetime.min.time())
            else:
                raise ValueError("Invalid start date format")
            
            if isinstance(end_date, str):
                end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            elif isinstance(end_date, (datetime, date)):
                end = end_date if isinstance(end_date, datetime) else datetime.combine(end_date, datetime.min.time())
            else:
                raise ValueError("Invalid end date format")
            
        except (ValueError, TypeError) as e:
            results.append(ValidationResult(
                field="date_range",
                rule=ValidationRule.VALID_DATE,
                level=ValidationLevel.ERROR,
                message=f"Неверный формат даты: {str(e)}",
                value={"start": start_date, "end": end_date},
                is_valid=False
            ))
            return results
        
        # Проверка что start_date <= end_date
        if start > end:
            results.append(ValidationResult(
                field="date_range",
                rule=ValidationRule.CONSISTENT,
                level=ValidationLevel.ERROR,
                message="Начальная дата должна быть раньше конечной даты",
                value={"start": start, "end": end},
                expected="start <= end",
                actual=f"start: {start}, end: {end}",
                is_valid=False
            ))
        
        # Проверка что диапазон не слишком большой
        days_diff = (end - start).days
        if days_diff > 365 * 5:  # 5 лет
            results.append(ValidationResult(
                field="date_range",
                rule=ValidationRule.BUSINESS_LOGIC,
                level=ValidationLevel.WARNING,
                message=f"Диапазон дат слишком большой ({days_diff} дней)",
                value=days_diff,
                expected="<= 5 лет",
                actual=f"{days_diff} дней"
            ))
        
        # Проверка что даты не в будущем (для фактических данных)
        now = datetime.now()
        if end > now:
            results.append(ValidationResult(
                field="date_range",
                rule=ValidationRule.BUSINESS_LOGIC,
                level=ValidationLevel.WARNING,
                message="Конечная дата в будущем",
                value=end,
                expected=f"<= {now.date()}",
                actual=f"{end.date()}"
            ))
        
        return results
    
    def validate_percentage(self, value: float, field_name: str = "percentage") -> ValidationResult:
        """
        Валидация процентного значения
        
        Args:
            value: Значение процента
            field_name: Название поля
        
        Returns:
            Результат валидации
        """
        
        if not isinstance(value, (int, float)):
            return ValidationResult(
                field=field_name,
                rule=ValidationRule.VALID_PERCENTAGE,
                level=ValidationLevel.ERROR,
                message="Процент должен быть числом",
                value=value,
                is_valid=False
            )
        
        if value < 0 or value > 100:
            return ValidationResult(
                field=field_name,
                rule=ValidationRule.VALID_PERCENTAGE,
                level=ValidationLevel.ERROR,
                message="Процент должен быть между 0 и 100",
                value=value,
                expected="0-100",
                actual=value,
                is_valid=False
            )
        
        return ValidationResult(
            field=field_name,
            rule=ValidationRule.VALID_PERCENTAGE,
            level=ValidationLevel.INFO,
            message="Процент валиден",
            value=value,
            is_valid=True
        )
    
    def summarize_validation_results(self, results: List[ValidationResult]) -> Dict[str, Any]:
        """
        Суммаризация результатов валидации
        
        Args:
            results: Список результатов валидации
        
        Returns:
            Dict с суммаризацией
        """
        
        summary = {
            "total_checks": len(results),
            "valid": 0,
            "invalid": 0,
            "by_level": {
                "info": 0,
                "warning": 0,
                "error": 0,
                "critical": 0
            },
            "by_rule": {},
            "has_errors": False,
            "has_critical": False,
            "messages": []
        }
        
        for result in results:
            # Подсчет по уровню
            level = result.level.value
            summary["by_level"][level] = summary["by_level"].get(level, 0) + 1
            
            # Подсчет по правилу
            rule = result.rule.value
            summary["by_rule"][rule] = summary["by_rule"].get(rule, 0) + 1
            
            # Подсчет valid/invalid
            if result.is_valid:
                summary["valid"] += 1
            else:
                summary["invalid"] += 1
            
            # Проверка наличия ошибок
            if result.level in [ValidationLevel.ERROR, ValidationLevel.CRITICAL]:
                summary["has_errors"] = True
            
            if result.level == ValidationLevel.CRITICAL:
                summary["has_critical"] = True
            
            # Сбор сообщений
            if result.level in [ValidationLevel.ERROR, ValidationLevel.CRITICAL, ValidationLevel.WARNING]:
                summary["messages"].append({
                    "level": result.level.value,
                    "field": result.field,
                    "message": result.message,
                    "value": result.value
                })
        
        # Определение общего статуса
        if summary["has_critical"]:
            summary["overall_status"] = "critical"
            summary["overall_message"] = "Есть критические ошибки валидации"
        elif summary["has_errors"]:
            summary["overall_status"] = "error"
            summary["overall_message"] = "Есть ошибки валидации"
        elif summary["by_level"]["warning"] > 0:
            summary["overall_status"] = "warning"
            summary["overall_message"] = "Есть предупреждения валидации"
        else:
            summary["overall_status"] = "valid"
            summary["overall_message"] = "Все данные валидны"
        
        return summary
    
    def get_validation_schema(self, data_type: str) -> Dict[str, Any]:
        """
        Получение схемы валидации для типа данных
        
        Args:
            data_type: Тип данных (company, metrics, plan, actuals)
        
        Returns:
            Dict со схемой валидации
        """
        
        schemas = {
            "company": {
                "description": "Схема валидации данных компании",
                "required_fields": ["company_name", "stage", "current_mrr", 
                                   "current_customers", "monthly_price", "team_size"],
                "optional_fields": ["cash_balance", "founding_date", "website", "description"],
                "validation_rules": self._get_rules_for_fields([
                    "company_name", "stage", "current_mrr", "current_customers",
                    "monthly_price", "team_size", "cash_balance"
                ])
            },
            "metrics": {
                "description": "Схема валидации финансовых метрик",
                "required_fields": ["mrr", "growth_rate"],
                "optional_fields": ["arr", "cac", "ltv", "churn_rate", 
                                   "burn_rate", "runway", "gross_margin"],
                "validation_rules": self._get_rules_for_fields([
                    "mrr", "arr", "cac", "ltv", "churn_rate", "growth_rate",
                    "burn_rate", "runway", "gross_margin"
                ])
            },
            "plan": {
                "description": "Схема валидации финансового плана",
                "required_fields": ["plan_name", "plan_year", "company_id"],
                "optional_fields": ["description", "assumptions", "monthly_plans"],
                "validation_rules": {
                    "plan_name": [ValidationRule.REQUIRED],
                    "plan_year": [ValidationRule.REQUIRED, ValidationRule.WITHIN_RANGE],
                    "company_id": [ValidationRule.REQUIRED]
                }
            },
            "actuals": {
                "description": "Схема валидации фактических данных",
                "required_fields": ["year", "month_number", "actual_mrr", 
                                   "actual_total_revenue", "actual_total_costs"],
                "optional_fields": ["actual_burn_rate", "actual_runway", 
                                   "actual_new_customers", "actual_churned_customers"],
                "validation_rules": self._get_rules_for_fields([
                    "year", "month_number", "actual_mrr", "actual_total_revenue",
                    "actual_total_costs", "actual_burn_rate", "actual_runway"
                ])
            }
        }
        
        return schemas.get(data_type, {})

    def _get_rules_for_fields(self, fields: List[str]) -> Dict[str, List[ValidationRule]]:
        """Получение правил валидации для списка полей"""
        
        rules = {}
        for field in fields:
            if field in self.validation_rules:
                rules[field] = self.validation_rules[field]
        
        return rules

# Создаем глобальный экземпляр валидатора
data_validator = DataValidator()

# Экспортируем полезные функции
def validate_company_input(company_data: Dict[str, Any]) -> Dict[str, Any]:
    """Публичная функция для валидации данных компании"""
    results = data_validator.validate_company_data(company_data)
    summary = data_validator.summarize_validation_results(results)
    
    return {
        "results": [r.__dict__ for r in results],
        "summary": summary,
        "is_valid": not summary["has_errors"]
    }

def validate_financial_metrics(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Публичная функция для валидации финансовых метрик"""
    results = data_validator.validate_financial_metrics(metrics)
    summary = data_validator.summarize_validation_results(results)
    
    return {
        "results": [r.__dict__ for r in results],
        "summary": summary,
        "is_valid": not summary["has_errors"]
    }

def get_validation_schema(schema_type: str) -> Dict[str, Any]:
    """Публичная функция для получения схемы валидации"""
    return data_validator.get_validation_schema(schema_type)