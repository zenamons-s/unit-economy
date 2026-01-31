"""
Финансовый планировщик на 12 месяцев для SaaS стартапов
Генерация детальных финансовых планов с AI рекомендациями
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import json
import plotly.graph_objects as go
import plotly.express as px

from database.db_manager import db_manager
from services.core.stage_aware_metrics import stage_metrics
from services.core.cohort_analyzer import cohort_analyzer
from services.core.runway_calculator import runway_calculator

@dataclass
class FinancialPlanInputs:
    """Входные данные для финансового планирования"""
    company_id: int
    plan_name: str
    plan_year: int
    start_month: int = 1
    
    # Текущее состояние
    current_mrr: float = 0
    current_customers: int = 0
    monthly_price: float = 0
    team_size: int = 1
    cash_balance: float = 0
    
    # Допущения
    mrr_growth_rate: float = 0.2
    customer_growth_rate: float = 0.15
    churn_rate: float = 0.05
    expansion_rate: float = 0.1
    
    # CAC assumptions
    cac_target: float = 20000
    cac_payback_target: int = 12
    
    # OPEX assumptions
    salary_per_employee: float = 150000
    office_rent_per_person: float = 10000
    cloud_cost_per_customer: float = 50
    
    # CAPEX assumptions
    capex_budget: float = 0
    capex_items: List[Dict] = field(default_factory=list)
    
    # Seasonality
    seasonality_pattern: Dict[int, float] = field(default_factory=dict)
    
    # AI enhancements
    use_ai_recommendations: bool = True
    optimize_for: str = "runway"  # runway, growth, profitability

class FinancialPlanner:
    """
    Планировщик финансов на 12 месяцев для SaaS
    Генерирует детальные планы с учетом stage-specific метрик
    """
    
    def __init__(self):
        self.month_names = {
            1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель',
            5: 'Май', 6: 'Июнь', 7: 'Июль', 8: 'Август',
            9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'
        }
        
        # Сезонные коэффициенты для B2B SaaS
        self.default_seasonality = {
            1: 0.9,   # Январь - медленно после праздников
            2: 0.95,  # Февраль
            3: 1.1,   # Март - конец квартала
            4: 1.0,   # Апрель
            5: 0.95,  # Май - предотпускной
            6: 0.9,   # Июнь - лето
            7: 0.85,  # Июль - отпуска
            8: 0.9,   # Август
            9: 1.2,   # Сентябрь - начало активности
            10: 1.1,  # Октябрь
            11: 1.0,  # Ноябрь
            12: 1.3   # Декабрь - конец года
        }
        
    def create_12month_plan(self, inputs: FinancialPlanInputs) -> Dict[str, Any]:
        """
        Создание детального финансового плана на 12 месяцев
        
        Args:
            inputs: Входные данные для планирования
        
        Returns:
            Dict с детальным планом
        """
        
        # Валидация входных данных
        self._validate_inputs(inputs)
        
        # Получение эталонных метрик для стадии компании
        company = db_manager.get_company(inputs.company_id)
        stage = company.stage if company else 'pre_seed'
        benchmarks = stage_metrics.get_stage_metrics(stage)
        
        # Генерация базового плана
        base_plan = self._generate_base_plan(inputs, benchmarks)
        
        # Создание записи в базе данных
        plan_id = self._save_financial_plan(inputs, base_plan)
        
        # Генерация месячных планов
        monthly_plans = self._generate_monthly_plans(plan_id, inputs, base_plan)
        
        # AI оптимизация и рекомендации
        if inputs.use_ai_recommendations:
            ai_enhanced_plan = self._apply_ai_optimization(
                monthly_plans, inputs, benchmarks, inputs.optimize_for
            )
            monthly_plans = ai_enhanced_plan.get('optimized_plans', monthly_plans)
            ai_recommendations = ai_enhanced_plan.get('recommendations', [])
        else:
            ai_recommendations = []
        
        # Расчет summary метрик
        summary_metrics = self._calculate_summary_metrics(monthly_plans, inputs.cash_balance)
        
        # Проверка реалистичности плана
        feasibility_check = self._check_plan_feasibility(monthly_plans, inputs, benchmarks)
        
        # Создание визуализаций
        visualizations = self._create_plan_visualizations(monthly_plans, summary_metrics)
        
        return {
            "plan_id": plan_id,
            "plan_name": inputs.plan_name,
            "company_id": inputs.company_id,
            "plan_year": inputs.plan_year,
            "created_at": datetime.now().isoformat(),
            "inputs": self._inputs_to_dict(inputs),
            "monthly_plans": monthly_plans,
            "summary_metrics": summary_metrics,
            "feasibility_check": feasibility_check,
            "ai_recommendations": ai_recommendations,
            "visualizations": visualizations,
            "benchmarks_used": benchmarks.metrics if benchmarks else {},
            "assumptions": self._extract_assumptions(inputs, base_plan)
        }

    def generate_monthly_plans(self, plan_id: int, assumptions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Генерация 12-месячного плана для обратной совместимости с UI.

        Args:
            plan_id: ID финансового плана в базе
            assumptions: словарь с допущениями по росту и затратам

        Returns:
            Список из 12 словарей с месячными планами (без datetime объектов)
        """

        growth = assumptions.get("growth", {})
        costs = assumptions.get("costs", {})

        monthly_growth_rate = float(growth.get("monthly_growth_rate", 0))
        monthly_churn_rate = float(growth.get("monthly_churn_rate", 0))
        starting_mrr = float(growth.get("starting_mrr", 0))
        starting_customers = int(growth.get("starting_customers", 0))
        starting_cash = float(growth.get("starting_cash", 0))

        salary_cost = float(costs.get("salary_cost", 0))
        marketing_cost = float(costs.get("marketing_cost", 0))
        infrastructure_cost = float(costs.get("infrastructure_cost", 0))
        other_cost = float(costs.get("other_cost", 0))
        cac = float(costs.get("cac", 0))

        plan = db_manager.get_financial_plan(plan_id)
        plan_year = plan.plan_year if plan else datetime.now().year

        current_mrr = starting_mrr
        current_customers = starting_customers
        cash_balance = starting_cash

        monthly_plans: List[Dict[str, Any]] = []

        for month in range(1, 13):
            churned_customers = int(current_customers * monthly_churn_rate)
            customers_after_churn = max(0, current_customers - churned_customers)
            target_customers = int(round(customers_after_churn * (1 + monthly_growth_rate)))
            new_customers = max(0, target_customers - customers_after_churn)
            total_customers = customers_after_churn + new_customers

            plan_mrr = max(0.0, current_mrr * (1 + monthly_growth_rate - monthly_churn_rate))
            plan_churned_mrr = current_mrr * monthly_churn_rate

            total_costs = salary_cost + marketing_cost + infrastructure_cost + other_cost
            burn_rate = max(0.0, total_costs - plan_mrr)
            cash_balance += plan_mrr - total_costs

            if burn_rate > 0:
                runway = max(0.0, cash_balance) / burn_rate
            else:
                runway = 999.0

            arpu = plan_mrr / total_customers if total_customers > 0 else 0.0
            ltv = arpu / monthly_churn_rate if monthly_churn_rate > 0 else 0.0
            ltv_cac_ratio = ltv / cac if cac > 0 else 0.0
            cac_payback = cac / arpu if arpu > 0 else 0.0

            month_name = self.month_names.get(month, f"Месяц {month}")
            quarter = ((month - 1) // 3) + 1

            monthly_plans.append({
                "plan_id": plan_id,
                "month_number": month,
                "month_name": month_name,
                "year": plan_year,
                "quarter": quarter,
                "plan_mrr": plan_mrr,
                "plan_new_customers": new_customers,
                "plan_expansion_mrr": 0.0,
                "plan_churn_rate": monthly_churn_rate,
                "plan_churned_mrr": plan_churned_mrr,
                "plan_reactivated_mrr": 0.0,
                "plan_marketing_budget": marketing_cost,
                "plan_sales_budget": marketing_cost * 0.3,
                "plan_cac_target": cac,
                "plan_salaries": salary_cost,
                "plan_office_rent": 0.0,
                "plan_cloud_services": infrastructure_cost,
                "plan_software_subscriptions": other_cost * 0.3,
                "plan_legal_accounting": other_cost * 0.2,
                "plan_marketing_ops": marketing_cost * 0.1,
                "plan_other_opex": other_cost * 0.5,
                "plan_capex_total": 0.0,
                "plan_capex_equipment": 0.0,
                "plan_capex_software": 0.0,
                "plan_capex_furniture": 0.0,
                "plan_capex_other": 0.0,
                "plan_total_revenue": plan_mrr,
                "plan_total_costs": total_costs,
                "plan_burn_rate": burn_rate,
                "plan_gross_margin": 0.8 if plan_mrr > 0 else 0.0,
                "plan_runway": runway,
                "plan_ltv_cac_ratio": ltv_cac_ratio,
                "plan_cac_payback_months": cac_payback,
                "plan_total_customers": total_customers,
                "plan_churned_customers": churned_customers,
                "plan_cash_balance": cash_balance,
                "plan_cac": cac,
                "plan_ltv": ltv,
                "is_locked": False,
                "seasonality_factor": 1.0
            })

            current_mrr = plan_mrr
            current_customers = total_customers

        return monthly_plans
    
    def _validate_inputs(self, inputs: FinancialPlanInputs):
        """Валидация входных данных"""
        
        if inputs.current_mrr < 0:
            raise ValueError("MRR не может быть отрицательным")
        
        if inputs.current_customers < 0:
            raise ValueError("Количество клиентов не может быть отрицательным")
        
        if inputs.monthly_price <= 0:
            raise ValueError("Цена должна быть положительной")
        
        if inputs.team_size <= 0:
            raise ValueError("Размер команды должен быть положительным")
        
        if inputs.cash_balance < 0:
            raise ValueError("Баланс денежных средств не может быть отрицательным")
        
        if inputs.mrr_growth_rate < -1 or inputs.mrr_growth_rate > 5:
            raise ValueError("Рост MRR должен быть между -100% и 500%")
        
        if inputs.churn_rate < 0 or inputs.churn_rate > 1:
            raise ValueError("Churn rate должен быть между 0 и 1")
    
    def _generate_base_plan(self, inputs: FinancialPlanInputs, 
                           benchmarks: Any) -> Dict[str, Any]:
        """Генерация базового плана на основе входных данных"""
        
        base_plan = {
            "revenue_projections": [],
            "customer_projections": [],
            "cac_projections": [],
            "opex_projections": [],
            "capex_projections": [],
            "cashflow_projections": [],
            "key_metrics_projections": []
        }
        
        # Инициализация текущих значений
        current_mrr = inputs.current_mrr
        current_customers = inputs.current_customers
        remaining_cash = inputs.cash_balance
        
        # Прогноз на 12 месяцев
        for month in range(1, 13):
            # Применяем сезонность
            seasonality = inputs.seasonality_pattern.get(month, 1.0)
            if not inputs.seasonality_pattern:
                seasonality = self.default_seasonality.get(month, 1.0)
            
            # Прогноз клиентов
            if month == 1:
                projected_customers = current_customers
            else:
                # Применяем рост с учетом сезонности
                monthly_growth = inputs.customer_growth_rate * seasonality
                new_customers = current_customers * monthly_growth
                churned_customers = current_customers * inputs.churn_rate
                projected_customers = current_customers + new_customers - churned_customers
            
            # Прогноз MRR
            if month == 1:
                projected_mrr = current_mrr
            else:
                # Базовый рост MRR
                mrr_growth = inputs.mrr_growth_rate * seasonality
                
                # Expansion revenue от существующих клиентов
                expansion_revenue = current_mrr * inputs.expansion_rate
                
                # New revenue от новых клиентов
                new_customers_revenue = (projected_customers - current_customers) * inputs.monthly_price
                
                # Churned revenue
                churned_revenue = current_mrr * inputs.churn_rate
                
                projected_mrr = current_mrr * (1 + mrr_growth) + expansion_revenue - churned_revenue
            
            # Прогноз CAC
            # CAC снижается с масштабом
            cac_efficiency = 1 - (0.05 * (month - 1))  # 5% улучшение каждый месяц
            projected_cac = max(inputs.cac_target * 0.5, inputs.cac_target * cac_efficiency)
            
            # Прогноз OPEX
            projected_opex = self._calculate_opex_projection(
                month, inputs, projected_customers, projected_mrr
            )
            
            # Прогноз CAPEX
            projected_capex = self._calculate_capex_projection(month, inputs)
            
            # Расчет cash flow
            net_cashflow = projected_mrr - projected_opex - projected_capex
            remaining_cash += net_cashflow
            
            # Расчет key metrics
            key_metrics = self._calculate_key_metrics(
                projected_mrr, projected_customers, projected_cac, 
                projected_opex, inputs.churn_rate
            )
            
            # Сохраняем projections
            base_plan["revenue_projections"].append({
                "month": month,
                "mrr": projected_mrr,
                "new_customers": max(0, projected_customers - current_customers),
                "churned_customers": current_customers * inputs.churn_rate,
                "expansion_revenue": expansion_revenue if month > 1 else 0
            })
            
            base_plan["customer_projections"].append({
                "month": month,
                "total_customers": projected_customers,
                "new_customers": max(0, projected_customers - current_customers),
                "churned_customers": current_customers * inputs.churn_rate
            })
            
            base_plan["cac_projections"].append({
                "month": month,
                "cac": projected_cac,
                "marketing_budget": projected_cac * max(0, projected_customers - current_customers),
                "sales_budget": projected_cac * max(0, projected_customers - current_customers) * 0.3
            })
            
            base_plan["opex_projections"].append({
                "month": month,
                "total_opex": projected_opex,
                "salaries": inputs.team_size * inputs.salary_per_employee * (1 + 0.02 * month),
                "cloud_costs": projected_customers * inputs.cloud_cost_per_customer,
                "other_opex": projected_opex * 0.2
            })
            
            base_plan["capex_projections"].append({
                "month": month,
                "total_capex": projected_capex,
                "equipment": projected_capex * 0.6,
                "software": projected_capex * 0.3,
                "other_capex": projected_capex * 0.1
            })
            
            base_plan["cashflow_projections"].append({
                "month": month,
                "net_cashflow": net_cashflow,
                "cumulative_cash": remaining_cash,
                "runway": remaining_cash / abs(net_cashflow) if net_cashflow < 0 else float('inf')
            })
            
            base_plan["key_metrics_projections"].append({
                "month": month,
                **key_metrics
            })
            
            # Обновляем текущие значения для следующего месяца
            current_mrr = projected_mrr
            current_customers = projected_customers
        
        return base_plan
    
    def _calculate_opex_projection(self, month: int, inputs: FinancialPlanInputs,
                                  projected_customers: float, projected_mrr: float) -> float:
        """Расчет проекции OPEX"""
        
        # Базовые OPEX
        base_salaries = inputs.team_size * inputs.salary_per_employee
        
        # Рост команды (нанимаем 1 человека каждые 3 месяца после 6 месяцев)
        team_growth = 0
        if month >= 6 and month % 3 == 0:
            team_growth = 1
        
        adjusted_team_size = inputs.team_size + team_growth
        
        # Зарплаты с учетом роста команды и инфляции (2% в месяц)
        salaries = adjusted_team_size * inputs.salary_per_employee * (1 + 0.02 * month)
        
        # Аренда офиса
        office_rent = adjusted_team_size * inputs.office_rent_per_person
        
        # Облачные расходы (растут с количеством клиентов)
        cloud_costs = projected_customers * inputs.cloud_cost_per_customer
        
        # Прочие OPEX (15% от зарплат)
        other_opex = salaries * 0.15
        
        # Маркетинговые и sales расходы (учитываются отдельно в CAC)
        # Здесь только operational marketing
        marketing_ops = projected_mrr * 0.05  # 5% от MRR
        
        total_opex = salaries + office_rent + cloud_costs + other_opex + marketing_ops
        
        return total_opex
    
    def _calculate_capex_projection(self, month: int, inputs: FinancialPlanInputs) -> float:
        """Расчет проекции CAPEX"""
        
        # Базовый CAPEX budget распределяется по месяцам
        if inputs.capex_budget > 0:
            # Распределяем на первые 6 месяцев
            if month <= 6:
                monthly_capex = inputs.capex_budget / 6
            else:
                monthly_capex = inputs.capex_budget * 0.1 / 6  # 10% на остальные 6 месяцев
        else:
            # Автоматический расчет CAPEX на основе роста
            if month % 3 == 0:  # Каждый квартал
                monthly_capex = inputs.team_size * 50000  # 50k на сотрудника
            else:
                monthly_capex = 0
        
        # Учитываем специфические CAPEX items
        for item in inputs.capex_items:
            if item.get('purchase_month') == month:
                monthly_capex += item.get('cost', 0)
        
        return monthly_capex
    
    def _calculate_key_metrics(self, mrr: float, customers: float, cac: float,
                              opex: float, churn_rate: float) -> Dict[str, float]:
        """Расчет ключевых метрик"""
        
        # LTV
        avg_mrr_per_customer = mrr / customers if customers > 0 else 0
        customer_lifetime = 1 / churn_rate if churn_rate > 0 else 12
        ltv = avg_mrr_per_customer * customer_lifetime
        
        # LTV/CAC Ratio
        ltv_cac_ratio = ltv / cac if cac > 0 else 0
        
        # CAC Payback Period
        cac_payback = cac / avg_mrr_per_customer if avg_mrr_per_customer > 0 else 0
        
        # Gross Margin (предполагаем 80% для SaaS)
        gross_margin = 0.8
        gross_profit = mrr * gross_margin
        
        # Net Burn Rate
        net_burn = opex - mrr if opex > mrr else 0
        
        # Runway (рассчитывается отдельно)
        
        return {
            "ltv": ltv,
            "ltv_cac_ratio": ltv_cac_ratio,
            "cac_payback_months": cac_payback,
            "gross_margin": gross_margin,
            "gross_profit": gross_profit,
            "net_burn_rate": net_burn,
            "avg_mrr_per_customer": avg_mrr_per_customer,
            "customer_lifetime_months": customer_lifetime
        }
    
    def _save_financial_plan(self, inputs: FinancialPlanInputs, 
                            base_plan: Dict[str, Any]) -> int:
        """Сохранение финансового плана в базу данных"""
        
        # Создание финансового плана
        from database.db_manager import FinancialPlan
        
        financial_plan = FinancialPlan(
            company_id=inputs.company_id,
            plan_name=inputs.plan_name,
            plan_year=inputs.plan_year,
            description=f"Автоматически сгенерированный план на {inputs.plan_year} год",
            assumptions=json.dumps(self._extract_assumptions(inputs, base_plan)),
            seasonality_pattern=json.dumps(inputs.seasonality_pattern or self.default_seasonality),
            growth_assumptions=json.dumps({
                "mrr_growth_rate": inputs.mrr_growth_rate,
                "customer_growth_rate": inputs.customer_growth_rate,
                "churn_rate": inputs.churn_rate,
                "expansion_rate": inputs.expansion_rate
            })
        )
        
        plan_id = db_manager.create_financial_plan(financial_plan)
        return plan_id
    
    def _generate_monthly_plans(self, plan_id: int, inputs: FinancialPlanInputs,
                               base_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Генерация детальных месячных планов"""
        
        monthly_plans = []
        
        for month in range(1, 13):
            # Получаем проекции для этого месяца
            revenue_proj = base_plan["revenue_projections"][month-1]
            customer_proj = base_plan["customer_projections"][month-1]
            cac_proj = base_plan["cac_projections"][month-1]
            opex_proj = base_plan["opex_projections"][month-1]
            capex_proj = base_plan["capex_projections"][month-1]
            cashflow_proj = base_plan["cashflow_projections"][month-1]
            metrics_proj = base_plan["key_metrics_projections"][month-1]
            
            # Определяем квартал
            quarter = ((month - 1) // 3) + 1
            
            # Создаем детальный месячный план
            monthly_plan = {
                "plan_id": plan_id,
                "month_number": month,
                "month_name": self.month_names.get(month, f"Месяц {month}"),
                "year": inputs.plan_year,
                "quarter": quarter,
                
                # Revenue
                "plan_mrr": revenue_proj["mrr"],
                "plan_new_customers": int(customer_proj["new_customers"]),
                "plan_expansion_mrr": revenue_proj.get("expansion_revenue", 0),
                "plan_churn_rate": inputs.churn_rate,
                "plan_churned_mrr": revenue_proj["mrr"] * inputs.churn_rate,
                "plan_reactivated_mrr": 0,  # Можно добавить логику
                
                # CAC
                "plan_marketing_budget": cac_proj["marketing_budget"],
                "plan_sales_budget": cac_proj["sales_budget"],
                "plan_cac_target": cac_proj["cac"],
                
                # OPEX
                "plan_salaries": opex_proj["salaries"],
                "plan_office_rent": opex_proj.get("office_rent", 0),
                "plan_cloud_services": opex_proj.get("cloud_costs", 0),
                "plan_software_subscriptions": opex_proj.get("other_opex", 0) * 0.3,
                "plan_legal_accounting": opex_proj.get("other_opex", 0) * 0.2,
                "plan_marketing_ops": opex_proj.get("marketing_ops", 0),
                "plan_other_opex": opex_proj.get("other_opex", 0) * 0.5,
                
                # CAPEX
                "plan_capex_total": capex_proj["total_capex"],
                "plan_capex_equipment": capex_proj.get("equipment", 0),
                "plan_capex_software": capex_proj.get("software", 0),
                "plan_capex_furniture": capex_proj.get("other_capex", 0) * 0.5,
                "plan_capex_other": capex_proj.get("other_capex", 0) * 0.5,
                
                # Calculated metrics
                "plan_total_revenue": revenue_proj["mrr"],
                "plan_total_costs": opex_proj["total_opex"] + capex_proj["total_capex"],
                "plan_burn_rate": max(0, opex_proj["total_opex"] + capex_proj["total_capex"] - revenue_proj["mrr"]),
                "plan_gross_margin": metrics_proj["gross_margin"],
                "plan_runway": cashflow_proj["runway"] if cashflow_proj["runway"] != float('inf') else 999,
                "plan_ltv_cac_ratio": metrics_proj["ltv_cac_ratio"],
                "plan_cac_payback_months": metrics_proj["cac_payback_months"],
                
                # Seasonality
                "seasonality_factor": inputs.seasonality_pattern.get(month, 1.0) if inputs.seasonality_pattern 
                                    else self.default_seasonality.get(month, 1.0)
            }
            
            # Сохраняем в базу данных
            from database.db_manager import MonthlyPlan
            monthly_plan_obj = MonthlyPlan(**monthly_plan)
            monthly_plan_id = db_manager.create_monthly_plan(monthly_plan_obj)
            
            monthly_plan["id"] = monthly_plan_id
            monthly_plans.append(monthly_plan)
        
        return monthly_plans
    
    def _apply_ai_optimization(self, monthly_plans: List[Dict[str, Any]],
                              inputs: FinancialPlanInputs, benchmarks: Any,
                              optimize_for: str) -> Dict[str, Any]:
        """Применение AI оптимизации к плану"""
        
        recommendations = []
        optimized_plans = monthly_plans.copy()
        
        # Анализ плана относительно benchmarks
        for month_idx, plan in enumerate(monthly_plans):
            month_recommendations = self._analyze_month_plan(
                plan, inputs, benchmarks, month_idx + 1
            )
            recommendations.extend(month_recommendations)
        
        # Оптимизация в зависимости от цели
        if optimize_for == "runway":
            optimized_plans = self._optimize_for_runway(optimized_plans, inputs)
        elif optimize_for == "growth":
            optimized_plans = self._optimize_for_growth(optimized_plans, inputs)
        elif optimize_for == "profitability":
            optimized_plans = self._optimize_for_profitability(optimized_plans, inputs)
        
        # Применение рекомендаций
        for rec in recommendations:
            if rec.get("apply_automatically", False):
                optimized_plans = self._apply_recommendation(optimized_plans, rec)
        
        return {
            "optimized_plans": optimized_plans,
            "recommendations": recommendations,
            "optimization_applied": optimize_for
        }
    
    def _analyze_month_plan(self, plan: Dict[str, Any], inputs: FinancialPlanInputs,
                           benchmarks: Any, month_number: int) -> List[Dict[str, Any]]:
        """Анализ месячного плана относительно benchmarks"""
        
        recommendations = []
        
        # Анализ CAC Payback
        cac_payback = plan.get("plan_cac_payback_months", 0)
        benchmark_payback = benchmarks.get_metric("cac_payback_months")
        
        if benchmark_payback and cac_payback > benchmark_payback.get("target", 12) * 1.5:
            recommendations.append({
                "month": month_number,
                "type": "cac_optimization",
                "priority": "high",
                "title": "Высокий CAC Payback",
                "description": f"CAC окупается {cac_payback:.1f} месяцев, что выше целевого",
                "suggestion": "Снизить CAC через оптимизацию маркетинговых каналов",
                "action": "reduce_cac",
                "target_reduction": 0.2,  # 20% reduction
                "apply_automatically": True
            })
        
        # Анализ LTV/CAC Ratio
        ltv_cac = plan.get("plan_ltv_cac_ratio", 0)
        benchmark_ltv_cac = benchmarks.get_metric("ltv_cac_ratio")
        
        if benchmark_ltv_cac and ltv_cac < benchmark_ltv_cac.get("target", 3.0) * 0.7:
            recommendations.append({
                "month": month_number,
                "type": "ltv_optimization",
                "priority": "medium",
                "title": "Низкий LTV/CAC Ratio",
                "description": f"LTV/CAC Ratio {ltv_cac:.1f}x ниже целевого",
                "suggestion": "Увеличить LTV через улучшение retention или увеличение цен",
                "action": "increase_ltv",
                "target_increase": 0.15,  # 15% increase
                "apply_automatically": False  # Требует ручного утверждения
            })
        
        # Анализ Runway
        runway = plan.get("plan_runway", 0)
        if runway < 6:
            recommendations.append({
                "month": month_number,
                "type": "runway_warning",
                "priority": "critical",
                "title": "Критически низкий Runway",
                "description": f"Runway всего {runway:.1f} месяцев",
                "suggestion": "Сократить расходы или ускорить revenue growth",
                "action": "reduce_burn_rate",
                "target_reduction": 0.25,  # 25% reduction
                "apply_automatically": True
            })
        
        # Анализ Gross Margin
        gross_margin = plan.get("plan_gross_margin", 0)
        if gross_margin < 0.7:  # Ниже 70%
            recommendations.append({
                "month": month_number,
                "type": "margin_optimization",
                "priority": "medium",
                "title": "Низкая валовая маржа",
                "description": f"Валовая маржа {gross_margin*100:.1f}% ниже стандартов SaaS",
                "suggestion": "Оптимизировать cost of goods sold или увеличить цены",
                "action": "improve_margin",
                "target_improvement": 0.1,  # 10% improvement
                "apply_automatically": False
            })
        
        return recommendations
    
    def _optimize_for_runway(self, monthly_plans: List[Dict[str, Any]],
                            inputs: FinancialPlanInputs) -> List[Dict[str, Any]]:
        """Оптимизация плана для увеличения runway"""
        
        optimized = monthly_plans.copy()
        
        # Стратегии для увеличения runway:
        # 1. Сокращение OPEX
        # 2. Оптимизация CAC
        # 3. Ускорение revenue growth
        
        for i, plan in enumerate(optimized):
            # Сокращаем OPEX на 15%
            opex_fields = [
                'plan_salaries', 'plan_office_rent', 'plan_cloud_services',
                'plan_software_subscriptions', 'plan_legal_accounting',
                'plan_marketing_ops', 'plan_other_opex'
            ]
            
            for field in opex_fields:
                if field in plan and plan[field] > 0:
                    plan[field] *= 0.85  # 15% reduction
            
            # Пересчитываем total costs
            total_opex = sum(plan.get(f, 0) for f in opex_fields)
            total_costs = total_opex + plan.get('plan_capex_total', 0)
            plan['plan_total_costs'] = total_costs
            
            # Пересчитываем burn rate
            revenue = plan.get('plan_total_revenue', 0)
            plan['plan_burn_rate'] = max(0, total_costs - revenue)
            
            # Улучшаем CAC efficiency
            if 'plan_cac_target' in plan:
                plan['plan_cac_target'] *= 0.9  # 10% improvement
                plan['plan_marketing_budget'] *= 0.9
                plan['plan_sales_budget'] *= 0.9
            
            # Пересчитываем LTV/CAC
            if plan.get('plan_new_customers', 0) > 0:
                cac = plan.get('plan_cac_target', 0)
                avg_mrr = revenue / plan.get('plan_new_customers', 1)
                churn_rate = plan.get('plan_churn_rate', 0.05)
                ltv = avg_mrr * (1 / churn_rate) if churn_rate > 0 else avg_mrr * 12
                plan['plan_ltv_cac_ratio'] = ltv / cac if cac > 0 else 0
        
        # Пересчитываем runway
        optimized = self._recalculate_runway(optimized, inputs.cash_balance)
        
        return optimized
    
    def _optimize_for_growth(self, monthly_plans: List[Dict[str, Any]],
                            inputs: FinancialPlanInputs) -> List[Dict[str, Any]]:
        """Оптимизация плана для ускорения роста"""
        
        optimized = monthly_plans.copy()
        
        # Стратегии для ускорения роста:
        # 1. Увеличение marketing budget
        # 2. Ускорение customer acquisition
        # 3. Улучшение expansion revenue
        
        growth_multiplier = 1.3  # 30% ускорение роста
        
        for i, plan in enumerate(optimized):
            if i > 0:  # Начиная со второго месяца
                # Увеличиваем marketing budget
                plan['plan_marketing_budget'] *= growth_multiplier
                plan['plan_sales_budget'] *= growth_multiplier
                
                # Увеличиваем new customers
                current_new = plan.get('plan_new_customers', 0)
                plan['plan_new_customers'] = int(current_new * growth_multiplier)
                
                # Увеличиваем expansion revenue
                current_expansion = plan.get('plan_expansion_mrr', 0)
                plan['plan_expansion_mrr'] = current_expansion * growth_multiplier
                
                # Пересчитываем MRR
                prev_plan = optimized[i-1]
                prev_mrr = prev_plan.get('plan_total_revenue', 0)
                prev_customers = prev_plan.get('plan_new_customers', 0) + \
                               sum(p.get('plan_new_customers', 0) for p in optimized[:i-1])
                
                # Новые клиенты приносят revenue
                new_customer_revenue = plan['plan_new_customers'] * inputs.monthly_price
                
                # Existing customers с churn
                churned_revenue = prev_mrr * plan.get('plan_churn_rate', 0.05)
                
                # Expansion revenue
                expansion_revenue = plan['plan_expansion_mrr']
                
                # Total MRR
                new_mrr = prev_mrr + new_customer_revenue - churned_revenue + expansion_revenue
                plan['plan_total_revenue'] = new_mrr
                plan['plan_mrr'] = new_mrr
        
        # Пересчитываем метрики
        for i, plan in enumerate(optimized):
            # Пересчитываем CAC (может увеличиться из-за более агрессивного роста)
            if plan.get('plan_new_customers', 0) > 0:
                marketing_spend = plan.get('plan_marketing_budget', 0)
                sales_spend = plan.get('plan_sales_budget', 0)
                plan['plan_cac_target'] = (marketing_spend + sales_spend) / plan['plan_new_customers']
            
            # Пересчитываем LTV/CAC
            if plan.get('plan_new_customers', 0) > 0:
                cac = plan.get('plan_cac_target', 0)
                avg_mrr = plan.get('plan_total_revenue', 0) / plan.get('plan_new_customers', 1)
                churn_rate = plan.get('plan_churn_rate', 0.05)
                ltv = avg_mrr * (1 / churn_rate) if churn_rate > 0 else avg_mrr * 12
                plan['plan_ltv_cac_ratio'] = ltv / cac if cac > 0 else 0
        
        return optimized
    
    def _optimize_for_profitability(self, monthly_plans: List[Dict[str, Any]],
                                   inputs: FinancialPlanInputs) -> List[Dict[str, Any]]:
        """Оптимизация плана для увеличения profitability"""
        
        optimized = monthly_plans.copy()
        
        # Стратегии для увеличения profitability:
        # 1. Увеличение цен
        # 2. Улучшение gross margin
        # 3. Оптимизация operational efficiency
        
        price_increase = 1.2  # 20% увеличение цен
        margin_improvement = 1.1  # 10% улучшение margin
        
        for i, plan in enumerate(optimized):
            # Увеличиваем gross margin
            current_margin = plan.get('plan_gross_margin', 0.8)
            plan['plan_gross_margin'] = min(0.9, current_margin * margin_improvement)
            
            # Увеличиваем цены для новых клиентов
            if i >= 3:  # После 3 месяцев можем увеличить цены
                # Новые клиенты платят больше
                new_customer_revenue = plan.get('plan_new_customers', 0) * inputs.monthly_price * price_increase
                
                # Пересчитываем MRR с учетом новых цен
                prev_plan = optimized[i-1]
                prev_mrr = prev_plan.get('plan_total_revenue', 0)
                churned_revenue = prev_mrr * plan.get('plan_churn_rate', 0.05)

                # Для существующих клиентов - постепенное увеличение
                existing_price_increase = 1.05  # 5% увеличение для существующих
                existing_customers_revenue = (prev_mrr - churned_revenue) * existing_price_increase
                
                # Total MRR с увеличенными ценами
                new_mrr = existing_customers_revenue + new_customer_revenue + plan.get('plan_expansion_mrr', 0)
                plan['plan_total_revenue'] = new_mrr
                plan['plan_mrr'] = new_mrr
            
            # Уменьшаем ненужные расходы
            if i > 0:
                # Сокращаем marketing budget если CAC payback слишком долгий
                if plan.get('plan_cac_payback_months', 0) > 15:
                    plan['plan_marketing_budget'] *= 0.7
                    plan['plan_sales_budget'] *= 0.7
                
                # Оптимизируем operational costs
                plan['plan_other_opex'] *= 0.8
                plan['plan_software_subscriptions'] = min(plan.get('plan_software_subscriptions', 0), 5000)
        
        # Пересчитываем метрики profitability
        for plan in optimized:
            # Пересчитываем net profit
            revenue = plan.get('plan_total_revenue', 0)
            total_costs = plan.get('plan_total_costs', 0)
            plan['plan_net_profit'] = revenue - total_costs
            
            # Profit margin
            plan['plan_profit_margin'] = (revenue - total_costs) / revenue if revenue > 0 else 0
            
            # Пересчитываем burn rate (может стать отрицательным - прибыль)
            plan['plan_burn_rate'] = max(0, total_costs - revenue)
        
        return optimized
    
    def _apply_recommendation(self, monthly_plans: List[Dict[str, Any]],
                             recommendation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Применение рекомендации к планам"""
        
        action = recommendation.get('action')
        month = recommendation.get('month')
        target = recommendation.get('target_reduction') or recommendation.get('target_increase') or 0
        
        if not action or not month or month > len(monthly_plans):
            return monthly_plans
        
        plan = monthly_plans[month-1]
        
        if action == "reduce_cac":
            # Уменьшаем CAC
            plan['plan_cac_target'] *= (1 - target)
            plan['plan_marketing_budget'] *= (1 - target)
            plan['plan_sales_budget'] *= (1 - target)
        
        elif action == "increase_ltv":
            # Увеличиваем LTV через снижение churn
            current_churn = plan.get('plan_churn_rate', 0.05)
            plan['plan_churn_rate'] = current_churn * (1 - target/3)  # Частично через churn
            
            # Частично через увеличение expansion
            current_expansion = plan.get('plan_expansion_mrr', 0)
            plan['plan_expansion_mrr'] = current_expansion * (1 + target)
        
        elif action == "reduce_burn_rate":
            # Снижаем burn rate
            opex_fields = ['plan_salaries', 'plan_office_rent', 'plan_cloud_services',
                          'plan_software_subscriptions', 'plan_legal_accounting',
                          'plan_marketing_ops', 'plan_other_opex']
            
            for field in opex_fields:
                if field in plan:
                    plan[field] *= (1 - target)
        
        elif action == "improve_margin":
            # Улучшаем margin
            current_margin = plan.get('plan_gross_margin', 0.8)
            plan['plan_gross_margin'] = min(0.9, current_margin * (1 + target))
        
        return monthly_plans
    
    def _recalculate_runway(self, monthly_plans: List[Dict[str, Any]],
                          initial_cash: float) -> List[Dict[str, Any]]:
        """Пересчет runway для оптимизированных планов"""
        
        cumulative_cash = initial_cash
        
        for i, plan in enumerate(monthly_plans):
            # Расчет net cash flow
            revenue = plan.get('plan_total_revenue', 0)
            total_costs = plan.get('plan_total_costs', 0)
            net_cashflow = revenue - total_costs
            
            # Обновляем cumulative cash
            cumulative_cash += net_cashflow
            
            # Расчет runway
            if net_cashflow < 0:  # Negative cash flow
                runway = cumulative_cash / abs(net_cashflow)
                plan['plan_runway'] = runway
            else:
                plan['plan_runway'] = float('inf') if cumulative_cash > 0 else 0
            
            # Сохраняем cumulative cash
            plan['plan_cumulative_cash'] = cumulative_cash
        
        return monthly_plans
    
    def _calculate_summary_metrics(self, monthly_plans: List[Dict[str, Any]],
                                 initial_cash: float) -> Dict[str, Any]:
        """Расчет summary метрик плана"""
        
        # Собираем данные по месяцам
        months_data = []
        cumulative_cash = initial_cash
        
        for plan in monthly_plans:
            months_data.append({
                'month': plan['month_number'],
                'revenue': plan.get('plan_total_revenue', 0),
                'costs': plan.get('plan_total_costs', 0),
                'net_cashflow': plan.get('plan_total_revenue', 0) - plan.get('plan_total_costs', 0),
                'customers': plan.get('plan_new_customers', 0),
                'runway': plan.get('plan_runway', 0),
                'ltv_cac': plan.get('plan_ltv_cac_ratio', 0),
                'burn_rate': plan.get('plan_burn_rate', 0)
            })
            
            cumulative_cash += months_data[-1]['net_cashflow']
        
        # Расчет summary метрик
        total_revenue = sum(m['revenue'] for m in months_data)
        total_costs = sum(m['costs'] for m in months_data)
        total_customers = sum(m['customers'] for m in months_data)
        
        # Средние метрики
        avg_monthly_growth = self._calculate_cagr(
            months_data[0]['revenue'] if months_data else 0,
            months_data[-1]['revenue'] if months_data else 0,
            len(months_data)
        ) if len(months_data) > 1 else 0
        
        avg_ltv_cac = np.mean([m['ltv_cac'] for m in months_data if m['ltv_cac'] > 0])
        avg_burn_rate = np.mean([m['burn_rate'] for m in months_data])
        
        # Находим минимальный runway
        min_runway = min(m['runway'] for m in months_data if m['runway'] != float('inf'))
        
        # Расчет breakeven month
        breakeven_month = None
        cumulative = initial_cash
        
        for i, m in enumerate(months_data):
            cumulative += m['net_cashflow']
            if cumulative > 0 and breakeven_month is None:
                breakeven_month = i + 1
        
        return {
            "total_12month_revenue": total_revenue,
            "total_12month_costs": total_costs,
            "total_12month_profit": total_revenue - total_costs,
            "total_customers_acquired": total_customers,
            "ending_cash_balance": cumulative_cash,
            "avg_monthly_growth_rate": avg_monthly_growth,
            "avg_ltv_cac_ratio": avg_ltv_cac,
            "avg_burn_rate": avg_burn_rate,
            "min_runway_months": min_runway,
            "breakeven_month": breakeven_month,
            "cash_peak_requirement": abs(min(0, min([m['net_cashflow'] for m in months_data]))) * 3,
            "gross_margin_avg": (total_revenue - total_costs * 0.2) / total_revenue if total_revenue > 0 else 0
        }
    
    def _calculate_cagr(self, start_value: float, end_value: float, 
                       periods: int) -> float:
        """Расчет CAGR"""
        if start_value <= 0:
            return 0
        return (end_value / start_value) ** (1 / periods) - 1
    
    def _check_plan_feasibility(self, monthly_plans: List[Dict[str, Any]],
                               inputs: FinancialPlanInputs,
                               benchmarks: Any) -> Dict[str, Any]:
        """Проверка реалистичности плана"""
        
        issues = []
        warnings = []
        
        # Проверка агрессивности роста
        growth_rates = []
        for i in range(1, len(monthly_plans)):
            current = monthly_plans[i]['plan_total_revenue']
            previous = monthly_plans[i-1]['plan_total_revenue']
            if previous > 0:
                growth_rate = (current - previous) / previous
                growth_rates.append(growth_rate)
        
        avg_growth = np.mean(growth_rates) if growth_rates else 0
        if avg_growth > 0.5:  # 50% monthly growth
            warnings.append({
                "type": "aggressive_growth",
                "severity": "medium",
                "message": f"Средний месячный рост {avg_growth*100:.1f}% может быть слишком агрессивным",
                "suggestion": "Рассмотреть более консервативный сценарий роста"
            })
        
        # Проверка LTV/CAC
        ltv_cac_values = [p['plan_ltv_cac_ratio'] for p in monthly_plans]
        avg_ltv_cac = np.mean(ltv_cac_values)
        
        if avg_ltv_cac < 2.0:
            issues.append({
                "type": "low_ltv_cac",
                "severity": "high",
                "message": f"Средний LTV/CAC {avg_ltv_cac:.1f}x ниже рекомендуемого минимума 3.0x",
                "suggestion": "Улучшить retention или снизить CAC"
            })
        
        # Проверка Runway
        runway_values = [p['plan_runway'] for p in monthly_plans if p['plan_runway'] != float('inf')]
        min_runway = min(runway_values) if runway_values else float('inf')
        
        if min_runway < 6:
            issues.append({
                "type": "low_runway",
                "severity": "critical",
                "message": f"Минимальный runway {min_runway:.1f} месяцев - риск нехватки денег",
                "suggestion": "Сократить расходы или ускорить fundraising"
            })
        
        # Проверка CAC Payback
        cac_payback_values = [p['plan_cac_payback_months'] for p in monthly_plans]
        avg_cac_payback = np.mean(cac_payback_values)
        
        if avg_cac_payback > 18:
            warnings.append({
                "type": "long_cac_payback",
                "severity": "medium",
                "message": f"Средний CAC payback {avg_cac_payback:.1f} месяцев слишком долгий",
                "suggestion": "Оптимизировать маркетинговые каналы"
            })
        
        # Проверка команды
        team_size_needed = inputs.team_size
        for plan in monthly_plans:
            # Эмпирическое правило: 1 инженер на 50к MRR
            mrr = plan['plan_total_revenue']
            engineers_needed = mrr / 50000
            if engineers_needed > team_size_needed:
                warnings.append({
                    "type": "team_scaling",
                    "severity": "low",
                    "message": f"Для MRR ${mrr:,.0f} может потребоваться дополнительная команда",
                    "suggestion": "Планировать hiring заранее"
                })
                break
        
        return {
            "has_issues": len(issues) > 0,
            "has_warnings": len(warnings) > 0,
            "issues": issues,
            "warnings": warnings,
            "feasibility_score": self._calculate_feasibility_score(issues, warnings),
            "recommendations": self._generate_feasibility_recommendations(issues, warnings)
        }
    
    def _calculate_feasibility_score(self, issues: List[Dict], warnings: List[Dict]) -> float:
        """Расчет score реалистичности плана"""
        
        base_score = 100
        
        # Вычитаем за issues
        for issue in issues:
            if issue["severity"] == "critical":
                base_score -= 30
            elif issue["severity"] == "high":
                base_score -= 20
            elif issue["severity"] == "medium":
                base_score -= 10
        
        # Вычитаем за warnings
        for warning in warnings:
            if warning["severity"] == "medium":
                base_score -= 5
            elif warning["severity"] == "low":
                base_score -= 2
        
        return max(0, min(100, base_score))
    
    def _generate_feasibility_recommendations(self, issues: List[Dict], 
                                             warnings: List[Dict]) -> List[str]:
        """Генерация рекомендаций по улучшению реалистичности"""
        
        recommendations = []
        
        # Рекомендации на основе issues
        for issue in issues:
            recommendations.append(f"⚠️ {issue['suggestion']}")
        
        # Рекомендации на основе warnings
        for warning in warnings:
            recommendations.append(f"ℹ️ {warning['suggestion']}")
        
        # Общие рекомендации
        if not issues and not warnings:
            recommendations.append("✅ План выглядит реалистичным. Можно начинать исполнение.")
        elif len(issues) > 0:
            recommendations.append("🔴 Сначала решите критические проблемы, затем пересмотрите план.")
        else:
            recommendations.append("🟡 Рассмотрите предупреждения при исполнении плана.")
        
        return recommendations
    
    def _create_plan_visualizations(self, monthly_plans: List[Dict[str, Any]],
                                   summary_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Создание визуализаций плана"""
        
        visualizations = {}
        
        # Подготовка данных для графиков
        months = [p['month_name'] for p in monthly_plans]
        revenue = [p['plan_total_revenue'] for p in monthly_plans]
        costs = [p['plan_total_costs'] for p in monthly_plans]
        profit = [r - c for r, c in zip(revenue, costs)]
        cumulative_cash = [p.get('plan_cumulative_cash', 0) for p in monthly_plans]
        runway = [p['plan_runway'] if p['plan_runway'] != float('inf') else 24 for p in monthly_plans]
        
        # 1. Revenue vs Costs Chart
        fig_revenue_costs = go.Figure()
        
        fig_revenue_costs.add_trace(go.Bar(
            x=months,
            y=revenue,
            name='Revenue',
            marker_color='green',
            opacity=0.7
        ))
        
        fig_revenue_costs.add_trace(go.Bar(
            x=months,
            y=costs,
            name='Costs',
            marker_color='red',
            opacity=0.7
        ))
        
        fig_revenue_costs.add_trace(go.Scatter(
            x=months,
            y=profit,
            name='Profit',
            mode='lines+markers',
            line=dict(color='blue', width=3),
            yaxis='y2'
        ))
        
        fig_revenue_costs.update_layout(
            title='Revenue vs Costs (12 месяцев)',
            xaxis_title='Месяц',
            yaxis_title='Сумма ($)',
            yaxis2=dict(
                title='Profit ($)',
                overlaying='y',
                side='right'
            ),
            barmode='group',
            height=500
        )
        
        visualizations['revenue_costs_chart'] = fig_revenue_costs
        
        # 2. Cash Flow Chart
        fig_cash_flow = go.Figure()
        
        fig_cash_flow.add_trace(go.Scatter(
            x=months,
            y=cumulative_cash,
            mode='lines+markers',
            name='Cash Balance',
            line=dict(color='navy', width=3),
            fill='tozeroy'
        ))
        
        # Добавляем линии runway
        fig_cash_flow.add_hline(y=0, line_dash="dash", line_color="red",
                               annotation_text="Zero Cash", annotation_position="bottom right")
        
        fig_cash_flow.update_layout(
            title='Cash Balance Projection',
            xaxis_title='Месяц',
            yaxis_title='Cash Balance ($)',
            height=400
        )
        
        visualizations['cash_flow_chart'] = fig_cash_flow
        
        # 3. Runway Chart
        fig_runway = go.Figure()
        
        fig_runway.add_trace(go.Bar(
            x=months,
            y=runway,
            name='Runway (месяцев)',
            marker_color='orange',
            text=[f"{r:.1f}" for r in runway],
            textposition='auto'
        ))
        
        # Добавляем линии threshold
        fig_runway.add_hline(y=12, line_dash="dash", line_color="green",
                           annotation_text="12 мес - Хорошо", annotation_position="top right")
        fig_runway.add_hline(y=6, line_dash="dash", line_color="orange",
                           annotation_text="6 мес - Внимание", annotation_position="top right")
        fig_runway.add_hline(y=3, line_dash="dash", line_color="red",
                           annotation_text="3 мес - Критично", annotation_position="top right")
        
        fig_runway.update_layout(
            title='Runway Projection',
            xaxis_title='Месяц',
            yaxis_title='Месяцев Runway',
            height=400
        )
        
        visualizations['runway_chart'] = fig_runway
        
        # 4. Key Metrics Dashboard
        metrics_data = {
            'Metric': ['Total Revenue', 'Total Costs', 'Profit', 'Avg LTV/CAC', 
                      'Min Runway', 'Breakeven Month', 'Feasibility Score'],
            'Value': [
                f"${summary_metrics['total_12month_revenue']:,.0f}",
                f"${summary_metrics['total_12month_costs']:,.0f}",
                f"${summary_metrics['total_12month_profit']:,.0f}",
                f"{summary_metrics['avg_ltv_cac_ratio']:.1f}x",
                f"{summary_metrics['min_runway_months']:.1f} мес",
                f"Месяц {summary_metrics['breakeven_month'] or 'N/A'}",
                f"{summary_metrics.get('feasibility_score', 0):.0f}/100"
            ]
        }
        
        fig_metrics = go.Figure(data=[go.Table(
            header=dict(values=list(metrics_data.keys()),
                       fill_color='paleturquoise',
                       align='left'),
            cells=dict(values=[metrics_data['Metric'], metrics_data['Value']],
                      fill_color='lavender',
                      align='left'))
        ])
        
        fig_metrics.update_layout(
            title='Key Metrics Summary',
            height=300
        )
        
        visualizations['metrics_table'] = fig_metrics
        
        return visualizations
    
    def _extract_assumptions(self, inputs: FinancialPlanInputs, 
                            base_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Извлечение ключевых допущений плана"""
        
        return {
            "growth_assumptions": {
                "mrr_growth_rate": inputs.mrr_growth_rate,
                "customer_growth_rate": inputs.customer_growth_rate,
                "churn_rate": inputs.churn_rate,
                "expansion_rate": inputs.expansion_rate
            },
            "financial_assumptions": {
                "monthly_price": inputs.monthly_price,
                "cac_target": inputs.cac_target,
                "cac_payback_target": inputs.cac_payback_target,
                "salary_per_employee": inputs.salary_per_employee,
                "cloud_cost_per_customer": inputs.cloud_cost_per_customer
            },
            "team_assumptions": {
                "team_size": inputs.team_size,
                "office_rent_per_person": inputs.office_rent_per_person
            },
            "seasonality": inputs.seasonality_pattern if inputs.seasonality_pattern 
                          else self.default_seasonality,
            "optimization_goal": inputs.optimize_for
        }
    
    def _inputs_to_dict(self, inputs: FinancialPlanInputs) -> Dict[str, Any]:
        """Конвертация входных данных в словарь"""
        return {
            "company_id": inputs.company_id,
            "plan_name": inputs.plan_name,
            "plan_year": inputs.plan_year,
            "start_month": inputs.start_month,
            "current_mrr": inputs.current_mrr,
            "current_customers": inputs.current_customers,
            "monthly_price": inputs.monthly_price,
            "team_size": inputs.team_size,
            "cash_balance": inputs.cash_balance,
            "mrr_growth_rate": inputs.mrr_growth_rate,
            "customer_growth_rate": inputs.customer_growth_rate,
            "churn_rate": inputs.churn_rate,
            "expansion_rate": inputs.expansion_rate,
            "cac_target": inputs.cac_target,
            "cac_payback_target": inputs.cac_payback_target,
            "salary_per_employee": inputs.salary_per_employee,
            "office_rent_per_person": inputs.office_rent_per_person,
            "cloud_cost_per_customer": inputs.cloud_cost_per_customer,
            "capex_budget": inputs.capex_budget,
            "capex_items": inputs.capex_items,
            "use_ai_recommendations": inputs.use_ai_recommendations,
            "optimize_for": inputs.optimize_for
        }

# Создаем глобальный экземпляр планировщика
financial_planner = FinancialPlanner()

# Экспортируем полезные функции
def create_12month_financial_plan(inputs_data: Dict[str, Any]) -> Dict[str, Any]:
    """Публичная функция для создания финансового плана"""
    inputs = FinancialPlanInputs(**inputs_data)
    return financial_planner.create_12month_plan(inputs)

def get_financial_plan_by_id(plan_id: int) -> Dict[str, Any]:
    """Получение плана по ID"""
    plan = db_manager.get_financial_plan(plan_id)
    monthly_plans = db_manager.get_monthly_plans(plan_id)
    
    if not plan:
        return None
    
    return {
        "plan": plan.to_dict(),
        "monthly_plans": [p.to_dict() for p in monthly_plans],
        "summary": financial_planner._calculate_summary_metrics(
            [p.to_dict() for p in monthly_plans],
            plan.cash_balance if hasattr(plan, 'cash_balance') else 0
        )
    }
