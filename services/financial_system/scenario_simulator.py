"""
Симулятор сценариев "что если" для SaaS компаний
Анализ impact различных стратегий и внешних факторов
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
import plotly.graph_objects as go
from enum import Enum

from services.utils.math_utils import safe_divide

class ScenarioType(Enum):
    """Типы сценариев"""
    GROWTH_ACCELERATION = "growth_acceleration"
    COST_REDUCTION = "cost_reduction"
    FUNDRAISING = "fundraising"
    MARKET_DOWNTURN = "market_downturn"
    PRICING_CHANGE = "pricing_change"
    TEAM_EXPANSION = "team_expansion"
    PRODUCT_LAUNCH = "product_launch"
    CUSTOM = "custom"

@dataclass
class ScenarioParameter:
    """Параметр сценария"""
    name: str
    current_value: float
    scenario_value: float
    change_percent: float
    impact_weight: float = 1.0

@dataclass
class ScenarioResult:
    """Результат сценария"""
    scenario_id: str
    scenario_type: str
    name: str
    description: str
    parameters: List[ScenarioParameter]
    base_outcomes: Dict[str, float]
    scenario_outcomes: Dict[str, float]
    impact_analysis: Dict[str, Any]
    recommendations: List[str]
    created_at: datetime = field(default_factory=datetime.now)

class ScenarioSimulator:
    """
    Симулятор сценариев для SaaS компаний
    Анализ impact различных стратегий и внешних факторов
    """
    
    def __init__(self):
        self.scenario_templates = self._create_scenario_templates()
        
    def _create_scenario_templates(self) -> Dict[str, Dict[str, Any]]:
        """Создание шаблонов сценариев"""
        
        templates = {
            "growth_acceleration": {
                "name": "Ускорение Роста",
                "description": "Сценарий ускоренного роста выручки",
                "parameters": {
                    "mrr_growth_rate": {"change": 0.3, "impact": "high"},  # +30%
                    "customer_growth_rate": {"change": 0.25, "impact": "high"},
                    "marketing_budget": {"change": 0.2, "impact": "medium"},
                    "sales_team_size": {"change": 0.15, "impact": "medium"}
                },
                "duration_months": 12,
                "probability": 0.4
            },
            "cost_reduction": {
                "name": "Сокращение Расходов",
                "description": "Сценарий оптимизации расходов",
                "parameters": {
                    "salaries": {"change": -0.15, "impact": "high"},  # -15%
                    "marketing_budget": {"change": -0.1, "impact": "medium"},
                    "cloud_costs": {"change": -0.2, "impact": "low"},
                    "other_opex": {"change": -0.25, "impact": "medium"}
                },
                "duration_months": 6,
                "probability": 0.6
            },
            "fundraising": {
                "name": "Fundraising Раунд",
                "description": "Сценарий успешного fundraising",
                "parameters": {
                    "cash_balance": {"change": 2.0, "impact": "high"},  # +200%
                    "runway": {"change": 1.5, "impact": "high"},  # +150%
                    "team_size": {"change": 0.3, "impact": "medium"},
                    "marketing_budget": {"change": 0.4, "impact": "high"}
                },
                "duration_months": 18,
                "probability": 0.3
            },
            "market_downturn": {
                "name": "Рыночный Спад",
                "description": "Сценарий экономического спада",
                "parameters": {
                    "mrr_growth_rate": {"change": -0.4, "impact": "high"},  # -40%
                    "customer_growth_rate": {"change": -0.35, "impact": "high"},
                    "churn_rate": {"change": 0.2, "impact": "medium"},  # +20%
                    "cac": {"change": 0.15, "impact": "medium"}  # +15%
                },
                "duration_months": 12,
                "probability": 0.2
            },
            "pricing_increase": {
                "name": "Увеличение Цен",
                "description": "Сценарий увеличения цен",
                "parameters": {
                    "average_price": {"change": 0.2, "impact": "high"},  # +20%
                    "mrr_per_customer": {"change": 0.15, "impact": "high"},
                    "churn_rate": {"change": 0.05, "impact": "medium"},  # +5%
                    "new_customers": {"change": -0.1, "impact": "low"}  # -10%
                },
                "duration_months": 6,
                "probability": 0.5
            }
        }
        
        return templates
    
    def run_scenario(self, company_id: int, 
                    scenario_type: str,
                    custom_parameters: Optional[Dict[str, float]] = None,
                    duration_months: int = 12) -> Dict[str, Any]:
        """
        Запуск сценария
        
        Args:
            company_id: ID компании
            scenario_type: Тип сценария
            custom_parameters: Кастомные параметры (опционально)
            duration_months: Длительность сценария в месяцах
        
        Returns:
            Dict с результатами сценария
        """
        
        # Получение данных компании
        company_data = self._get_company_data(company_id)
        
        if not company_data:
            return {
                "success": False,
                "error": "Company data not found"
            }
        
        # Получение базовых метрик
        base_metrics = self._get_base_metrics(company_data)
        
        # Применение шаблона сценария
        if scenario_type in self.scenario_templates:
            scenario_template = self.scenario_templates[scenario_type]
            scenario_params = self._apply_scenario_template(
                base_metrics, scenario_template, custom_parameters
            )
        else:
            # Custom сценарий
            scenario_params = self._create_custom_scenario(
                base_metrics, custom_parameters or {}
            )
            scenario_template = {
                "name": "Custom Scenario",
                "description": "Пользовательский сценарий",
                "duration_months": duration_months
            }
        
        # Симуляция сценария
        scenario_results = self._simulate_scenario(
            company_data, base_metrics, scenario_params, duration_months
        )
        
        # Сравнение с базовым сценарием
        comparison = self._compare_with_base(scenario_results, base_metrics)
        
        # Анализ impact
        impact_analysis = self._analyze_impact(scenario_results, comparison)
        
        # Генерация рекомендаций
        recommendations = self._generate_scenario_recommendations(
            scenario_type, scenario_results, impact_analysis
        )
        
        # Создание результата
        result = ScenarioResult(
            scenario_id=f"{company_id}_{scenario_type}_{datetime.now().timestamp()}",
            scenario_type=scenario_type,
            name=scenario_template["name"],
            description=scenario_template["description"],
            parameters=scenario_params,
            base_outcomes=base_metrics,
            scenario_outcomes=scenario_results["final_metrics"],
            impact_analysis=impact_analysis,
            recommendations=recommendations
        )
        
        # Визуализации
        visualizations = self._create_scenario_visualizations(
            scenario_results, comparison, scenario_template["name"]
        )
        
        return {
            "success": True,
            "scenario": self._scenario_result_to_dict(result),
            "simulation_results": scenario_results,
            "comparison": comparison,
            "impact_analysis": impact_analysis,
            "recommendations": recommendations,
            "visualizations": visualizations,
            "key_insights": self._extract_scenario_insights(result, impact_analysis)
        }
    
    def _get_company_data(self, company_id: int) -> Optional[Dict[str, Any]]:
        """Получение данных компании"""
        
        from database.db_manager import db_manager
        
        company = db_manager.get_company(company_id)
        if not company:
            return None
        
        # Получение финансовых данных
        financials = db_manager.get_actual_financials_by_filters(
            {"company_id": company_id}
        )
        
        # Конвертация в dict
        company_dict = company.to_dict()
        company_dict["financials"] = [f.to_dict() for f in financials]
        
        return company_dict
    
    def _get_base_metrics(self, company_data: Dict[str, Any]) -> Dict[str, float]:
        """Получение базовых метрик компании"""
        
        # Извлекаем последние фактические данные
        financials = company_data.get("financials", [])
        
        if financials:
            latest_financial = max(financials, key=lambda x: (x["year"], x["month_number"]))
            
            base_metrics = {
                "mrr": latest_financial.get("actual_mrr", company_data.get("current_mrr", 0)),
                "customers": company_data.get("current_customers", 0),
                "burn_rate": latest_financial.get("actual_burn_rate", 0),
                "runway": latest_financial.get("actual_runway", 0),
                "cash_balance": company_data.get("cash_balance", 0),
                "monthly_growth_rate": 0.1,  # Default 10%
                "churn_rate": 0.05,  # Default 5%
                "cac": 1000.0,  # Default CAC
                "average_price": company_data.get("monthly_price", 100)
            }
        else:
            # Если нет финансовых данных, используем company data
            base_metrics = {
                "mrr": company_data.get("current_mrr", 0),
                "customers": company_data.get("current_customers", 0),
                "burn_rate": 10000,  # Default
                "runway": 12,  # Default
                "cash_balance": company_data.get("cash_balance", 0),
                "monthly_growth_rate": 0.1,
                "churn_rate": 0.05,
                "cac": 1000.0,
                "average_price": company_data.get("monthly_price", 100)
            }
        
        return base_metrics
    
    def _apply_scenario_template(self, base_metrics: Dict[str, float],
                                template: Dict[str, Any],
                                custom_parameters: Optional[Dict[str, float]]) -> List[ScenarioParameter]:
        """Применение шаблона сценария"""
        
        parameters = []
        template_params = template.get("parameters", {})
        
        # Применяем параметры из шаблона
        for param_name, param_config in template_params.items():
            if param_name in base_metrics:
                current_value = base_metrics[param_name]
                change = param_config["change"]
                
                # Применяем custom параметры если есть
                if custom_parameters and param_name in custom_parameters:
                    scenario_value = custom_parameters[param_name]
                    change_percent = (scenario_value - current_value) / current_value if current_value != 0 else 0
                else:
                    scenario_value = current_value * (1 + change)
                    change_percent = change
                
                # Определяем impact weight
                impact_weight = {"high": 3.0, "medium": 2.0, "low": 1.0}.get(
                    param_config.get("impact", "medium"), 1.0
                )
                
                parameters.append(ScenarioParameter(
                    name=param_name,
                    current_value=current_value,
                    scenario_value=scenario_value,
                    change_percent=change_percent,
                    impact_weight=impact_weight
                ))
        
        # Добавляем custom параметры которых нет в шаблоне
        if custom_parameters:
            for param_name, param_value in custom_parameters.items():
                if param_name in base_metrics and not any(p.name == param_name for p in parameters):
                    current_value = base_metrics[param_name]
                    change_percent = (param_value - current_value) / current_value if current_value != 0 else 0
                    
                    parameters.append(ScenarioParameter(
                        name=param_name,
                        current_value=current_value,
                        scenario_value=param_value,
                        change_percent=change_percent,
                        impact_weight=1.0
                    ))
        
        return parameters
    
    def _create_custom_scenario(self, base_metrics: Dict[str, float],
                               custom_parameters: Dict[str, float]) -> List[ScenarioParameter]:
        """Создание custom сценария"""
        
        parameters = []
        
        for param_name, param_value in custom_parameters.items():
            if param_name in base_metrics:
                current_value = base_metrics[param_name]
                change_percent = (param_value - current_value) / current_value if current_value != 0 else 0
                
                parameters.append(ScenarioParameter(
                    name=param_name,
                    current_value=current_value,
                    scenario_value=param_value,
                    change_percent=change_percent,
                    impact_weight=1.0
                ))
        
        return parameters
    
    def _simulate_scenario(self, company_data: Dict[str, Any],
                          base_metrics: Dict[str, float],
                          scenario_params: List[ScenarioParameter],
                          duration_months: int) -> Dict[str, Any]:
        """Симуляция сценария"""
        
        # Создаем словарь параметров сценария
        scenario_dict = {p.name: p.scenario_value for p in scenario_params}
        
        # Инициализация переменных
        current_mrr = base_metrics["mrr"]
        current_customers = base_metrics["customers"]
        current_cash = base_metrics["cash_balance"]
        
        # Параметры сценария
        growth_rate = scenario_dict.get("monthly_growth_rate", base_metrics["monthly_growth_rate"])
        churn_rate = scenario_dict.get("churn_rate", base_metrics["churn_rate"])
        cac = scenario_dict.get("cac", base_metrics["cac"])
        average_price = scenario_dict.get("average_price", base_metrics["average_price"])
        
        # Burn rate components
        salaries = scenario_dict.get("salaries", 0)
        marketing_budget = scenario_dict.get("marketing_budget", 0)
        cloud_costs = scenario_dict.get("cloud_costs", 0)
        other_opex = scenario_dict.get("other_opex", 0)
        
        # Если burn rate компоненты не заданы, используем базовый burn rate
        if salaries == 0 and marketing_budget == 0 and cloud_costs == 0 and other_opex == 0:
            base_burn = base_metrics["burn_rate"]
            salaries = base_burn * 0.6  # 60% на зарплаты
            marketing_budget = base_burn * 0.2  # 20% на маркетинг
            cloud_costs = base_burn * 0.1  # 10% на облако
            other_opex = base_burn * 0.1  # 10% на прочие расходы
        
        # Симуляция по месяцам
        monthly_results = []
        
        for month in range(1, duration_months + 1):
            # Расчет новых клиентов на основе marketing budget
            new_customers = int(marketing_budget / cac) if cac > 0 else 0
            
            # Churned customers
            churned_customers = int(current_customers * churn_rate)
            
            # Обновление количества клиентов
            current_customers = current_customers + new_customers - churned_customers
            
            # Расчет MRR
            if month == 1:
                current_mrr = base_metrics["mrr"]
            else:
                # MRR growth from existing customers (expansion)
                expansion_revenue = current_mrr * growth_rate * 0.3  # 30% роста от существующих
                
                # New customer revenue
                new_customer_revenue = new_customers * average_price
                
                # Churned revenue
                churned_revenue = churned_customers * average_price
                
                # Total MRR
                current_mrr = current_mrr + expansion_revenue + new_customer_revenue - churned_revenue
            
            # Расчет расходов
            total_costs = salaries + marketing_budget + cloud_costs + other_opex
            
            # Расчет cash flow
            cash_flow = current_mrr - total_costs
            current_cash += cash_flow
            
            # Расчет runway
            if cash_flow < 0:
                runway = current_cash / abs(cash_flow)
            else:
                runway = float('inf')
            
            # Сохранение monthly results
            monthly_results.append({
                "month": month,
                "mrr": current_mrr,
                "customers": current_customers,
                "new_customers": new_customers,
                "churned_customers": churned_customers,
                "revenue": current_mrr,
                "costs": total_costs,
                "cash_flow": cash_flow,
                "cash_balance": current_cash,
                "runway": runway if runway != float('inf') else 999
            })
        
        # Итоговые метрики
        final_metrics = {
            "ending_mrr": current_mrr,
            "ending_customers": current_customers,
            "ending_cash": current_cash,
            "ending_runway": monthly_results[-1]["runway"] if monthly_results else 0,
            "total_revenue": sum(r["revenue"] for r in monthly_results),
            "total_costs": sum(r["costs"] for r in monthly_results),
            "total_profit": sum(r["cash_flow"] for r in monthly_results),
            "avg_monthly_growth": self._calculate_average_growth(monthly_results, "mrr"),
            "peak_cash_requirement": self._calculate_peak_cash_requirement(monthly_results),
            "breakeven_month": self._find_breakeven_month(monthly_results)
        }
        
        return {
            "monthly_results": monthly_results,
            "final_metrics": final_metrics,
            "scenario_parameters": scenario_dict
        }
    
    def _calculate_average_growth(self, monthly_results: List[Dict], metric: str) -> float:
        """Расчет среднего роста"""
        
        if len(monthly_results) < 2:
            return 0
        
        growth_rates = []
        for i in range(1, len(monthly_results)):
            prev_value = monthly_results[i-1][metric]
            curr_value = monthly_results[i][metric]
            
            if prev_value > 0:
                growth_rate = safe_divide(curr_value - prev_value, prev_value)
                growth_rates.append(growth_rate)
        
        return np.mean(growth_rates) if growth_rates else 0
    
    def _calculate_peak_cash_requirement(self, monthly_results: List[Dict]) -> float:
        """Расчет peak cash requirement"""
        
        if not monthly_results:
            return 0
        
        cash_balances = [r["cash_balance"] for r in monthly_results]
        min_cash = min(cash_balances)
        
        # Если минимальный баланс отрицательный, это cash requirement
        return abs(min(0, min_cash))
    
    def _find_breakeven_month(self, monthly_results: List[Dict]) -> Optional[int]:
        """Нахождение месяца breakeven"""
        
        for i, month in enumerate(monthly_results):
            if month["cash_flow"] >= 0:
                # Проверяем что все последующие месяцы также positive
                future_positive = all(
                    m["cash_flow"] >= 0 
                    for m in monthly_results[i:min(i+3, len(monthly_results))]
                )
                
                if future_positive:
                    return i + 1  # Month numbers start from 1
        
        return None
    
    def _compare_with_base(self, scenario_results: Dict[str, Any],
                          base_metrics: Dict[str, float]) -> Dict[str, Any]:
        """Сравнение с базовым сценарием"""
        
        comparison = {
            "metrics_comparison": {},
            "percentage_changes": {},
            "key_differences": []
        }
        
        final_metrics = scenario_results["final_metrics"]
        
        # Сравнение ключевых метрик
        key_metrics = ["ending_mrr", "ending_customers", "ending_cash", "ending_runway"]
        
        for metric in key_metrics:
            if metric in final_metrics and metric.replace("ending_", "") in base_metrics:
                base_key = metric.replace("ending_", "")
                scenario_value = final_metrics[metric]
                base_value = base_metrics[base_key]
                
                if base_value != 0:
                    change_percent = safe_divide(scenario_value - base_value, base_value) * 100
                else:
                    change_percent = 100 if scenario_value > 0 else 0
                
                comparison["metrics_comparison"][metric] = {
                    "base": base_value,
                    "scenario": scenario_value,
                    "absolute_change": scenario_value - base_value,
                    "percent_change": change_percent
                }
                
                # Добавляем в key differences если изменение значительное
                if abs(change_percent) > 20:
                    comparison["key_differences"].append({
                        "metric": metric,
                        "change_percent": change_percent,
                        "impact": "positive" if change_percent > 0 else "negative"
                    })
        
        # Сравнение growth rates
        if "avg_monthly_growth" in final_metrics:
            scenario_growth = final_metrics["avg_monthly_growth"] * 100  # в процентах
            base_growth = base_metrics.get("monthly_growth_rate", 0.1) * 100
            
            comparison["metrics_comparison"]["growth_rate"] = {
                "base": base_growth,
                "scenario": scenario_growth,
                "absolute_change": scenario_growth - base_growth,
                "percent_change": safe_divide(scenario_growth - base_growth, base_growth) * 100 if base_growth != 0 else 0
            }
        
        # Сравнение runway
        if "ending_runway" in final_metrics:
            scenario_runway = final_metrics["ending_runway"]
            base_runway = base_metrics.get("runway", 12)
            
            runway_change = scenario_runway - base_runway
            comparison["metrics_comparison"]["runway_change"] = {
                "base": base_runway,
                "scenario": scenario_runway,
                "months_change": runway_change,
                "percent_change": safe_divide(runway_change, base_runway) * 100 if base_runway != 0 else 0
            }
            
            if abs(runway_change) > 3:  # Изменение на 3+ месяца значительное
                comparison["key_differences"].append({
                    "metric": "runway",
                    "months_change": runway_change,
                    "impact": "positive" if runway_change > 0 else "negative"
                })
        
        return comparison
    
    def _analyze_impact(self, scenario_results: Dict[str, Any],
                       comparison: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ impact сценария"""
        
        impact = {
            "financial_impact": {},
            "strategic_impact": {},
            "risk_analysis": {},
            "sensitivity_analysis": {}
        }
        
        final_metrics = scenario_results["final_metrics"]
        
        # Financial impact
        ending_cash = final_metrics.get("ending_cash", 0)
        total_profit = final_metrics.get("total_profit", 0)
        peak_cash_requirement = final_metrics.get("peak_cash_requirement", 0)
        
        impact["financial_impact"] = {
            "ending_cash": ending_cash,
            "total_profit": total_profit,
            "profitability_trend": "improving" if total_profit > 0 else "worsening",
            "cash_requirement": peak_cash_requirement,
            "breakeven_month": final_metrics.get("breakeven_month"),
            "runway_impact": self._assess_runway_impact(final_metrics.get("ending_runway", 0))
        }
        
        # Strategic impact
        ending_mrr = final_metrics.get("ending_mrr", 0)
        ending_customers = final_metrics.get("ending_customers", 0)
        avg_growth = final_metrics.get("avg_monthly_growth", 0)
        
        impact["strategic_impact"] = {
            "scale_impact": self._assess_scale_impact(ending_mrr),
            "growth_impact": self._assess_growth_impact(avg_growth),
            "market_position_impact": self._assess_market_position_impact(ending_customers),
            "valuation_impact": self._estimate_valuation_impact(ending_mrr, avg_growth)
        }
        
        # Risk analysis
        monthly_results = scenario_results.get("monthly_results", [])
        
        impact["risk_analysis"] = {
            "cash_risk": self._assess_cash_risk(monthly_results),
            "growth_risk": self._assess_growth_risk(monthly_results),
            "execution_risk": self._assess_execution_risk(scenario_results),
            "market_risk": self._assess_market_risk(scenario_results)
        }
        
        # Sensitivity analysis
        impact["sensitivity_analysis"] = self._perform_sensitivity_analysis(
            scenario_results, comparison
        )
        
        return impact
    
    def _assess_runway_impact(self, runway: float) -> Dict[str, Any]:
        """Оценка impact на runway"""
        
        if runway == float('inf') or runway > 24:
            return {
                "level": "excellent",
                "description": "Более 2 лет runway, отличная позиция",
                "implication": "Можно фокусироваться на growth а не на survival"
            }
        elif runway >= 18:
            return {
                "level": "very_good",
                "description": "Более 1.5 лет runway",
                "implication": "Хорошая позиция для стратегических инвестиций"
            }
        elif runway >= 12:
            return {
                "level": "good",
                "description": "1+ год runway",
                "implication": "Стабильная позиция, можно планировать рост"
            }
        elif runway >= 9:
            return {
                "level": "warning",
                "description": "Менее года runway",
                "implication": "Требуется внимание к финансам"
            }
        elif runway >= 6:
            return {
                "level": "concerning",
                "description": "Менее 9 месяцев",
                "implication": "Срочно требуется action"
            }
        elif runway >= 3:
            return {
                "level": "critical",
                "description": "Менее 6 месяцев",
                "implication": "Emergency меры необходимы"
            }
        else:
            return {
                "level": "emergency",
                "description": "Критически мало времени",
                "implication": "Немедленные действия required"
            }
    
    def _assess_scale_impact(self, mrr: float) -> Dict[str, Any]:
        """Оценка impact на масштаб"""
        
        if mrr >= 10000000:  # $10M+ ARR
            return {
                "level": "enterprise",
                "description": "Enterprise scale",
                "implication": "Можно конкурировать с крупными игроками"
            }
        elif mrr >= 1000000:  # $1M+ ARR
            return {
                "level": "growth",
                "description": "Growth stage",
                "implication": "Масштабируемый бизнес"
            }
        elif mrr >= 100000:  # $100k+ ARR
            return {
                "level": "established",
                "description": "Established business",
                "implication": "Доказанная бизнес-модель"
            }
        elif mrr >= 10000:  # $10k+ ARR
            return {
                "level": "early_traction",
                "description": "Early traction",
                "implication": "Продукт нашел рынок"
            }
        else:
            return {
                "level": "pre_revenue",
                "description": "Pre-revenue or early",
                "implication": "Фокус на product-market fit"
            }
    
    def _assess_growth_impact(self, growth_rate: float) -> Dict[str, Any]:
        """Оценка impact на рост"""
        
        monthly_growth = growth_rate * 100  # в процентах
        
        if monthly_growth >= 20:
            return {
                "level": "hypergrowth",
                "description": "Hypergrowth (>20%/мес)",
                "implication": "Очень быстрое масштабирование"
            }
        elif monthly_growth >= 15:
            return {
                "level": "high_growth",
                "description": "High growth (15-20%/мес)",
                "implication": "Быстрое масштабирование"
            }
        elif monthly_growth >= 10:
            return {
                "level": "strong_growth",
                "description": "Strong growth (10-15%/мес)",
                "implication": "Устойчивый рост"
            }
        elif monthly_growth >= 5:
            return {
                "level": "moderate_growth",
                "description": "Moderate growth (5-10%/мес)",
                "implication": "Стабильный рост"
            }
        else:
            return {
                "level": "slow_growth",
                "description": "Slow growth (<5%/мес)",
                "implication": "Требуется ускорение роста"
            }
    
    def _assess_market_position_impact(self, customers: int) -> Dict[str, Any]:
        """Оценка impact на рыночную позицию"""
        
        if customers >= 10000:
            return {
                "level": "market_leader",
                "description": "Large customer base",
                "implication": "Сильная рыночная позиция"
            }
        elif customers >= 1000:
            return {
                "level": "established_player",
                "description": "Established customer base",
                "implication": "Значительное присутствие на рынке"
            }
        elif customers >= 100:
            return {
                "level": "growing_presence",
                "description": "Growing customer base",
                "implication": "Развивающееся присутствие на рынке"
            }
        elif customers >= 10:
            return {
                "level": "early_adopters",
                "description": "Early adopter base",
                "implication": "Доказательство концепции"
            }
        else:
            return {
                "level": "very_early",
                "description": "Very early stage",
                "implication": "Фокус на первых клиентах"
            }
    
    def _estimate_valuation_impact(self, mrr: float, growth_rate: float) -> Dict[str, Any]:
        """Оценка impact на valuation"""
        
        # Простая оценка valuation (ARR * multiple)
        arr = mrr * 12
        multiple = 10 if growth_rate >= 0.15 else 8 if growth_rate >= 0.1 else 6
        
        valuation = arr * multiple
        
        return {
            "estimated_arr": arr,
            "growth_multiple": multiple,
            "estimated_valuation": valuation,
            "valuation_range": f"${valuation*0.7:,.0f} - ${valuation*1.3:,.0f}",
            "assumptions": "Based on industry standard SaaS multiples"
        }
    
    def _assess_cash_risk(self, monthly_results: List[Dict]) -> Dict[str, Any]:
        """Оценка cash risk"""
        
        if not monthly_results:
            return {"level": "unknown", "description": "No data"}
        
        cash_balances = [r["cash_balance"] for r in monthly_results]
        min_cash = min(cash_balances)
        
        if min_cash <= 0:
            return {
                "level": "high",
                "description": "Negative cash balance projected",
                "implication": "Требуется дополнительное финансирование"
            }
        elif min_cash < 10000:
            return {
                "level": "medium",
                "description": "Very low cash balance",
                "implication": "Небольшой margin for error"
            }
        else:
            return {
                "level": "low",
                "description": "Adequate cash reserves",
                "implication": "Хорошая финансовая устойчивость"
            }
    
    def _assess_growth_risk(self, monthly_results: List[Dict]) -> Dict[str, Any]:
        """Оценка growth risk"""
        
        if len(monthly_results) < 3:
            return {"level": "unknown", "description": "Insufficient data"}
        
        mrr_values = [r["mrr"] for r in monthly_results]
        growth_rates = []
        
        for i in range(1, len(mrr_values)):
            if mrr_values[i-1] > 0:
                growth_rate = safe_divide(mrr_values[i] - mrr_values[i-1], mrr_values[i-1])
                growth_rates.append(growth_rate)
        
        if not growth_rates:
            return {"level": "high", "description": "No growth", "implication": "Business may be stagnant"}
        
        avg_growth = np.mean(growth_rates)
        volatility = np.std(growth_rates)
        
        if avg_growth <= 0:
            return {
                "level": "critical",
                "description": "Negative growth",
                "implication": "Business is declining"
            }
        elif avg_growth < 0.05:
            return {
                "level": "high",
                "description": "Very slow growth",
                "implication": "May not reach scale"
            }
        elif volatility > avg_growth:
            return {
                "level": "medium",
                "description": "Volatile growth",
                "implication": "Unpredictable performance"
            }
        else:
            return {
                "level": "low",
                "description": "Stable growth",
                "implication": "Predictable scaling"
            }
    
    def _assess_execution_risk(self, scenario_results: Dict[str, Any]) -> Dict[str, Any]:
        """Оценка execution risk"""
        
        # Оценка based на агрессивности сценария
        parameters = scenario_results.get("scenario_parameters", {})
        
        aggressive_changes = 0
        for param_name, param_value in parameters.items():
            # Проверяем на агрессивные изменения
            if "growth" in param_name and param_value > 0.3:
                aggressive_changes += 1
            elif "cost" in param_name and param_value < -0.2:
                aggressive_changes += 1
        
        if aggressive_changes >= 3:
            return {
                "level": "high",
                "description": "Very aggressive scenario",
                "implication": "High execution难度"
            }
        elif aggressive_changes >= 2:
            return {
                "level": "medium",
                "description": "Aggressive scenario",
                "implication": "Challenging but achievable"
            }
        else:
            return {
                "level": "low",
                "description": "Realistic scenario",
                "implication": "Achievable with good execution"
            }
    
    def _assess_market_risk(self, scenario_results: Dict[str, Any]) -> Dict[str, Any]:
        """Оценка market risk"""
        
        # Здесь можно добавить анализ market conditions
        # Пока используем простую оценку
        
        return {
            "level": "medium",  # Default
            "description": "Standard market risk",
            "implication": "Market conditions may affect results",
            "factors": [
                "Competitive landscape",
                "Economic conditions",
                "Customer demand",
                "Regulatory environment"
            ]
        }
    
    def _perform_sensitivity_analysis(self, scenario_results: Dict[str, Any],
                                     comparison: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение sensitivity analysis"""
        
        sensitivity = {
            "key_drivers": [],
            "break_even_analysis": {},
            "what_if_scenarios": []
        }
        
        # Определяем key drivers
        metrics_comparison = comparison.get("metrics_comparison", {})
        
        for metric, data in metrics_comparison.items():
            change_percent = abs(data.get("percent_change", 0))
            
            if change_percent > 20:  # Significant change
                sensitivity["key_drivers"].append({
                    "metric": metric,
                    "impact_percent": change_percent,
                    "direction": "positive" if data.get("percent_change", 0) > 0 else "negative"
                })
        
        # Break-even analysis
        breakeven_month = scenario_results["final_metrics"].get("breakeven_month")
        
        if breakeven_month:
            sensitivity["break_even_analysis"] = {
                "month": breakeven_month,
                "conditions": "Positive cash flow sustained",
                "sensitivity_to_growth": "High - faster growth reduces breakeven time",
                "sensitivity_to_costs": "High - lower costs reduce breakeven time"
            }
        
        # What-if scenarios
        sensitivity["what_if_scenarios"] = [
            {
                "scenario": "10% slower growth",
                "impact": "Breakeven delayed by 2-3 months",
                "risk_level": "low"
            },
            {
                "scenario": "20% higher costs",
                "impact": "Runway reduced by 25%",
                "risk_level": "medium"
            },
            {
                "scenario": "30% lower customer acquisition",
                "impact": "MRR growth reduced by 15%",
                "risk_level": "high"
            }
        ]
        
        return sensitivity
    
    def _generate_scenario_recommendations(self, scenario_type: str,
                                          scenario_results: Dict[str, Any],
                                          impact_analysis: Dict[str, Any]) -> List[str]:
        """Генерация рекомендаций на основе сценария"""
        
        recommendations = []
        
        # Общие рекомендации на основе типа сценария
        if scenario_type == "growth_acceleration":
            recommendations.extend([
                "Инвестировать в sales и marketing для достижения target growth",
                "Убедиться что infrastructure может масштабироваться с ростом",
                "Нанимать team заранее для поддержки роста"
            ])
        elif scenario_type == "cost_reduction":
            recommendations.extend([
                "Приоритизировать cost reductions с highest impact",
                "Избегать сокращений которые могут повредить growth",
                "Коммуницировать changes прозрачно с team"
            ])
        elif scenario_type == "fundraising":
            recommendations.extend([
                "Начать fundraising process за 6 месяцев до need",
                "Подготовить compelling pitch deck и financial model",
                "Build relationships с investors заранее"
            ])
        
        # Рекомендации на основе risk analysis
        risk_analysis = impact_analysis.get("risk_analysis", {})
        
        cash_risk = risk_analysis.get("cash_risk", {}).get("level", "unknown")
        if cash_risk in ["high", "critical"]:
            recommendations.append("Разработать contingency plan для cash shortage")
        
        growth_risk = risk_analysis.get("growth_risk", {}).get("level", "unknown")
        if growth_risk in ["high", "critical"]:
            recommendations.append("Диверсифицировать growth channels для снижения risk")
        
        # Рекомендации на основе financial impact
        financial_impact = impact_analysis.get("financial_impact", {})
        breakeven_month = financial_impact.get("breakeven_month")
        
        if breakeven_month and breakeven_month <= 12:
            recommendations.append(f"Фокусироваться на достижении breakeven к месяцу {breakeven_month}")
        elif breakeven_month and breakeven_month > 24:
            recommendations.append("Рассмотреть способы ускорения пути к profitability")
        
        return recommendations
    
    def _create_scenario_visualizations(self, scenario_results: Dict[str, Any],
                                       comparison: Dict[str, Any],
                                       scenario_name: str) -> Dict[str, Any]:
        """Создание визуализаций для сценария"""
        
        visualizations = {}
        
        monthly_results = scenario_results.get("monthly_results", [])
        
        if not monthly_results:
            return visualizations
        
        # 1. MRR Growth Comparison
        months = [r["month"] for r in monthly_results]
        mrr_values = [r["mrr"] for r in monthly_results]
        
        fig_mrr = go.Figure()
        
        fig_mrr.add_trace(go.Scatter(
            x=months,
            y=mrr_values,
            mode='lines+markers',
            name='Scenario MRR',
            line=dict(color='blue', width=3)
        ))
        
        # Добавляем базовый рост (проекция)
        if len(mrr_values) > 0:
            base_growth_rate = 0.1  # 10% monthly
            base_mrr = [mrr_values[0] * ((1 + base_growth_rate) ** i) for i in range(len(months))]
            
            fig_mrr.add_trace(go.Scatter(
                x=months,
                y=base_mrr,
                mode='lines',
                name='Base Growth (10%/мес)',
                line=dict(color='gray', dash='dash')
            ))
        
        fig_mrr.update_layout(
            title=f'MRR Projection: {scenario_name}',
            xaxis_title='Month',
            yaxis_title='MRR ($)',
            height=400
        )
        
        visualizations['mrr_growth'] = fig_mrr
        
        # 2. Cash Balance
        cash_balances = [r["cash_balance"] for r in monthly_results]
        
        fig_cash = go.Figure()
        
        fig_cash.add_trace(go.Scatter(
            x=months,
            y=cash_balances,
            mode='lines+markers',
            name='Cash Balance',
            line=dict(color='green', width=3),
            fill='tozeroy'
        ))
        
        fig_cash.add_hline(y=0, line_dash="dash", line_color="red",
                          annotation_text="Zero Cash", annotation_position="bottom right")
        
        fig_cash.update_layout(
            title='Cash Balance Projection',
            xaxis_title='Month',
            yaxis_title='Cash Balance ($)',
            height=400
        )
        
        visualizations['cash_balance'] = fig_cash
        
        # 3. Key Metrics Comparison
        metrics_comparison = comparison.get("metrics_comparison", {})
        
        if metrics_comparison:
            metrics = []
            base_values = []
            scenario_values = []
            
            for metric, data in metrics_comparison.items():
                if metric in ["ending_mrr", "ending_cash", "ending_customers"]:
                    metrics.append(metric.replace("ending_", "").title())
                    base_values.append(data.get("base", 0))
                    scenario_values.append(data.get("scenario", 0))
            
            fig_comparison = go.Figure()
            
            fig_comparison.add_trace(go.Bar(
                name='Base',
                x=metrics,
                y=base_values,
                marker_color='gray'
            ))
            
            fig_comparison.add_trace(go.Bar(
                name='Scenario',
                x=metrics,
                y=scenario_values,
                marker_color='blue'
            ))
            
            fig_comparison.update_layout(
                title='Key Metrics Comparison',
                barmode='group',
                height=400
            )
            
            visualizations['metrics_comparison'] = fig_comparison
        
        return visualizations
    
    def _extract_scenario_insights(self, scenario_result: ScenarioResult,
                                  impact_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Извлечение ключевых инсайтов из сценария"""
        
        insights = []
        
        # Insight 1: Наибольший impact
        biggest_change = max(
            scenario_result.parameters,
            key=lambda p: abs(p.change_percent),
            default=None
        )
        
        if biggest_change and abs(biggest_change.change_percent) > 30:
            insights.append({
                "type": "biggest_lever",
                "title": f"Наибольший рычаг: {biggest_change.name}",
                "description": f"Изменение на {biggest_change.change_percent:.1%} имеет наибольший impact",
                "severity": "high",
                "recommendation": f"Фокусироваться на управлении {biggest_change.name}"
            })
        
        # Insight 2: Financial impact
        financial_impact = impact_analysis.get("financial_impact", {})
        runway_impact = financial_impact.get("runway_impact", {})
        
        if runway_impact.get("level") in ["warning", "concerning", "critical", "emergency"]:
            insights.append({
                "type": "runway_warning",
                "title": runway_impact.get("description", "Runway warning"),
                "description": runway_impact.get("implication", ""),
                "severity": runway_impact.get("level", "medium"),
                "recommendation": "Принять меры для увеличения runway"
            })
        
        # Insight 3: Growth potential
        strategic_impact = impact_analysis.get("strategic_impact", {})
        growth_impact = strategic_impact.get("growth_impact", {})
        
        if growth_impact.get("level") in ["hypergrowth", "high_growth"]:
            insights.append({
                "type": "growth_opportunity",
                "title": growth_impact.get("description", "High growth opportunity"),
                "description": growth_impact.get("implication", ""),
                "severity": "positive",
                "recommendation": "Инвестировать в масштабирование для захвата opportunity"
            })
        
        # Insight 4: Risk assessment
        risk_analysis = impact_analysis.get("risk_analysis", {})
        highest_risk = max(
            risk_analysis.values(),
            key=lambda r: {"high": 3, "medium": 2, "low": 1}.get(r.get("level", "low"), 0),
            default={}
        )
        
        if highest_risk.get("level") in ["high", "critical"]:
            insights.append({
                "type": "high_risk",
                "title": f"Высокий риск: {highest_risk.get('description', '')}",
                "description": highest_risk.get("implication", ""),
                "severity": "critical",
                "recommendation": "Разработать mitigation plan для этого риска"
            })
        
        return insights
    
    def _scenario_result_to_dict(self, result: ScenarioResult) -> Dict[str, Any]:
        """Конвертация ScenarioResult в dict"""
        
        return {
            "scenario_id": result.scenario_id,
            "scenario_type": result.scenario_type,
            "name": result.name,
            "description": result.description,
            "parameters": [
                {
                    "name": p.name,
                    "current_value": p.current_value,
                    "scenario_value": p.scenario_value,
                    "change_percent": p.change_percent,
                    "impact_weight": p.impact_weight
                }
                for p in result.parameters
            ],
            "base_outcomes": result.base_outcomes,
            "scenario_outcomes": result.scenario_outcomes,
            "impact_analysis": result.impact_analysis,
            "recommendations": result.recommendations,
            "created_at": result.created_at.isoformat()
        }
    
    def run_multiple_scenarios(self, company_id: int,
                              scenario_types: List[str],
                              duration_months: int = 12) -> Dict[str, Any]:
        """
        Запуск multiple сценариев
        
        Args:
            company_id: ID компании
            scenario_types: Список типов сценариев
            duration_months: Длительность сценариев
        
        Returns:
            Dict с результатами всех сценариев
        """
        
        results = {}
        
        for scenario_type in scenario_types:
            try:
                result = self.run_scenario(
                    company_id, scenario_type, 
                    duration_months=duration_months
                )
                
                if result["success"]:
                    results[scenario_type] = result
                else:
                    results[scenario_type] = {"error": result.get("error", "Unknown error")}
                    
            except Exception as e:
                results[scenario_type] = {"error": str(e)}
        
        # Сравнение сценариев
        comparison = self._compare_scenarios(results)
        
        # Рекомендации по выбору сценария
        scenario_recommendations = self._recommend_best_scenario(results, comparison)
        
        return {
            "success": True,
            "scenarios_run": len([r for r in results.values() if "error" not in r]),
            "results": results,
            "comparison": comparison,
            "scenario_recommendations": scenario_recommendations,
            "summary": self._create_scenarios_summary(results)
        }
    
    def _compare_scenarios(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Сравнение multiple сценариев"""
        
        comparison = {
            "metrics_comparison": {},
            "ranking": [],
            "tradeoffs": []
        }
        
        # Собираем final metrics из всех успешных сценариев
        successful_scenarios = {
            name: data for name, data in results.items() 
            if "error" not in data and data.get("success", False)
        }
        
        if not successful_scenarios:
            return comparison
        
        # Сравнение по ключевым метрикам
        key_metrics = ["ending_mrr", "ending_cash", "ending_runway", "total_profit"]
        
        for metric in key_metrics:
            comparison["metrics_comparison"][metric] = {}
            
            for scenario_name, scenario_data in successful_scenarios.items():
                outcomes = scenario_data.get("scenario", {}).get("scenario_outcomes", {})
                if metric in outcomes:
                    comparison["metrics_comparison"][metric][scenario_name] = outcomes[metric]
        
        # Ранжирование сценариев
        for scenario_name, scenario_data in successful_scenarios.items():
            scenario_info = scenario_data.get("scenario", {})
            outcomes = scenario_info.get("scenario_outcomes", {})
            impact = scenario_data.get("impact_analysis", {})
            
            # Простая scoring system
            score = 0
            
            # Growth score
            if "ending_mrr" in outcomes:
                score += outcomes["ending_mrr"] / 10000  # Каждые $10k MRR = 1 балл
            
            # Profitability score
            if "total_profit" in outcomes and outcomes["total_profit"] > 0:
                score += outcomes["total_profit"] / 10000  # Каждые $10k прибыли = 1 балл
            
            # Runway score
            if "ending_runway" in outcomes:
                score += min(outcomes["ending_runway"], 24)  # До 24 месяцев
            
            # Risk adjustment
            risk_analysis = impact.get("risk_analysis", {})
            cash_risk = risk_analysis.get("cash_risk", {}).get("level", "medium")
            
            risk_multiplier = {"low": 1.0, "medium": 0.9, "high": 0.7, "critical": 0.5}
            score *= risk_multiplier.get(cash_risk, 0.9)
            
            comparison["ranking"].append({
                "scenario": scenario_name,
                "score": score,
                "name": scenario_info.get("name", scenario_name),
                "key_metric": outcomes.get("ending_mrr", 0)
            })
        
        # Сортируем по score
        comparison["ranking"].sort(key=lambda x: x["score"], reverse=True)
        
        # Определяем tradeoffs
        if len(successful_scenarios) >= 2:
            # Сравниваем лучший и второй лучший сценарий
            if len(comparison["ranking"]) >= 2:
                best = comparison["ranking"][0]
                second_best = comparison["ranking"][1]
                
                comparison["tradeoffs"].append({
                    "between": [best["scenario"], second_best["scenario"]],
                    "description": f"{best['scenario']} дает больше роста, но с higher risk",
                    "considerations": [
                        "Risk tolerance компании",
                        "Fundraising timeline",
                        "Market conditions"
                    ]
                })
        
        return comparison
    
    def _recommend_best_scenario(self, results: Dict[str, Any],
                                comparison: Dict[str, Any]) -> Dict[str, Any]:
        """Рекомендация лучшего сценария"""
        
        ranking = comparison.get("ranking", [])
        
        if not ranking:
            return {
                "recommendation": "No successful scenarios to recommend",
                "reason": "All scenarios failed or no data"
            }
        
        best_scenario = ranking[0]
        scenario_name = best_scenario["scenario"]
        
        scenario_data = results.get(scenario_name, {})
        impact_analysis = scenario_data.get("impact_analysis", {})
        risk_analysis = impact_analysis.get("risk_analysis", {})
        
        recommendation = {
            "recommended_scenario": scenario_name,
            "scenario_name": best_scenario["name"],
            "score": best_scenario["score"],
            "key_strengths": [],
            "key_risks": [],
            "implementation_considerations": []
        }
        
        # Key strengths
        if best_scenario["score"] > ranking[1]["score"] * 1.2 if len(ranking) > 1 else 0:
            recommendation["key_strengths"].append("Значительно outperforms другие сценарии")
        
        financial_impact = impact_analysis.get("financial_impact", {})
        if financial_impact.get("breakeven_month", 99) <= 12:
            recommendation["key_strengths"].append("Достигает breakeven в течение года")
        
        # Key risks
        cash_risk = risk_analysis.get("cash_risk", {}).get("level", "medium")
        if cash_risk in ["high", "critical"]:
            recommendation["key_risks"].append("Высокий cash risk")
        
        growth_risk = risk_analysis.get("growth_risk", {}).get("level", "medium")
        if growth_risk in ["high", "critical"]:
            recommendation["key_risks"].append("Высокий growth risk")
        
        # Implementation considerations
        recommendation["implementation_considerations"].extend([
            "Разработать detailed implementation plan",
            "Установить milestones и metrics для отслеживания",
            "Создать contingency plans для key risks"
        ])
        
        return recommendation
    
    def _create_scenarios_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Создание summary multiple сценариев"""
        
        successful_scenarios = {
            name: data for name, data in results.items() 
            if "error" not in data and data.get("success", False)
        }
        
        if not successful_scenarios:
            return {"no_successful_scenarios": True}
        
        summary = {
            "total_scenarios": len(results),
            "successful_scenarios": len(successful_scenarios),
            "failed_scenarios": len(results) - len(successful_scenarios),
            "best_performing_metric": {},
            "worst_performing_metric": {},
            "risk_assessment": {}
        }
        
        # Анализируем performance по метрикам
        metrics_performance = {}
        
        for scenario_name, scenario_data in successful_scenarios.items():
            outcomes = scenario_data.get("scenario", {}).get("scenario_outcomes", {})
            
            for metric, value in outcomes.items():
                if metric not in metrics_performance:
                    metrics_performance[metric] = []
                metrics_performance[metric].append({
                    "scenario": scenario_name,
                    "value": value
                })
        
        # Определяем best и worst performing metrics
        for metric, performances in metrics_performance.items():
            if performances:
                best = max(performances, key=lambda x: x["value"])
                worst = min(performances, key=lambda x: x["value"])
                
                summary["best_performing_metric"][metric] = {
                    "scenario": best["scenario"],
                    "value": best["value"]
                }
                
                summary["worst_performing_metric"][metric] = {
                    "scenario": worst["scenario"],
                    "value": worst["value"]
                }
        
        # Risk assessment
        high_risk_scenarios = []
        for scenario_name, scenario_data in successful_scenarios.items():
            risk_analysis = scenario_data.get("impact_analysis", {}).get("risk_analysis", {})
            
            high_risks = [
                risk for risk in risk_analysis.values() 
                if risk.get("level", "") in ["high", "critical"]
            ]
            
            if high_risks:
                high_risk_scenarios.append({
                    "scenario": scenario_name,
                    "high_risks": len(high_risks),
                    "risk_types": [r.get("description", "") for r in high_risks[:2]]
                })
        
        summary["risk_assessment"] = {
            "high_risk_scenarios": high_risk_scenarios,
            "total_high_risk_scenarios": len(high_risk_scenarios),
            "percentage_high_risk": safe_divide(len(high_risk_scenarios), len(successful_scenarios)) * 100
        }
        
        return summary

# Создаем глобальный экземпляр симулятора
scenario_simulator = ScenarioSimulator()

# Экспортируем полезные функции
def run_what_if_scenario(company_id: int, scenario_type: str, 
                        custom_params: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    """Публичная функция для запуска сценария"""
    return scenario_simulator.run_scenario(company_id, scenario_type, custom_params)

def compare_multiple_scenarios(company_id: int, scenario_types: List[str]) -> Dict[str, Any]:
    """Публичная функция для сравнения multiple сценариев"""
    return scenario_simulator.run_multiple_scenarios(company_id, scenario_types)
