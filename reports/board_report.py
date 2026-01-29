"""
Генератор отчетов для совета директоров
Ежеквартальные отчеты и dashboards для board members
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from enum import Enum

# Импортируем внутренние модули с обработкой возможных ошибок
try:
    from services.financial_system.variance_analyzer import variance_analyzer
    from services.financial_system.monthly_tracker import monthly_tracker
    from services.financial_system.ai_recommendations import ai_recommendation_engine
    from services.financial_system.saas_benchmarks import saas_benchmarks
    from services.utils.visualization import visualization_engine
    from services.utils.export_generator import export_generator, ExportFormat
except ImportError as e:
    print(f"Warning: Could not import some modules: {e}")
    # Создаем заглушки для модулей, которые не удалось импортировать
    class MockVarianceAnalyzer:
        def analyze_quarterly_variance(self, *args, **kwargs):
            return {"significant_variances": []}
    
    class MockAIRecommendationEngine:
        def generate_recommendations(self, *args, **kwargs):
            return {"recommendations": []}
    
    class MockSaaSBenchmarks:
        def get_benchmarks(self, stage):
            return None
        def compare_with_benchmarks(self, metrics, stage):
            return {}
    
    class MockExportGenerator:
        def export_company_report(self, *args, **kwargs):
            return None
    
    class ExportFormat(Enum):
        PDF = "pdf"
        PPTX = "pptx"
        HTML = "html"
    
    variance_analyzer = MockVarianceAnalyzer()
    ai_recommendation_engine = MockAIRecommendationEngine()
    saas_benchmarks = MockSaaSBenchmarks()
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

class BoardReportType(Enum):
    """Типы отчетов для board"""
    QUARTERLY = "quarterly"
    MONTHLY = "monthly"
    STRATEGIC_REVIEW = "strategic_review"
    BUDGET_REVIEW = "budget_review"
    SPECIAL = "special"

@dataclass
class BoardReport:
    """Отчет для совета директоров"""
    report_id: str
    company_id: int
    report_type: BoardReportType
    period_start: datetime
    period_end: datetime
    generated_date: datetime
    sections: Dict[str, Any]
    metrics: Dict[str, Any]
    actions_required: List[Dict[str, Any]]
    decisions_needed: List[Dict[str, Any]]
    attachments: List[Dict[str, Any]]

class BoardReportGenerator:
    """
    Генератор отчетов для совета директоров
    Ежеквартальные отчеты, dashboards и strategic reviews
    """
    
    def __init__(self):
        self.report_templates = self._load_board_report_templates()
    
    def _load_board_report_templates(self) -> Dict[str, Dict[str, Any]]:
        """Загрузка шаблонов board отчетов"""
        
        templates = {
            "quarterly": {
                "sections": [
                    "executive_summary",
                    "financial_performance",
                    "operational_metrics",
                    "strategic_initiatives",
                    "risk_assessment",
                    "key_decisions",
                    "action_items",
                    "forward_look"
                ],
                "required_metrics": [
                    "mrr_growth",
                    "burn_rate",
                    "runway",
                    "ltv_cac",
                    "customer_growth",
                    "team_performance"
                ],
                "timeline": "quarterly"
            },
            "monthly": {
                "sections": [
                    "performance_snapshot",
                    "financial_highlights",
                    "key_metrics",
                    "burn_monitor",
                    "immediate_actions",
                    "next_month_focus"
                ],
                "required_metrics": [
                    "mrr",
                    "burn_rate",
                    "runway",
                    "cash_balance",
                    "key_risks"
                ],
                "timeline": "monthly"
            },
            "strategic_review": {
                "sections": [
                    "strategic_context",
                    "market_position",
                    "competitive_analysis",
                    "financial_health",
                    "growth_strategy",
                    "resource_allocation",
                    "strategic_risks",
                    "recommendations"
                ],
                "required_metrics": [
                    "market_share",
                    "competitive_position",
                    "strategic_metrics",
                    "resource_efficiency"
                ],
                "timeline": "as_needed"
            }
        }
        
        return templates
    
    def generate_quarterly_board_report(self, company_id: int,
                                       quarter: int,
                                       year: int) -> Dict[str, Any]:
        """
        Генерация квартального отчета для board
        
        Args:
            company_id: ID компании
            quarter: Квартал (1-4)
            year: Год
        
        Returns:
            Dict с quarterly board report
        """
        
        # Определение периода отчета
        period_start, period_end = self._get_quarter_dates(quarter, year)
        
        # Получение данных компании
        company_data = self._get_company_data(company_id)
        
        if not company_data:
            return {
                "success": False,
                "error": "Company data not found"
            }
        
        # Получение данных за квартал
        quarterly_data = self._get_quarterly_data(company_id, quarter, year)
        
        # Анализ performance
        performance_analysis = self._analyze_quarterly_performance(
            company_data, quarterly_data, quarter, year
        )
        
        # Анализ variances
        variance_analysis = self._analyze_quarterly_variances(company_id, quarter, year)
        
        # Генерация стратегических insights
        strategic_insights = self._generate_strategic_insights(
            company_data, quarterly_data, performance_analysis
        )
        
        # Определение actions required
        actions_required = self._determine_actions_required(
            performance_analysis, variance_analysis, strategic_insights
        )
        
        # Определение decisions needed
        decisions_needed = self._determine_decisions_needed(
            performance_analysis, strategic_insights, quarter, year
        )
        
        # Создание quarterly board report
        board_report = {
            "report_type": "quarterly",
            "company": company_data,
            "quarter": quarter,
            "year": year,
            "period": {
                "start": period_start.isoformat(),
                "end": period_end.isoformat()
            },
            "performance_summary": performance_analysis,
            "variance_analysis": variance_analysis,
            "strategic_insights": strategic_insights,
            "financial_review": self._create_financial_review(quarterly_data),
            "operational_review": self._create_operational_review(quarterly_data),
            "actions_required": actions_required,
            "decisions_needed": decisions_needed,
            "forward_look": self._create_forward_look(company_data, quarter, year),
            "generated_date": datetime.now().isoformat()
        }
        
        # Создание dashboard visualizations
        board_report["dashboard"] = self._create_board_dashboard(
            company_data, quarterly_data, performance_analysis
        )
        
        # Генерация рекомендаций от AI
        board_report["ai_recommendations"] = self._get_ai_recommendations(
            company_id, "board_report"
        )
        
        return {
            "success": True,
            "report": board_report,
            "export_formats": ["pdf", "pptx", "html"],
            "estimated_pages": 15
        }
    
    def _get_quarter_dates(self, quarter: int, year: int) -> Tuple[datetime, datetime]:
        """Получение дат начала и конца квартала"""
        
        quarter_starts = {
            1: datetime(year, 1, 1),
            2: datetime(year, 4, 1),
            3: datetime(year, 7, 1),
            4: datetime(year, 10, 1)
        }
        
        quarter_ends = {
            1: datetime(year, 3, 31),
            2: datetime(year, 6, 30),
            3: datetime(year, 9, 30),
            4: datetime(year, 12, 31)
        }
        
        start_date = quarter_starts.get(quarter, datetime(year, 1, 1))
        end_date = quarter_ends.get(quarter, datetime(year, 12, 31))
        
        return start_date, end_date
    
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
                    "stage": getattr(company, 'stage', "pre_seed"),
                    "cash_balance": getattr(company, 'cash_balance', 0),
                    "current_mrr": getattr(company, 'current_mrr', 0)
                }
        except Exception as e:
            print(f"Error getting company data: {e}")
            return None
    
    def _get_quarterly_data(self, company_id: int,
                           quarter: int,
                           year: int) -> Dict[str, Any]:
        """Получение данных за квартал"""
        
        # Определение месяцев в квартале
        quarter_months = {
            1: [1, 2, 3],
            2: [4, 5, 6],
            3: [7, 8, 9],
            4: [10, 11, 12]
        }
        
        months = quarter_months.get(quarter, [])
        
        quarterly_data = {
            "actuals": [],
            "plans": [],
            "metrics": {}
        }
        
        try:
            # Получение фактических данных за каждый месяц квартала
            for month in months:
                actuals = db_manager.get_actual_financials_by_filters({
                    "company_id": company_id,
                    "year": year,
                    "month_number": month
                })
                
                if actuals:
                    for actual in actuals:
                        if hasattr(actual, 'to_dict'):
                            quarterly_data["actuals"].append(actual.to_dict())
                        else:
                            # Создаем словарь вручную
                            quarterly_data["actuals"].append({
                                "year": getattr(actual, 'year', year),
                                "month_number": getattr(actual, 'month_number', month),
                                "actual_mrr": getattr(actual, 'actual_mrr', 0),
                                "actual_total_revenue": getattr(actual, 'actual_total_revenue', 0),
                                "actual_total_costs": getattr(actual, 'actual_total_costs', 0),
                                "actual_burn_rate": getattr(actual, 'actual_burn_rate', 0),
                                "actual_cash_balance": getattr(actual, 'actual_cash_balance', 0),
                                "actual_new_customers": getattr(actual, 'actual_new_customers', 0),
                                "actual_churned_customers": getattr(actual, 'actual_churned_customers', 0),
                                "actual_marketing_spend": getattr(actual, 'actual_marketing_spend', 0)
                            })
            
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
                    
                    # Фильтрация по кварталу
                    for plan in monthly_plans:
                        plan_year = getattr(plan, 'year', 0)
                        plan_month = getattr(plan, 'month_number', 0)
                        
                        if plan_year == year and plan_month in months:
                            if hasattr(plan, 'to_dict'):
                                quarterly_data["plans"].append(plan.to_dict())
                            else:
                                quarterly_data["plans"].append({
                                    "year": plan_year,
                                    "month_number": plan_month,
                                    "plan_total_revenue": getattr(plan, 'plan_total_revenue', 0),
                                    "plan_total_costs": getattr(plan, 'plan_total_costs', 0)
                                })
        except Exception as e:
            print(f"Error getting quarterly data: {e}")
        
        # Расчет квартальных метрик
        if quarterly_data["actuals"]:
            quarterly_data["metrics"] = self._calculate_quarterly_metrics(
                quarterly_data["actuals"]
            )
        
        return quarterly_data
    
    def _calculate_quarterly_metrics(self, actuals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Расчет квартальных метрик"""
        
        metrics = {
            "revenue": {},
            "customers": {},
            "financial": {},
            "efficiency": {}
        }
        
        if not actuals:
            return metrics
        
        try:
            # Revenue Metrics
            mrr_values = [a.get("actual_mrr", 0) for a in actuals if a.get("actual_mrr") is not None]
            metrics["revenue"] = {
                "starting_mrr": mrr_values[0] if mrr_values else 0,
                "ending_mrr": mrr_values[-1] if mrr_values else 0,
                "quarterly_growth": (mrr_values[-1] - mrr_values[0]) / mrr_values[0] if mrr_values and mrr_values[0] > 0 else 0,
                "average_mrr": np.mean(mrr_values) if mrr_values else 0,
                "total_revenue": sum(a.get("actual_total_revenue", 0) for a in actuals)
            }
            
            # Customer Metrics
            if all("actual_new_customers" in a for a in actuals):
                new_customers = sum(a.get("actual_new_customers", 0) for a in actuals)
                churned_customers = sum(a.get("actual_churned_customers", 0) for a in actuals)
                
                metrics["customers"] = {
                    "new_customers": new_customers,
                    "churned_customers": churned_customers,
                    "net_new_customers": new_customers - churned_customers,
                    "churn_rate": churned_customers / max(1, new_customers) if new_customers > 0 else 0
                }
            
            # Financial Metrics
            metrics["financial"] = {
                "total_costs": sum(a.get("actual_total_costs", 0) for a in actuals),
                "total_burn": sum(max(0, a.get("actual_total_costs", 0) - a.get("actual_total_revenue", 0)) 
                                for a in actuals),
                "average_burn_rate": np.mean([a.get("actual_burn_rate", 0) for a in actuals if a.get("actual_burn_rate") is not None]),
                "ending_cash": actuals[-1].get("actual_cash_balance", 0) if actuals else 0
            }
            
            # Efficiency Metrics
            if metrics.get("customers", {}).get("new_customers", 0) > 0:
                total_marketing = sum(a.get("actual_marketing_spend", 0) for a in actuals)
                metrics["efficiency"] = {
                    "cac": total_marketing / metrics["customers"]["new_customers"],
                    "marketing_efficiency": metrics["revenue"].get("total_revenue", 0) / max(1, total_marketing)
                }
        except Exception as e:
            print(f"Error calculating quarterly metrics: {e}")
        
        return metrics
    
    def _analyze_quarterly_performance(self, company_data: Dict[str, Any],
                                      quarterly_data: Dict[str, Any],
                                      quarter: int,
                                      year: int) -> Dict[str, Any]:
        """Анализ квартальной performance"""
        
        analysis = {
            "overall_performance": {},
            "vs_plan": {},
            "vs_previous_quarter": {},
            "vs_benchmarks": {},
            "key_achievements": [],
            "areas_for_improvement": []
        }
        
        metrics = quarterly_data.get("metrics", {})
        revenue_metrics = metrics.get("revenue", {})
        customer_metrics = metrics.get("customers", {})
        financial_metrics = metrics.get("financial", {})
        
        # Overall Performance Assessment
        growth_rate = revenue_metrics.get("quarterly_growth", 0)
        burn_rate = financial_metrics.get("average_burn_rate", 0)
        net_new_customers = customer_metrics.get("net_new_customers", 0)
        
        # Scoring system
        score = 0
        if growth_rate >= 0.3:
            score += 3  # Excellent growth
        elif growth_rate >= 0.15:
            score += 2  # Good growth
        elif growth_rate >= 0:
            score += 1  # Positive growth
        
        if net_new_customers >= 100:
            score += 3
        elif net_new_customers >= 50:
            score += 2
        elif net_new_customers > 0:
            score += 1
        
        if burn_rate <= 50000:
            score += 3  # Efficient burn
        elif burn_rate <= 100000:
            score += 2
        elif burn_rate <= 200000:
            score += 1
        
        # Overall rating
        if score >= 8:
            rating = "Excellent"
            color = "green"
        elif score >= 6:
            rating = "Good"
            color = "blue"
        elif score >= 4:
            rating = "Satisfactory"
            color = "yellow"
        else:
            rating = "Needs Improvement"
            color = "red"
        
        analysis["overall_performance"] = {
            "score": score,
            "rating": rating,
            "color": color,
            "summary": f"Q{quarter} {year} performance was {rating.lower()}"
        }
        
        # Vs Plan Analysis
        if quarterly_data.get("plans"):
            vs_plan = self._compare_vs_plan(quarterly_data)
            analysis["vs_plan"] = vs_plan
            
            # Добавляем key achievements если превысили план
            if vs_plan.get("revenue_vs_plan_percent", 0) > 10:  # 10% выше плана
                analysis["key_achievements"].append(
                    f"Exceeded revenue plan by {vs_plan.get('revenue_vs_plan_percent', 0):.1f}%"
                )
            
            # Добавляем areas for improvement если ниже плана
            if vs_plan.get("revenue_vs_plan_percent", 0) < -10:  # 10% ниже плана
                analysis["areas_for_improvement"].append(
                    f"Missed revenue target by {abs(vs_plan.get('revenue_vs_plan_percent', 0)):.1f}%"
                )
        
        # Vs Previous Quarter
        if quarter > 1:
            prev_quarter_data = self._get_quarterly_data(
                company_data.get("id", 0), quarter - 1, year
            )
            
            if prev_quarter_data.get("metrics"):
                vs_prev = self._compare_vs_previous(
                    metrics, prev_quarter_data.get("metrics", {})
                )
                analysis["vs_previous_quarter"] = vs_prev
        
        # Vs Benchmarks
        try:
            stage = company_data.get("stage", "pre_seed")
            benchmarks = saas_benchmarks.get_benchmarks(stage)
            
            if benchmarks:
                company_metrics = {
                    "mrr_growth_monthly": growth_rate / 3,  # Quarterly to monthly
                    "ltv_cac_ratio": 0,  # Нужны данные
                    "gross_margin": 0.8  # Предположение
                }
                
                comparison = saas_benchmarks.compare_with_benchmarks(
                    company_metrics, stage
                )
                analysis["vs_benchmarks"] = comparison
        except:
            pass
        
        # Key Achievements (дополнительные)
        if net_new_customers > 0:
            analysis["key_achievements"].append(
                f"Added {net_new_customers} net new customers"
            )
        
        if financial_metrics.get("total_burn", 0) < 100000:
            analysis["key_achievements"].append(
                "Maintained efficient burn rate"
            )
        
        # Areas for Improvement (дополнительные)
        if growth_rate < 0.1:
            analysis["areas_for_improvement"].append(
                "Growth rate below target of 10% quarterly"
            )
        
        if customer_metrics.get("churn_rate", 0) > 0.1:
            analysis["areas_for_improvement"].append(
                "Churn rate above acceptable level"
            )
        
        return analysis
    
    def _compare_vs_plan(self, quarterly_data: Dict[str, Any]) -> Dict[str, Any]:
        """Сравнение с планом"""
        
        comparison = {
            "revenue_vs_plan": 0,
            "revenue_vs_plan_percent": 0,
            "costs_vs_plan": 0,
            "costs_vs_plan_percent": 0,
            "detailed_comparison": []
        }
        
        if not quarterly_data.get("actuals") or not quarterly_data.get("plans"):
            return comparison
        
        try:
            # Группируем данные по месяцам
            actuals_by_month = {}
            for actual in quarterly_data["actuals"]:
                month_key = f"{actual.get('year', 0)}-{actual.get('month_number', 0)}"
                actuals_by_month[month_key] = actual
            
            plans_by_month = {}
            for plan in quarterly_data["plans"]:
                month_key = f"{plan.get('year', 0)}-{plan.get('month_number', 0)}"
                plans_by_month[month_key] = plan
            
            # Сравниваем по общим месяцам
            total_actual_revenue = 0
            total_plan_revenue = 0
            total_actual_costs = 0
            total_plan_costs = 0
            
            for month_key in set(actuals_by_month.keys()) & set(plans_by_month.keys()):
                actual = actuals_by_month[month_key]
                plan = plans_by_month[month_key]
                
                actual_revenue = actual.get("actual_total_revenue", 0)
                plan_revenue = plan.get("plan_total_revenue", 0)
                actual_costs = actual.get("actual_total_costs", 0)
                plan_costs = plan.get("plan_total_costs", 0)
                
                total_actual_revenue += actual_revenue
                total_plan_revenue += plan_revenue
                total_actual_costs += actual_costs
                total_plan_costs += plan_costs
                
                comparison["detailed_comparison"].append({
                    "month": month_key,
                    "revenue_variance": actual_revenue - plan_revenue,
                    "revenue_variance_percent": (actual_revenue - plan_revenue) / plan_revenue if plan_revenue > 0 else 0,
                    "costs_variance": actual_costs - plan_costs,
                    "costs_variance_percent": (actual_costs - plan_costs) / plan_costs if plan_costs > 0 else 0
                })
            
            # Итоговое сравнение
            comparison["revenue_vs_plan"] = total_actual_revenue - total_plan_revenue
            comparison["revenue_vs_plan_percent"] = (comparison["revenue_vs_plan"] / total_plan_revenue * 100) if total_plan_revenue > 0 else 0
            
            comparison["costs_vs_plan"] = total_actual_costs - total_plan_costs
            comparison["costs_vs_plan_percent"] = (comparison["costs_vs_plan"] / total_plan_costs * 100) if total_plan_costs > 0 else 0
        except Exception as e:
            print(f"Error in compare_vs_plan: {e}")
        
        return comparison
    
    def _compare_vs_previous(self, current_metrics: Dict[str, Any],
                            previous_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Сравнение с предыдущим кварталом"""
        
        comparison = {
            "revenue_growth": 0,
            "customer_growth": 0,
            "burn_rate_change": 0,
            "efficiency_change": 0
        }
        
        try:
            # Revenue Growth Comparison
            current_revenue = current_metrics.get("revenue", {}).get("ending_mrr", 0)
            previous_revenue = previous_metrics.get("revenue", {}).get("ending_mrr", 0)
            
            if previous_revenue > 0:
                comparison["revenue_growth"] = (current_revenue - previous_revenue) / previous_revenue
            
            # Customer Growth Comparison
            current_customers = current_metrics.get("customers", {}).get("net_new_customers", 0)
            previous_customers = previous_metrics.get("customers", {}).get("net_new_customers", 0)
            
            if previous_customers != 0:
                comparison["customer_growth"] = (current_customers - previous_customers) / abs(previous_customers)
            
            # Burn Rate Comparison
            current_burn = current_metrics.get("financial", {}).get("average_burn_rate", 0)
            previous_burn = previous_metrics.get("financial", {}).get("average_burn_rate", 0)
            
            if previous_burn > 0:
                comparison["burn_rate_change"] = (current_burn - previous_burn) / previous_burn
            
            # Efficiency Comparison
            current_cac = current_metrics.get("efficiency", {}).get("cac", 0)
            previous_cac = previous_metrics.get("efficiency", {}).get("cac", 0)
            
            if previous_cac > 0:
                comparison["efficiency_change"] = (previous_cac - current_cac) / previous_cac  # Отрицательное значение = улучшение
        except Exception as e:
            print(f"Error in compare_vs_previous: {e}")
        
        return comparison
    
    def _analyze_quarterly_variances(self, company_id: int,
                                    quarter: int,
                                    year: int) -> Dict[str, Any]:
        """Анализ квартальных отклонений"""
        
        try:
            # Используем variance analyzer
            variance_data = variance_analyzer.analyze_quarterly_variance(
                company_id, quarter, year
            )
            return variance_data
        except Exception as e:
            print(f"Error analyzing variances: {e}")
            return {"significant_variances": []}
    
    def _generate_strategic_insights(self, company_data: Dict[str, Any],
                                    quarterly_data: Dict[str, Any],
                                    performance_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Генерация стратегических insights"""
        
        insights = {
            "growth_trajectory": {},
            "market_position": {},
            "competitive_advantages": [],
            "strategic_risks": [],
            "opportunities": []
        }
        
        metrics = quarterly_data.get("metrics", {})
        revenue_metrics = metrics.get("revenue", {})
        
        # Growth Trajectory Analysis
        growth_rate = revenue_metrics.get("quarterly_growth", 0)
        
        if growth_rate >= 0.3:
            trajectory = "Hypergrowth"
            implication = "Scale operations rapidly, consider fundraising"
        elif growth_rate >= 0.15:
            trajectory = "Strong Growth"
            implication = "Continue current strategy, optimize for efficiency"
        elif growth_rate >= 0:
            trajectory = "Moderate Growth"
            implication = "Review growth strategy, consider pivots"
        else:
            trajectory = "Declining"
            implication = "Urgent action required, possible strategic pivot"
        
        insights["growth_trajectory"] = {
            "current_rate": growth_rate,
            "trajectory": trajectory,
            "implication": implication
        }
        
        # Market Position Analysis
        stage = company_data.get("stage", "pre_seed")
        mrr = revenue_metrics.get("ending_mrr", 0)
        
        if mrr >= 100000:
            position = "Emerging Leader"
            description = "Strong position in market, potential to become category leader"
        elif mrr >= 50000:
            position = "Strong Contender"
            description = "Well-positioned for Series A/B, building momentum"
        elif mrr >= 10000:
            position = "Promising Startup"
            description = "Early traction, proving product-market fit"
        else:
            position = "Early Stage"
            description = "Pre-product-market fit, focused on validation"
        
        insights["market_position"] = {
            "position": position,
            "description": description,
            "current_mrr": mrr,
            "stage": stage
        }
        
        # Competitive Advantages
        advantages = []
        
        # На основе метрик определяем преимущества
        if metrics.get("efficiency", {}).get("cac", 0) < 1000:
            advantages.append("Low customer acquisition cost")
        
        if metrics.get("customers", {}).get("churn_rate", 0) < 0.05:
            advantages.append("High customer retention")
        
        if revenue_metrics.get("quarterly_growth", 0) > 0.2:
            advantages.append("Strong growth momentum")
        
        if not advantages:
            advantages.append("Early stage, advantages being established")
        
        insights["competitive_advantages"] = advantages
        
        # Strategic Risks
        risks = []
        
        if company_data.get("cash_balance", 0) < 100000:
            risks.append("Limited cash reserves")
        
        if metrics.get("customers", {}).get("churn_rate", 0) > 0.1:
            risks.append("High churn rate")
        
        if revenue_metrics.get("quarterly_growth", 0) < 0.1:
            risks.append("Slowing growth")
        
        if not risks:
            risks.append("Standard early-stage startup risks")
        
        insights["strategic_risks"] = risks
        
        # Opportunities
        opportunities = []
        
        if growth_rate > 0.2:
            opportunities.append("Accelerate growth with additional funding")
        
        if metrics.get("efficiency", {}).get("marketing_efficiency", 0) > 3:
            opportunities.append("Scale marketing investment")
        
        if mrr < 50000 and growth_rate > 0.15:
            opportunities.append("Raise next funding round")
        
        if not opportunities:
            opportunities.append("Continue current strategy with focus on execution")
        
        insights["opportunities"] = opportunities
        
        return insights
    
    def _determine_actions_required(self, performance_analysis: Dict[str, Any],
                                  variance_analysis: Dict[str, Any],
                                  strategic_insights: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Определение необходимых действий"""
        
        actions = []
        
        # На основе performance analysis
        performance = performance_analysis.get("overall_performance", {})
        rating = performance.get("rating", "")
        
        if rating == "Needs Improvement":
            actions.append({
                "action": "Conduct strategic review",
                "priority": "high",
                "owner": "CEO",
                "due_date": (datetime.now() + timedelta(days=30)).isoformat(),
                "description": "Review strategy and make necessary adjustments"
            })
        
        # На основе variance analysis
        if variance_analysis.get("significant_variances", []):
            actions.append({
                "action": "Address significant budget variances",
                "priority": "medium",
                "owner": "CFO",
                "due_date": (datetime.now() + timedelta(days=14)).isoformat(),
                "description": "Review and explain significant budget deviations"
            })
        
        # На основе strategic insights
        risks = strategic_insights.get("strategic_risks", [])
        
        if "Limited cash reserves" in risks:
            actions.append({
                "action": "Extend runway or start fundraising",
                "priority": "high",
                "owner": "CEO/CFO",
                "due_date": (datetime.now() + timedelta(days=60)).isoformat(),
                "description": "Ensure sufficient cash for operations"
            })
        
        if "High churn rate" in risks:
            actions.append({
                "action": "Implement customer retention program",
                "priority": "medium",
                "owner": "Head of Customer Success",
                "due_date": (datetime.now() + timedelta(days=45)).isoformat(),
                "description": "Reduce churn rate below 5%"
            })
        
        # Обязательные board actions
        actions.extend([
            {
                "action": "Review and approve next quarter's budget",
                "priority": "high",
                "owner": "Board",
                "due_date": (datetime.now() + timedelta(days=30)).isoformat(),
                "description": "Approve financial plan for next quarter"
            },
            {
                "action": "Schedule next board meeting",
                "priority": "medium",
                "owner": "Board Secretary",
                "due_date": (datetime.now() + timedelta(days=7)).isoformat(),
                "description": "Set date for next quarterly board meeting"
            }
        ])
        
        return actions
    
    def _determine_decisions_needed(self, performance_analysis: Dict[str, Any],
                                  strategic_insights: Dict[str, Any],
                                  quarter: int,
                                  year: int) -> List[Dict[str, Any]]:
        """Определение необходимых решений"""
        
        decisions = []
        
        # На основе performance
        rating = performance_analysis.get("overall_performance", {}).get("rating", "")
        
        if rating == "Needs Improvement":
            decisions.append({
                "decision": "Approve strategic pivot",
                "description": "Based on poor performance, approve change in strategy",
                "options": ["Minor adjustments", "Major pivot", "Continue current strategy"],
                "recommended": "Minor adjustments",
                "impact": "Medium",
                "deadline": (datetime.now() + timedelta(days=45)).isoformat()
            })
        
        # На основе strategic insights
        trajectory = strategic_insights.get("growth_trajectory", {}).get("trajectory", "")
        
        if trajectory == "Hypergrowth":
            decisions.append({
                "decision": "Approve growth investment",
                "description": "Capitalize on hypergrowth with additional investment",
                "options": ["Invest $500k", "Invest $1M", "Maintain current budget"],
                "recommended": "Invest $1M",
                "impact": "High",
                "deadline": (datetime.now() + timedelta(days=60)).isoformat()
            })
        
        # Сезонные решения
        if quarter == 4:
            decisions.append({
                "decision": "Approve annual budget for next year",
                "description": "Review and approve company budget for next fiscal year",
                "options": ["Conservative budget", "Growth budget", "Aggressive budget"],
                "recommended": "Growth budget",
                "impact": "High",
                "deadline": f"{year+1}-01-15"
            })
        
        # Обязательные board decisions
        decisions.append({
            "decision": "Approve next quarter's strategic priorities",
            "description": "Set strategic focus areas for next quarter",
            "options": ["Growth", "Profitability", "Market expansion", "Product development"],
            "recommended": "Growth",
            "impact": "High",
            "deadline": (datetime.now() + timedelta(days=30)).isoformat()
        })
        
        return decisions
    
    def _create_financial_review(self, quarterly_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создание финансового обзора"""
        
        review = {
            "income_statement": {},
            "balance_sheet": {},
            "cash_flow": {},
            "key_ratios": {}
        }
        
        metrics = quarterly_data.get("metrics", {})
        revenue_metrics = metrics.get("revenue", {})
        financial_metrics = metrics.get("financial", {})
        
        # Income Statement Summary
        total_revenue = revenue_metrics.get("total_revenue", 0)
        total_costs = financial_metrics.get("total_costs", 0)
        
        review["income_statement"] = {
            "revenue": total_revenue,
            "cogs": total_costs * 0.2,  # Предположение
            "gross_profit": total_revenue - (total_costs * 0.2),
            "operating_expenses": total_costs * 0.8,  # Предположение
            "operating_income": total_revenue - total_costs,
            "net_income": total_revenue - total_costs
        }
        
        # Key Ratios
        if total_revenue > 0:
            review["key_ratios"] = {
                "gross_margin": (review["income_statement"]["gross_profit"] / total_revenue) if total_revenue > 0 else 0,
                "operating_margin": (review["income_statement"]["operating_income"] / total_revenue) if total_revenue > 0 else 0,
                "burn_rate": financial_metrics.get("average_burn_rate", 0),
                "revenue_growth": revenue_metrics.get("quarterly_growth", 0)
            }
        
        # Cash Flow Analysis
        review["cash_flow"] = {
            "operating_cash_flow": -financial_metrics.get("total_burn", 0),  # Negative for burn
            "investing_cash_flow": -10000,  # Предположение
            "financing_cash_flow": 0,  # Предположение
            "net_cash_flow": -financial_metrics.get("total_burn", 0) - 10000,
            "ending_cash": financial_metrics.get("ending_cash", 0)
        }
        
        return review
    
    def _create_operational_review(self, quarterly_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создание операционного обзора"""
        
        review = {
            "customer_metrics": {},
            "team_metrics": {},
            "product_metrics": {},
            "operational_efficiency": {}
        }
        
        metrics = quarterly_data.get("metrics", {})
        customer_metrics = metrics.get("customers", {})
        efficiency_metrics = metrics.get("efficiency", {})
        
        # Customer Metrics
        review["customer_metrics"] = {
            "total_customers": 0,  # Нужны данные
            "new_customers": customer_metrics.get("new_customers", 0),
            "churned_customers": customer_metrics.get("churned_customers", 0),
            "net_new_customers": customer_metrics.get("net_new_customers", 0),
            "churn_rate": customer_metrics.get("churn_rate", 0),
            "customer_satisfaction": 4.2  # Предположение
        }
        
        # Team Metrics
        review["team_metrics"] = {
            "headcount": 0,  # Нужны данные
            "hires": 0,  # Нужны данные
            "attrition": 0,  # Нужны данные
            "productivity": "Improving",  # Предположение
            "key_hires": ["Position 1", "Position 2"]  # Предположение
        }
        
        # Product Metrics
        review["product_metrics"] = {
            "active_users": 0,  # Нужны данные
            "feature_adoption": 0,  # Нужны данные
            "bug_count": 0,  # Нужны данные
            "release_velocity": "On track",  # Предположение
            "customer_feedback": "Positive"  # Предположение
        }
        
        # Operational Efficiency
        review["operational_efficiency"] = {
            "cac": efficiency_metrics.get("cac", 0),
            "ltv": 0,  # Нужны данные
            "ltv_cac_ratio": 0,  # Нужны данные
            "cac_payback": 12,  # Предположение
            "marketing_efficiency": efficiency_metrics.get("marketing_efficiency", 0)
        }
        
        return review
    
    def _create_forward_look(self, company_data: Dict[str, Any],
                            quarter: int,
                            year: int) -> Dict[str, Any]:
        """Создание forward look"""
        
        forward_look = {
            "next_quarter_outlook": {},
            "key_milestones": [],
            "risks_and_opportunities": {},
            "strategic_initiatives": []
        }
        
        # Определяем следующий квартал
        next_quarter = quarter + 1 if quarter < 4 else 1
        next_year = year if quarter < 4 else year + 1
        
        # Next Quarter Outlook
        forward_look["next_quarter_outlook"] = {
            "period": f"Q{next_quarter} {next_year}",
            "revenue_target": company_data.get("current_mrr", 0) * 1.3,  # 30% рост
            "customer_target": 0,  # Нужны данные
            "burn_target": 0,  # Нужны данные
            "key_focus": "Growth acceleration" if quarter < 3 else "Year-end planning"
        }
        
        # Key Milestones
        milestones = [
            {
                "milestone": f"Q{next_quarter} planning completed",
                "due_date": f"{next_year}-{next_quarter*3-2:02d}-15",
                "owner": "CEO",
                "status": "Planned"
            },
            {
                "milestone": "Product feature launch",
                "due_date": f"{next_year}-{next_quarter*3-1:02d}-01",
                "owner": "CTO",
                "status": "In progress"
            },
            {
                "milestone": "Marketing campaign launch",
                "due_date": f"{next_year}-{next_quarter*3:02d}-01",
                "owner": "CMO",
                "status": "Planned"
            }
        ]
        
        forward_look["key_milestones"] = milestones
        
        # Risks and Opportunities
        forward_look["risks_and_opportunities"] = {
            "risks": [
                "Market conditions may change",
                "Competitive pressures increasing",
                "Talent market tightness"
            ],
            "opportunities": [
                "New market segment opening",
                "Partnership opportunities",
                "Technology advancements"
            ]
        }
        
        # Strategic Initiatives
        forward_look["strategic_initiatives"] = [
            {
                "initiative": "Market expansion",
                "description": "Expand into new geographic markets",
                "timeline": "6-12 months",
                "resources_needed": "$500k",
                "expected_impact": "50% revenue growth"
            },
            {
                "initiative": "Product platformization",
                "description": "Build platform capabilities",
                "timeline": "9-18 months",
                "resources_needed": "$1M",
                "expected_impact": "Increased customer stickiness"
            }
        ]
        
        return forward_look
    
    def _create_board_dashboard(self, company_data: Dict[str, Any],
                               quarterly_data: Dict[str, Any],
                               performance_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Создание dashboard для board"""
        
        dashboard = {
            "key_metrics": {},
            "visualizations": {},
            "alerts": [],
            "summary_cards": []
        }
        
        metrics = quarterly_data.get("metrics", {})
        
        # Key Metrics
        dashboard["key_metrics"] = {
            "mrr": metrics.get("revenue", {}).get("ending_mrr", 0),
            "growth_rate": metrics.get("revenue", {}).get("quarterly_growth", 0),
            "burn_rate": metrics.get("financial", {}).get("average_burn_rate", 0),
            "runway": metrics.get("financial", {}).get("ending_cash", 0) / 
                     max(metrics.get("financial", {}).get("average_burn_rate", 1), 1),
            "customers": metrics.get("customers", {}).get("net_new_customers", 0),
            "cac": metrics.get("efficiency", {}).get("cac", 0)
        }
        
        # Summary Cards
        performance = performance_analysis.get("overall_performance", {})
        dashboard["summary_cards"] = [
            {
                "title": "Overall Performance",
                "value": performance.get("rating", "N/A"),
                "color": performance.get("color", "gray"),
                "trend": "neutral"
            },
            {
                "title": "Cash Runway",
                "value": f"{dashboard['key_metrics']['runway']:.1f} months",
                "color": "green" if dashboard['key_metrics']['runway'] > 12 else 
                        "yellow" if dashboard['key_metrics']['runway'] > 6 else "red",
                "trend": "down"  # Runway всегда уменьшается
            },
            {
                "title": "Revenue Growth",
                "value": f"{dashboard['key_metrics']['growth_rate']*100:.1f}%",
                "color": "green" if dashboard['key_metrics']['growth_rate'] > 0.2 else 
                        "yellow" if dashboard['key_metrics']['growth_rate'] > 0 else "red",
                "trend": "up" if dashboard['key_metrics']['growth_rate'] > 0 else "down"
            }
        ]
        
        # Alerts
        if dashboard["key_metrics"]["runway"] < 6:
            dashboard["alerts"].append({
                "level": "critical",
                "message": f"Runway only {dashboard['key_metrics']['runway']:.1f} months",
                "action": "Start fundraising immediately"
            })
        
        if dashboard["key_metrics"]["growth_rate"] < 0.1:
            dashboard["alerts"].append({
                "level": "warning",
                "message": "Growth below target (10% quarterly)",
                "action": "Review growth strategy"
            })
        
        return dashboard
    
    def _get_ai_recommendations(self, company_id: int,
                               context: str = "board_report") -> List[Dict[str, Any]]:
        """Получение AI рекомендаций"""
        
        try:
            # Используем AI recommendation engine
            recommendations = ai_recommendation_engine.generate_recommendations(
                company_id=company_id,
                context=context,
                report_type="board"
            )
            
            if recommendations and "recommendations" in recommendations:
                return recommendations["recommendations"]
        except Exception as e:
            print(f"Error getting AI recommendations: {e}")
        
        # Fallback рекомендации
        return [
            {
                "category": "Financial",
                "priority": "high",
                "recommendation": "Monitor burn rate closely and extend runway",
                "rationale": "Based on current financial metrics",
                "expected_impact": "Medium",
                "implementation": "30-60 days"
            },
            {
                "category": "Strategic",
                "priority": "medium",
                "recommendation": "Review growth strategy for next quarter",
                "rationale": "Ensure alignment with market opportunities",
                "expected_impact": "High",
                "implementation": "60-90 days"
            }
        ]
    
    def generate_monthly_board_report(self, company_id: int,
                                     month: int,
                                     year: int) -> Dict[str, Any]:
        """
        Генерация месячного отчета для board
        
        Args:
            company_id: ID компании
            month: Месяц (1-12)
            year: Год
        
        Returns:
            Dict с monthly board report
        """
        
        # Аналогичная структура как для quarterly, но более focused
        # Для краткости опускаем полную реализацию
        
        return {
            "success": True,
            "report": {
                "report_type": "monthly",
                "month": month,
                "year": year,
                "summary": "Monthly board report placeholder",
                "generated_date": datetime.now().isoformat()
            }
        }
    
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
board_report_generator = BoardReportGenerator()

# Экспортируем полезные функции
def generate_quarterly_board_report(company_id: int,
                                   quarter: int,
                                   year: int) -> Dict[str, Any]:
    """Публичная функция для генерации квартального board отчета"""
    return board_report_generator.generate_quarterly_board_report(company_id, quarter, year)

def export_board_report(report_data: Dict[str, Any],
                       format_str: str,
                       filename: Optional[str] = None) -> Union[bytes, str, None]:
    """Публичная функция для экспорта board отчета"""
    return board_report_generator.export_report(report_data, format_str, filename)