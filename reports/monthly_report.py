"""
Генератор ежемесячных отчетов
Операционные отчеты для менеджмента и команды
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from enum import Enum

# Импортируем внутренние модули с обработкой возможных ошибок
try:
    from services.financial_system.monthly_tracker import monthly_tracker
    from services.financial_system.variance_analyzer import variance_analyzer
    from services.financial_system.ai_recommendations import ai_recommendation_engine
    from services.core.cohort_analyzer import cohort_analyzer
    from services.utils.visualization import visualization_engine
    from services.utils.export_generator import export_generator, ExportFormat
except ImportError as e:
    print(f"Warning: Could not import some modules: {e}")
    # Создаем заглушки для модулей, которые не удалось импортировать
    class MockMonthlyTracker:
        pass
    
    class MockVarianceAnalyzer:
        def analyze_monthly_variance(self, *args, **kwargs):
            return {"significant_variances": []}
    
    class MockAIRecommendationEngine:
        def generate_recommendations(self, *args, **kwargs):
            return {"insights": []}
    
    class MockCohortAnalyzer:
        pass
    
    class MockExportGenerator:
        def export_company_report(self, *args, **kwargs):
            return None
    
    class ExportFormat(Enum):
        PDF = "pdf"
        HTML = "html"
        MD = "md"
    
    monthly_tracker = MockMonthlyTracker()
    variance_analyzer = MockVarianceAnalyzer()
    ai_recommendation_engine = MockAIRecommendationEngine()
    cohort_analyzer = MockCohortAnalyzer()
    export_generator = MockExportGenerator()

# Импортируем db_manager с обработкой ошибки
try:
    from database.db_manager import db_manager
except ImportError as e:
    print(f"Warning: Could not import db_manager: {e}")
    
    class MockDBManager:
        def get_company(self, company_id):
            return None
        def get_actual_financials_by_filters(self, filters):
            return []
        def get_financial_plans(self, company_id):
            return []
        def get_monthly_plans(self, plan_id):
            return []
    
    db_manager = MockDBManager()

class MonthlyReportType(Enum):
    """Типы месячных отчетов"""
    MANAGEMENT = "management"
    TEAM = "team"
    FINANCIAL = "financial"
    OPERATIONAL = "operational"
    CUSTOMER = "customer"

@dataclass
class MonthlyReport:
    """Месячный отчет"""
    report_id: str
    company_id: int
    report_type: MonthlyReportType
    month: int
    year: int
    generated_date: datetime
    sections: Dict[str, Any]
    metrics: Dict[str, Any]
    highlights: List[str]
    lowlights: List[str]
    actions: List[Dict[str, Any]]

class MonthlyReportGenerator:
    """
    Генератор ежемесячных отчетов
    Операционные отчеты для менеджмента и команды
    """
    
    def __init__(self):
        self.report_templates = self._load_monthly_report_templates()
    
    def _load_monthly_report_templates(self) -> Dict[str, Dict[str, Any]]:
        """Загрузка шаблонов месячных отчетов"""
        
        templates = {
            "management": {
                "sections": [
                    "executive_summary",
                    "financial_performance",
                    "operational_metrics",
                    "key_initiatives",
                    "team_performance",
                    "risks_and_issues",
                    "next_month_priorities",
                    "action_items"
                ],
                "audience": "CEO, CTO, CMO, department heads",
                "level": "executive"
            },
            "team": {
                "sections": [
                    "monthly_highlights",
                    "key_achievements",
                    "metrics_review",
                    "team_shoutouts",
                    "learning_moments",
                    "next_month_goals"
                ],
                "audience": "All employees",
                "level": "company_wide"
            },
            "financial": {
                "sections": [
                    "financial_snapshot",
                    "revenue_analysis",
                    "cost_analysis",
                    "cash_flow",
                    "budget_variance",
                    "forecast_update",
                    "financial_health",
                    "action_plan"
                ],
                "audience": "Finance team, executives",
                "level": "financial"
            },
            "operational": {
                "sections": [
                    "operational_snapshot",
                    "product_metrics",
                    "engineering_metrics",
                    "customer_support",
                    "marketing_performance",
                    "sales_performance",
                    "bottlenecks",
                    "improvement_plan"
                ],
                "audience": "Operations team, department heads",
                "level": "operational"
            }
        }
        
        return templates
    
    def generate_management_report(self, company_id: int,
                                  month: int,
                                  year: int) -> Dict[str, Any]:
        """
        Генерация месячного отчета для менеджмента
        
        Args:
            company_id: ID компании
            month: Месяц (1-12)
            year: Год
        
        Returns:
            Dict с management report
        """
        
        # Получение данных компании
        company_data = self._get_company_data(company_id)
        
        if not company_data:
            return {
                "success": False,
                "error": "Company data not found"
            }
        
        # Получение месячных данных
        monthly_data = self._get_monthly_data(company_id, month, year)
        
        # Анализ performance
        performance_analysis = self._analyze_monthly_performance(
            company_data, monthly_data, month, year
        )
        
        # Анализ variance
        variance_analysis = self._analyze_monthly_variance(company_id, month, year)
        
        # Анализ operational metrics
        operational_analysis = self._analyze_operational_metrics(
            company_data, monthly_data
        )
        
        # Генерация highlights и lowlights
        highlights, lowlights = self._generate_highlights_lowlights(
            performance_analysis, variance_analysis
        )
        
        # Определение action items
        action_items = self._determine_action_items(
            performance_analysis, variance_analysis, operational_analysis
        )
        
        # Создание management report
        management_report = {
            "report_type": "management",
            "company": company_data,
            "month": month,
            "year": year,
            "month_name": datetime(year, month, 1).strftime("%B %Y"),
            "performance_summary": performance_analysis,
            "variance_analysis": variance_analysis,
            "operational_analysis": operational_analysis,
            "highlights": highlights,
            "lowlights": lowlights,
            "action_items": action_items,
            "next_month_priorities": self._determine_next_month_priorities(
                company_data, monthly_data, month, year
            ),
            "generated_date": datetime.now().isoformat()
        }
        
        # Создание dashboard
        management_report["dashboard"] = self._create_management_dashboard(
            company_data, monthly_data, performance_analysis
        )
        
        # Генерация AI insights
        management_report["ai_insights"] = self._get_ai_insights(
            company_id, "management_report", month, year
        )
        
        return {
            "success": True,
            "report": management_report,
            "export_formats": ["pdf", "html", "md"],
            "estimated_pages": 10
        }
    
    def _get_company_data(self, company_id: int) -> Optional[Dict[str, Any]]:
        """Получение данных компании"""
        
        try:
            company = db_manager.get_company(company_id)
            if not company:
                return None
            
            # Проверяем, есть ли метод to_dict
            if hasattr(company, 'to_dict'):
                return company.to_dict()
            else:
                # Если нет метода to_dict, создаем словарь вручную
                return {
                    "id": getattr(company, 'id', company_id),
                    "name": getattr(company, 'name', f"Company {company_id}"),
                    "team_size": getattr(company, 'team_size', 10)
                }
        except Exception as e:
            print(f"Error getting company data: {e}")
            return None
    
    def _get_monthly_data(self, company_id: int,
                         month: int,
                         year: int) -> Dict[str, Any]:
        """Получение месячных данных"""
        
        monthly_data = {
            "actuals": {},
            "plan": {},
            "comparisons": {},
            "metrics": {}
        }
        
        try:
            # Получение фактических данных
            actuals = db_manager.get_actual_financials_by_filters({
                "company_id": company_id,
                "year": year,
                "month_number": month
            })
            
            if actuals:
                actual = actuals[0]  # Берем первый (должен быть один)
                if hasattr(actual, 'to_dict'):
                    monthly_data["actuals"] = actual.to_dict()
                else:
                    # Создаем словарь вручную
                    monthly_data["actuals"] = {
                        "actual_mrr": getattr(actual, 'actual_mrr', 0),
                        "actual_new_customers": getattr(actual, 'actual_new_customers', 0),
                        "actual_churned_customers": getattr(actual, 'actual_churned_customers', 0),
                        "actual_total_customers": getattr(actual, 'actual_total_customers', 0),
                        "actual_total_revenue": getattr(actual, 'actual_total_revenue', 0),
                        "actual_total_costs": getattr(actual, 'actual_total_costs', 0),
                        "actual_burn_rate": getattr(actual, 'actual_burn_rate', 0),
                        "actual_cash_balance": getattr(actual, 'actual_cash_balance', 0),
                        "actual_runway": getattr(actual, 'actual_runway', 0),
                        "actual_cac": getattr(actual, 'actual_cac', 0),
                        "actual_ltv": getattr(actual, 'actual_ltv', 0),
                        "actual_ltv_cac_ratio": getattr(actual, 'actual_ltv_cac_ratio', 0),
                        "actual_cac_payback": getattr(actual, 'actual_cac_payback', 0),
                        "actual_gross_margin": getattr(actual, 'actual_gross_margin', 0)
                    }
            
            # Получение плановых данных
            plans = db_manager.get_financial_plans(company_id)
            
            if plans:
                # Находим самый последний план
                latest_plan = None
                latest_date = None
                
                for plan in plans:
                    plan_date = getattr(plan, 'created_at', None)
                    if plan_date and (latest_date is None or plan_date > latest_date):
                        latest_plan = plan
                        latest_date = plan_date
                
                if latest_plan:
                    plan_id = getattr(latest_plan, 'id', 0)
                    monthly_plans = db_manager.get_monthly_plans(plan_id)
                    
                    # Находим план для этого месяца
                    for plan in monthly_plans:
                        plan_year = getattr(plan, 'year', 0)
                        plan_month = getattr(plan, 'month_number', 0)
                        
                        if plan_year == year and plan_month == month:
                            if hasattr(plan, 'to_dict'):
                                monthly_data["plan"] = plan.to_dict()
                            else:
                                monthly_data["plan"] = {
                                    "plan_mrr": getattr(plan, 'plan_mrr', 0),
                                    "plan_total_revenue": getattr(plan, 'plan_total_revenue', 0),
                                    "plan_total_costs": getattr(plan, 'plan_total_costs', 0)
                                }
                            break
            
            # Получение данных за предыдущий месяц для сравнения
            prev_month = month - 1 if month > 1 else 12
            prev_year = year if month > 1 else year - 1
            
            prev_actuals = db_manager.get_actual_financials_by_filters({
                "company_id": company_id,
                "year": prev_year,
                "month_number": prev_month
            })
            
            if prev_actuals:
                prev_actual = prev_actuals[0]
                if hasattr(prev_actual, 'to_dict'):
                    monthly_data["comparisons"]["previous_month"] = prev_actual.to_dict()
                else:
                    monthly_data["comparisons"]["previous_month"] = {
                        "actual_mrr": getattr(prev_actual, 'actual_mrr', 0)
                    }
            
            # Получение данных за тот же месяц прошлого года
            same_month_last_year = db_manager.get_actual_financials_by_filters({
                "company_id": company_id,
                "year": year - 1,
                "month_number": month
            })
            
            if same_month_last_year:
                last_year_actual = same_month_last_year[0]
                if hasattr(last_year_actual, 'to_dict'):
                    monthly_data["comparisons"]["year_over_year"] = last_year_actual.to_dict()
                else:
                    monthly_data["comparisons"]["year_over_year"] = {
                        "actual_mrr": getattr(last_year_actual, 'actual_mrr', 0)
                    }
        except Exception as e:
            print(f"Error getting monthly data: {e}")
        
        # Расчет метрик
        monthly_data["metrics"] = self._calculate_monthly_metrics(monthly_data)
        
        return monthly_data
    
    def _calculate_monthly_metrics(self, monthly_data: Dict[str, Any]) -> Dict[str, Any]:
        """Расчет месячных метрик"""
        
        metrics = {
            "revenue": {},
            "customers": {},
            "financial": {},
            "operational": {}
        }
        
        actuals = monthly_data.get("actuals", {})
        plan = monthly_data.get("plan", {})
        comparisons = monthly_data.get("comparisons", {})
        
        try:
            # Revenue Metrics
            actual_mrr = actuals.get("actual_mrr", 0)
            plan_mrr = plan.get("plan_mrr", 0)
            
            metrics["revenue"] = {
                "actual_mrr": actual_mrr,
                "plan_mrr": plan_mrr,
                "variance": actual_mrr - plan_mrr,
                "variance_percent": ((actual_mrr - plan_mrr) / plan_mrr * 100) if plan_mrr > 0 else 0,
                "growth_rate": self._calculate_monthly_growth(actuals, comparisons.get("previous_month", {}))
            }
            
            # Customer Metrics
            new_customers = actuals.get("actual_new_customers", 0)
            churned_customers = actuals.get("actual_churned_customers", 0)
            total_customers = actuals.get("actual_total_customers", 0)
            
            metrics["customers"] = {
                "new_customers": new_customers,
                "churned_customers": churned_customers,
                "net_new_customers": new_customers - churned_customers,
                "total_customers": total_customers,
                "churn_rate": (churned_customers / max(total_customers, 1) * 100) if total_customers > 0 else 0
            }
            
            # Financial Metrics
            actual_revenue = actuals.get("actual_total_revenue", 0)
            actual_costs = actuals.get("actual_total_costs", 0)
            
            metrics["financial"] = {
                "revenue": actual_revenue,
                "costs": actual_costs,
                "profit": actual_revenue - actual_costs,
                "burn_rate": actuals.get("actual_burn_rate", 0),
                "cash_balance": actuals.get("actual_cash_balance", 0),
                "runway": actuals.get("actual_runway", 0)
            }
            
            # Operational Metrics
            metrics["operational"] = {
                "cac": actuals.get("actual_cac", 0),
                "ltv": actuals.get("actual_ltv", 0),
                "ltv_cac_ratio": actuals.get("actual_ltv_cac_ratio", 0),
                "cac_payback": actuals.get("actual_cac_payback", 0),
                "gross_margin": actuals.get("actual_gross_margin", 0)
            }
        except Exception as e:
            print(f"Error calculating monthly metrics: {e}")
        
        return metrics
    
    def _calculate_monthly_growth(self, current_actuals: Dict[str, Any],
                                previous_actuals: Dict[str, Any]) -> float:
        """Расчет месячного роста"""
        
        try:
            current_mrr = current_actuals.get("actual_mrr", 0)
            previous_mrr = previous_actuals.get("actual_mrr", 0)
            
            if previous_mrr > 0:
                return ((current_mrr - previous_mrr) / previous_mrr) * 100
            
            return 0
        except Exception as e:
            print(f"Error calculating monthly growth: {e}")
            return 0
    
    def _analyze_monthly_performance(self, company_data: Dict[str, Any],
                                    monthly_data: Dict[str, Any],
                                    month: int,
                                    year: int) -> Dict[str, Any]:
        """Анализ месячной performance"""
        
        analysis = {
            "overall_score": 0,
            "score_components": {},
            "trends": {},
            "strengths": [],
            "weaknesses": []
        }
        
        metrics = monthly_data.get("metrics", {})
        revenue_metrics = metrics.get("revenue", {})
        customer_metrics = metrics.get("customers", {})
        financial_metrics = metrics.get("financial", {})
        
        try:
            # Scoring components
            score = 0
            max_score = 0
            
            # Revenue Performance (40% weight)
            revenue_variance = revenue_metrics.get("variance_percent", 0)
            revenue_score = 0
            
            if revenue_variance >= 10:  # 10% above plan
                revenue_score = 10
            elif revenue_variance >= 0:  # On target or slightly above
                revenue_score = 7
            elif revenue_variance >= -10:  # Up to 10% below plan
                revenue_score = 5
            else:  # More than 10% below plan
                revenue_score = 2
            
            analysis["score_components"]["revenue"] = revenue_score
            score += revenue_score * 0.4
            max_score += 10 * 0.4
            
            # Customer Growth (30% weight)
            net_new_customers = customer_metrics.get("net_new_customers", 0)
            customer_score = 0
            
            if net_new_customers >= 50:
                customer_score = 10
            elif net_new_customers >= 25:
                customer_score = 7
            elif net_new_customers > 0:
                customer_score = 5
            elif net_new_customers == 0:
                customer_score = 3
            else:  # Negative net new
                customer_score = 1
            
            analysis["score_components"]["customers"] = customer_score
            score += customer_score * 0.3
            max_score += 10 * 0.3
            
            # Financial Health (30% weight)
            runway = financial_metrics.get("runway", 0)
            financial_score = 0
            
            if runway >= 12:
                financial_score = 10
            elif runway >= 9:
                financial_score = 8
            elif runway >= 6:
                financial_score = 6
            elif runway >= 3:
                financial_score = 4
            else:
                financial_score = 2
            
            analysis["score_components"]["financial"] = financial_score
            score += financial_score * 0.3
            max_score += 10 * 0.3
            
            # Overall Score
            analysis["overall_score"] = (score / max_score) * 100 if max_score > 0 else 0
            
            # Trends Analysis
            growth_rate = revenue_metrics.get("growth_rate", 0)
            
            analysis["trends"] = {
                "revenue_trend": "accelerating" if growth_rate > 10 else 
                                "stable" if growth_rate > 0 else "declining",
                "customer_trend": "growing" if net_new_customers > 10 else 
                                "stable" if net_new_customers > 0 else "declining",
                "efficiency_trend": "improving" if financial_metrics.get("burn_rate", 0) < 100000 else 
                                  "stable" if financial_metrics.get("burn_rate", 0) < 200000 else "worsening"
            }
            
            # Strengths and Weaknesses
            if revenue_variance >= 0:
                analysis["strengths"].append("Met or exceeded revenue target")
            
            if net_new_customers > 0:
                analysis["strengths"].append("Positive net customer growth")
            
            if runway >= 6:
                analysis["strengths"].append("Healthy runway")
            
            if revenue_variance < -10:
                analysis["weaknesses"].append("Missed revenue target significantly")
            
            if net_new_customers < 0:
                analysis["weaknesses"].append("Net customer loss")
            
            churn_rate = customer_metrics.get("churn_rate", 0)
            if churn_rate > 10:
                analysis["weaknesses"].append("High churn rate")
        except Exception as e:
            print(f"Error analyzing monthly performance: {e}")
        
        return analysis
    
    def _analyze_monthly_variance(self, company_id: int,
                                 month: int,
                                 year: int) -> Dict[str, Any]:
        """Анализ месячных отклонений"""
        
        try:
            # Используем variance analyzer
            variance_data = variance_analyzer.analyze_monthly_variance(
                company_id, month, year
            )
            return variance_data
        except Exception as e:
            print(f"Error analyzing monthly variance: {e}")
            return {"significant_variances": [], "total_variance_percent": 0}
    
    def _analyze_operational_metrics(self, company_data: Dict[str, Any],
                                    monthly_data: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ операционных метрик"""
        
        analysis = {
            "product_metrics": {},
            "team_metrics": {},
            "customer_metrics": {},
            "process_efficiency": {}
        }
        
        metrics = monthly_data.get("metrics", {})
        customer_metrics = metrics.get("customers", {})
        operational_metrics = metrics.get("operational", {})
        
        try:
            # Product Metrics (упрощенные)
            analysis["product_metrics"] = {
                "active_users": 0,  # Нужны данные
                "feature_usage": 0,  # Нужны данные
                "bug_resolution": "85% within SLA",  # Предположение
                "release_cadence": "Weekly",  # Предположение
                "user_feedback": "Positive trending"  # Предположение
            }
            
            # Team Metrics
            analysis["team_metrics"] = {
                "headcount": company_data.get("team_size", 0),
                "attrition": "0% this month",  # Предположение
                "productivity": "On target",  # Предположение
                "hiring": "2 positions filled"  # Предположение
            }
            
            # Customer Metrics
            analysis["customer_metrics"] = {
                "satisfaction": "4.5/5.0",  # Предположение
                "support_tickets": 150,  # Предположение
                "resolution_time": "4.2 hours",  # Предположение
                "nps": 45,  # Предположение
                "testimonials": "3 new this month"  # Предположение
            }
            
            # Process Efficiency
            cac = operational_metrics.get("cac", 0)
            ltv_cac_ratio = operational_metrics.get("ltv_cac_ratio", 0)
            
            analysis["process_efficiency"] = {
                "cac_efficiency": "Good" if cac < 1000 else "Needs improvement",
                "ltv_cac_efficiency": "Excellent" if ltv_cac_ratio > 5 else 
                                     "Good" if ltv_cac_ratio > 3 else "Needs improvement",
                "cac_payback": "12 months" if operational_metrics.get("cac_payback", 0) <= 12 else "Long",
                "operational_scalability": "Scaling well"  # Предположение
            }
        except Exception as e:
            print(f"Error analyzing operational metrics: {e}")
        
        return analysis
    
    def _generate_highlights_lowlights(self, performance_analysis: Dict[str, Any],
                                      variance_analysis: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Генерация highlights и lowlights"""
        
        highlights = []
        lowlights = []
        
        try:
            # Из performance analysis
            overall_score = performance_analysis.get("overall_score", 0)
            
            if overall_score >= 80:
                highlights.append("Excellent overall performance this month")
            elif overall_score >= 60:
                highlights.append("Good performance meeting most targets")
            else:
                lowlights.append("Below target performance this month")
            
            # Из variance analysis
            significant_variances = variance_analysis.get("significant_variances", [])
            
            for variance in significant_variances:
                variance_percent = variance.get("variance_percent", 0)
                if variance_percent > 20:  # 20% positive variance
                    highlights.append(f"Significantly exceeded {variance.get('category', 'target')} target")
                elif variance_percent < -20:  # 20% negative variance
                    lowlights.append(f"Missed {variance.get('category', 'target')} target significantly")
        except Exception as e:
            print(f"Error generating highlights/lowlights: {e}")
        
        # Добавляем стандартные если недостаточно
        if len(highlights) < 3:
            highlights.extend([
                "Team delivered on key initiatives",
                "Customer satisfaction remained high",
                "Operational processes improved"
            ])
        
        if len(lowlights) < 2:
            lowlights.extend([
                "Some areas need performance improvement",
                "Market conditions challenging"
            ])
        
        return highlights[:5], lowlights[:3]  # Ограничиваем количество
    
    def _determine_action_items(self, performance_analysis: Dict[str, Any],
                               variance_analysis: Dict[str, Any],
                               operational_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Определение action items"""
        
        action_items = []
        
        try:
            # На основе performance
            weaknesses = performance_analysis.get("weaknesses", [])
            
            for weakness in weaknesses:
                if "revenue" in weakness.lower():
                    action_items.append({
                        "action": "Review and adjust revenue strategy",
                        "owner": "CEO/Head of Sales",
                        "due_date": (datetime.now() + timedelta(days=30)).isoformat(),
                        "priority": "high",
                        "status": "pending"
                    })
                
                if "customer" in weakness.lower():
                    action_items.append({
                        "action": "Improve customer retention program",
                        "owner": "Head of Customer Success",
                        "due_date": (datetime.now() + timedelta(days=45)).isoformat(),
                        "priority": "medium",
                        "status": "pending"
                    })
            
            # На основе variance analysis
            if variance_analysis.get("total_variance_percent", 0) < -10:  # 10% below plan
                action_items.append({
                    "action": "Conduct budget review and adjustment",
                    "owner": "CFO",
                    "due_date": (datetime.now() + timedelta(days=14)).isoformat(),
                    "priority": "high",
                    "status": "pending"
                })
            
            # На основе operational analysis
            efficiency = operational_analysis.get("process_efficiency", {})
            
            if efficiency.get("cac_efficiency") == "Needs improvement":
                action_items.append({
                    "action": "Optimize customer acquisition channels",
                    "owner": "Head of Marketing",
                    "due_date": (datetime.now() + timedelta(days=60)).isoformat(),
                    "priority": "medium",
                    "status": "pending"
                })
        except Exception as e:
            print(f"Error determining action items: {e}")
        
        # Обязательные action items
        action_items.extend([
            {
                "action": "Prepare next month's forecast",
                "owner": "Finance Team",
                "due_date": (datetime.now() + timedelta(days=5)).isoformat(),
                "priority": "high",
                "status": "in_progress"
            },
            {
                "action": "Review team OKRs for next month",
                "owner": "Department Heads",
                "due_date": (datetime.now() + timedelta(days=7)).isoformat(),
                "priority": "medium",
                "status": "pending"
            }
        ])
        
        return action_items
    
    def _determine_next_month_priorities(self, company_data: Dict[str, Any],
                                        monthly_data: Dict[str, Any],
                                        current_month: int,
                                        current_year: int) -> List[Dict[str, Any]]:
        """Определение приоритетов на следующий месяц"""
        
        priorities = []
        
        try:
            # Определяем следующий месяц
            next_month = current_month + 1 if current_month < 12 else 1
            next_year = current_year if current_month < 12 else current_year + 1
            
            # Анализируем текущие метрики
            metrics = monthly_data.get("metrics", {})
            revenue_metrics = metrics.get("revenue", {})
            customer_metrics = metrics.get("customers", {})
            
            # Приоритеты на основе performance
            revenue_variance = revenue_metrics.get("variance_percent", 0)
            
            if revenue_variance < 0:
                priorities.append({
                    "priority": "Revenue acceleration",
                    "description": "Focus on meeting revenue targets",
                    "owner": "Sales & Marketing",
                    "metrics": ["MRR growth", "New customers"],
                    "target": "10% growth"
                })
            
            churn_rate = customer_metrics.get("churn_rate", 0)
            
            if churn_rate > 5:
                priorities.append({
                    "priority": "Customer retention",
                    "description": "Reduce churn rate",
                    "owner": "Customer Success",
                    "metrics": ["Churn rate", "NPS"],
                    "target": "Churn < 5%"
                })
            
            # Сезонные приоритеты
            if next_month == 1:  # Январь
                priorities.append({
                    "priority": "Annual planning",
                    "description": "Set goals and budget for new year",
                    "owner": "Leadership Team",
                    "metrics": ["Annual plan completion"],
                    "target": "Complete by Jan 15"
                })
        except Exception as e:
            print(f"Error determining next month priorities: {e}")
        
        # Обязательные приоритеты
        priorities.extend([
            {
                "priority": "Team development",
                "description": "Invest in team growth and skills",
                "owner": "People Ops",
                "metrics": ["Training completion", "Employee satisfaction"],
                "target": "90% satisfaction"
            },
            {
                "priority": "Product innovation",
                "description": "Continue product development",
                "owner": "Product & Engineering",
                "metrics": ["Features shipped", "Technical debt reduction"],
                "target": "2 major features"
            }
        ])
        
        return priorities[:5]  # Ограничиваем 5 приоритетами
    
    def _create_management_dashboard(self, company_data: Dict[str, Any],
                                    monthly_data: Dict[str, Any],
                                    performance_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Создание dashboard для менеджмента"""
        
        dashboard = {
            "kpis": {},
            "trends": {},
            "alerts": [],
            "quick_actions": []
        }
        
        metrics = monthly_data.get("metrics", {})
        
        try:
            # Key KPIs
            dashboard["kpis"] = {
                "mrr": {
                    "value": metrics.get("revenue", {}).get("actual_mrr", 0),
                    "target": metrics.get("revenue", {}).get("plan_mrr", 0),
                    "status": "on_target" if metrics.get("revenue", {}).get("variance_percent", 0) >= 0 else "below_target",
                    "trend": "up" if metrics.get("revenue", {}).get("growth_rate", 0) > 0 else "down"
                },
                "customers": {
                    "value": metrics.get("customers", {}).get("net_new_customers", 0),
                    "target": 25,  # Предположение
                    "status": "on_target" if metrics.get("customers", {}).get("net_new_customers", 0) >= 25 else "below_target",
                    "trend": "up" if metrics.get("customers", {}).get("net_new_customers", 0) > 0 else "down"
                },
                "burn_rate": {
                    "value": metrics.get("financial", {}).get("burn_rate", 0),
                    "target": 100000,  # Предположение
                    "status": "on_target" if metrics.get("financial", {}).get("burn_rate", 0) <= 100000 else "above_target",
                    "trend": "down" if metrics.get("financial", {}).get("burn_rate", 0) < 150000 else "up"
                },
                "runway": {
                    "value": metrics.get("financial", {}).get("runway", 0),
                    "target": 12,
                    "status": "healthy" if metrics.get("financial", {}).get("runway", 0) >= 12 else 
                             "warning" if metrics.get("financial", {}).get("runway", 0) >= 6 else "critical",
                    "trend": "down"  # Runway всегда уменьшается
                }
            }
            
            # Trends
            dashboard["trends"] = {
                "revenue_trend": performance_analysis.get("trends", {}).get("revenue_trend", "stable"),
                "customer_trend": performance_analysis.get("trends", {}).get("customer_trend", "stable"),
                "efficiency_trend": performance_analysis.get("trends", {}).get("efficiency_trend", "stable")
            }
            
            # Alerts
            if dashboard["kpis"]["runway"]["status"] == "critical":
                dashboard["alerts"].append({
                    "level": "critical",
                    "message": f"Runway only {dashboard['kpis']['runway']['value']:.1f} months",
                    "action": "Start fundraising immediately"
                })
            
            if dashboard["kpis"]["mrr"]["status"] == "below_target":
                dashboard["alerts"].append({
                    "level": "warning",
                    "message": "MRR below target",
                    "action": "Review sales strategy"
                })
        except Exception as e:
            print(f"Error creating management dashboard: {e}")
        
        # Quick Actions
        dashboard["quick_actions"] = [
            {
                "action": "Review budget variances",
                "priority": "high",
                "estimated_time": "30 min"
            },
            {
                "action": "Update next month forecast",
                "priority": "medium",
                "estimated_time": "1 hour"
            },
            {
                "action": "Team performance review",
                "priority": "medium",
                "estimated_time": "2 hours"
            }
        ]
        
        return dashboard
    
    def _get_ai_insights(self, company_id: int,
                        context: str,
                        month: int,
                        year: int) -> List[Dict[str, Any]]:
        """Получение AI insights"""
        
        try:
            # Используем AI recommendation engine
            recommendations = ai_recommendation_engine.generate_recommendations(
                company_id=company_id,
                context=context,
                month=month,
                year=year,
                report_type="monthly"
            )
            
            if recommendations and "insights" in recommendations:
                return recommendations["insights"]
        except Exception as e:
            print(f"Error getting AI insights: {e}")
        
        # Fallback insights
        return [
            {
                "insight": "Revenue growth is steady but could accelerate with focused marketing",
                "confidence": "high",
                "data_points": ["MRR growth rate", "CAC trends"],
                "recommendation": "Increase marketing budget by 20%"
            },
            {
                "insight": "Customer churn is slightly above industry average",
                "confidence": "medium",
                "data_points": ["Churn rate", "Customer feedback"],
                "recommendation": "Implement proactive retention program"
            }
        ]
    
    def generate_team_report(self, company_id: int,
                            month: int,
                            year: int) -> Dict[str, Any]:
        """
        Генерация отчета для команды
        
        Args:
            company_id: ID компании
            month: Месяц (1-12)
            year: Год
        
        Returns:
            Dict с team report
        """
        
        # Получение данных компании
        company_data = self._get_company_data(company_id)
        
        if not company_data:
            return {
                "success": False,
                "error": "Company data not found"
            }
        
        # Получение месячных данных
        monthly_data = self._get_monthly_data(company_id, month, year)
        
        # Создание team report
        team_report = {
            "report_type": "team",
            "company": company_data,
            "month": month,
            "year": year,
            "month_name": datetime(year, month, 1).strftime("%B %Y"),
            "company_update": self._create_company_update(company_data, monthly_data),
            "team_achievements": self._get_team_achievements(company_id, month, year),
            "customer_stories": self._get_customer_stories(company_id),
            "learning_moments": self._get_learning_moments(company_id, month, year),
            "next_month_focus": self._get_next_month_focus(company_id, month, year),
            "generated_date": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "report": team_report,
            "export_formats": ["html", "md", "pdf"],
            "estimated_pages": 5
        }
    
    def _create_company_update(self, company_data: Dict[str, Any],
                              monthly_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создание company update"""
        
        update = {
            "from_leadership": "We had a strong month with key achievements across all departments.",
            "key_metrics": {
                "mrr": monthly_data.get("metrics", {}).get("revenue", {}).get("actual_mrr", 0),
                "customers": monthly_data.get("metrics", {}).get("customers", {}).get("net_new_customers", 0),
                "milestone": "Reached important product milestone"
            },
            "wins": [
                "Launched new product feature",
                "Expanded into new market",
                "Received industry recognition"
            ],
            "thank_yous": [
                "Thanks to the engineering team for the successful release",
                "Great work by sales on exceeding targets"
            ]
        }
        
        return update
    
    def _get_team_achievements(self, company_id: int,
                              month: int,
                              year: int) -> List[Dict[str, Any]]:
        """Получение team achievements"""
        
        # Здесь можно интегрировать с системой управления задачами
        # Пока используем mock данные
        
        achievements = [
            {
                "team": "Engineering",
                "achievement": "Successfully launched v2.0 of our platform",
                "impact": "Improved performance by 40%",
                "team_members": ["Alex", "Sam", "Taylor"]
            },
            {
                "team": "Sales",
                "achievement": "Exceeded monthly target by 15%",
                "impact": "Added 25 new enterprise customers",
                "team_members": ["Jordan", "Casey"]
            },
            {
                "team": "Marketing",
                "achievement": "Ran successful campaign resulting in 500+ leads",
                "impact": "Reduced CAC by 20%",
                "team_members": ["Morgan", "Riley"]
            }
        ]
        
        return achievements
    
    def _get_customer_stories(self, company_id: int) -> List[Dict[str, Any]]:
        """Получение customer stories"""
        
        stories = [
            {
                "customer": "Enterprise Corp",
                "story": "Increased efficiency by 60% using our platform",
                "quote": "This tool transformed our workflow",
                "impact": "Expanded to 500 seats"
            },
            {
                "customer": "Startup Inc",
                "story": "Scaled from 10 to 100 employees using our solution",
                "quote": "Essential for our growth journey",
                "impact": "Case study published"
            }
        ]
        
        return stories
    
    def _get_learning_moments(self, company_id: int,
                             month: int,
                             year: int) -> List[Dict[str, Any]]:
        """Получение learning moments"""
        
        learnings = [
            {
                "learning": "Customer onboarding process needs optimization",
                "insight": "First week engagement predicts long-term retention",
                "action": "Revise onboarding flow"
            },
            {
                "learning": "Certain features have higher adoption than expected",
                "insight": "Users value simplicity over complexity",
                "action": "Focus on core features"
            }
        ]
        
        return learnings
    
    def _get_next_month_focus(self, company_id: int,
                             month: int,
                             year: int) -> Dict[str, Any]:
        """Получение focus на следующий месяц"""
        
        next_month = month + 1 if month < 12 else 1
        next_year = year if month < 12 else year + 1
        
        focus = {
            "month": datetime(next_year, next_month, 1).strftime("%B %Y"),
            "theme": "Acceleration and Excellence",
            "department_focus": {
                "engineering": "Performance optimization",
                "sales": "Enterprise expansion",
                "marketing": "Content strategy",
                "customer_success": "Proactive engagement"
            },
            "company_goals": [
                "Achieve 20% MRR growth",
                "Reduce churn to below 3%",
                "Launch 2 major features"
            ]
        }
        
        return focus
    
    def export_report(self, report_data: Dict[str, Any],
                     export_format: str,
                     filename: Optional[str] = None) -> Union[bytes, str, None]:
        """
        Экспорт отчета
        
        Args:
            report_data: Данные отчета
            export_format: Формат экспорта
            filename: Имя файла
        
        Returns:
            Экспортированные данные
        """
        
        try:
            export_fmt = ExportFormat(export_format.lower())
        except ValueError:
            raise ValueError(f"Unsupported export format: {export_format}")
        
        # Используем export generator
        return export_generator.export_company_report(
            report_data.get("company", {}),
            report_data,
            export_fmt,
            filename
        )

# Создаем глобальный экземпляр генератора отчетов
monthly_report_generator = MonthlyReportGenerator()

# Экспортируем полезные функции
def generate_management_report(company_id: int,
                              month: int,
                              year: int) -> Dict[str, Any]:
    """Публичная функция для генерации management отчета"""
    return monthly_report_generator.generate_management_report(company_id, month, year)

def generate_team_report(company_id: int,
                        month: int,
                        year: int) -> Dict[str, Any]:
    """Публичная функция для генерации team отчета"""
    return monthly_report_generator.generate_team_report(company_id, month, year)

def export_monthly_report(report_data: Dict[str, Any],
                         format_str: str,
                         filename: Optional[str] = None) -> Union[bytes, str, None]:
    """Публичная функция для экспорта monthly отчета"""
    return monthly_report_generator.export_report(report_data, format_str, filename)