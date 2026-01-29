"""
Генератор отчетов для инвесторов
Создание профессиональных pitch decks и investment memos
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Union
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from dataclasses import dataclass

# Импорты для визуализации
try:
    import plotly.graph_objects as go
    import plotly.io as pio
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

from services.financial_system.financial_planner import financial_planner
from services.financial_system.saas_benchmarks import saas_benchmarks
from services.core.runway_calculator import runway_calculator
from services.utils.export_generator import export_generator, ExportFormat

class ReportType(Enum):
    """Типы отчетов для инвесторов"""
    PITCH_DECK = "pitch_deck"
    INVESTMENT_MEMO = "investment_memo"
    EXECUTIVE_SUMMARY = "executive_summary"
    DUE_DILIGENCE = "due_diligence"
    QUARTERLY_UPDATE = "quarterly_update"

@dataclass
class InvestorReport:
    """Отчет для инвесторов"""
    report_id: str
    company_id: int
    report_type: ReportType
    generated_date: datetime
    sections: Dict[str, Any]
    financial_data: Dict[str, Any]
    metrics_summary: Dict[str, Any]
    recommendations: List[str]
    attachments: List[Dict[str, Any]]

class InvestorReportGenerator:
    """
    Генератор отчетов для инвесторов
    Создание pitch decks, investment memos и других investor materials
    """
    
    def __init__(self):
        self.report_templates = self._load_report_templates()
    
    def _load_report_templates(self) -> Dict[str, Dict[str, Any]]:
        """Загрузка шаблонов отчетов"""
        
        templates = {
            "pitch_deck": {
                "sections": [
                    "cover",
                    "problem",
                    "solution",
                    "market",
                    "product",
                    "traction",
                    "business_model",
                    "competition",
                    "team",
                    "financials",
                    "funding",
                    "ask"
                ],
                "slide_count": 12,
                "format": "pptx"
            },
            "investment_memo": {
                "sections": [
                    "executive_summary",
                    "investment_thesis",
                    "market_analysis",
                    "product_technology",
                    "competitive_landscape",
                    "financial_analysis",
                    "team_assessment",
                    "risks",
                    "valuation",
                    "recommendation"
                ],
                "format": "pdf"
            },
            "executive_summary": {
                "sections": [
                    "overview",
                    "key_achievements",
                    "financial_highlights",
                    "growth_trajectory",
                    "key_metrics",
                    "funding_needs",
                    "next_milestones"
                ],
                "format": "pdf"
            }
        }
        
        return templates
    
    def generate_pitch_deck(self, company_id: int,
                           funding_round: str = "seed",
                           ask_amount: float = 0) -> Dict[str, Any]:
        """
        Генерация pitch deck для инвесторов
        
        Args:
            company_id: ID компании
            funding_round: Раунд финансирования
            ask_amount: Запрашиваемая сумма
        
        Returns:
            Dict с pitch deck данными
        """
        
        # Получение данных компании
        company_data = self._get_company_data(company_id)
        
        if not company_data:
            return {
                "success": False,
                "error": "Company data not found"
            }
        
        # Получение финансовых данных
        financial_data = self._get_financial_data(company_id)
        
        # Получение метрик
        metrics_summary = self._get_metrics_summary(company_data, financial_data)
        
        # Расчет valuation
        valuation_analysis = self._calculate_valuation(company_data, financial_data, funding_round)
        
        # Определение ask_amount если не указан
        if ask_amount == 0:
            ask_amount = self._calculate_funding_ask(company_data, financial_data, funding_round)
        
        # Создание pitch deck
        pitch_deck = {
            "report_type": "pitch_deck",
            "company": company_data,
            "funding_round": funding_round,
            "ask_amount": ask_amount,
            "valuation": valuation_analysis,
            "slides": self._create_pitch_deck_slides(company_data, financial_data, metrics_summary, 
                                                   funding_round, ask_amount, valuation_analysis),
            "financial_projections": self._create_financial_projections(company_data, financial_data),
            "market_data": self._get_market_data(company_data),
            "team_info": self._get_team_info(company_id),
            "generated_date": datetime.now().isoformat()
        }
        
        # Создание visualizations
        pitch_deck["visualizations"] = self._create_pitch_deck_visualizations(
            company_data, financial_data, metrics_summary
        )
        
        # Генерация рекомендаций
        pitch_deck["recommendations"] = self._generate_pitch_deck_recommendations(
            company_data, metrics_summary, valuation_analysis
        )
        
        return {
            "success": True,
            "report": pitch_deck,
            "export_formats": ["pdf", "pptx", "html"],
            "estimated_pages": 12
        }
    
    def _get_company_data(self, company_id: int) -> Optional[Dict[str, Any]]:
        """Получение данных компании"""
        
        try:
            from database.db_manager import db_manager
            
            company = db_manager.get_company(company_id)
            if not company:
                return None
            
            company_dict = company.to_dict()
            
            # Добавляем дополнительные данные
            financials = db_manager.get_actual_financials_by_filters(
                {"company_id": company_id}
            )
            
            if financials:
                latest_financial = max(financials, key=lambda x: (x.year, x.month_number))
                company_dict["latest_financial"] = latest_financial.to_dict()
            
            return company_dict
        except ImportError:
            # Если БД недоступна, создаем mock данные для разработки
            return {
                "id": company_id,
                "company_name": f"Company {company_id}",
                "stage": "seed",
                "current_mrr": 50000,
                "current_customers": 500,
                "monthly_price": 100,
                "team_size": 10,
                "cash_balance": 1000000,
                "industry": "SaaS",
                "description": "A SaaS company"
            }
    
    def _get_financial_data(self, company_id: int) -> Dict[str, Any]:
        """Получение финансовых данных"""
        
        financial_data = {
            "actuals": [],
            "plans": [],
            "metrics": {}
        }
        
        try:
            from database.db_manager import db_manager
            
            # Получение фактических данных
            actuals = db_manager.get_actual_financials_by_filters(
                {"company_id": company_id}
            )
            
            if actuals:
                financial_data["actuals"] = [a.to_dict() for a in actuals]
                
                # Расчет key metrics из actuals
                latest_actual = max(actuals, key=lambda x: (x.year, x.month_number))
                financial_data["metrics"]["latest"] = {
                    "mrr": latest_actual.actual_mrr,
                    "burn_rate": latest_actual.actual_burn_rate,
                    "runway": latest_actual.actual_runway
                }
            
            # Получение планов
            plans = db_manager.get_financial_plans(company_id)
            
            if plans:
                latest_plan = max(plans, key=lambda x: x.created_at)
                monthly_plans = db_manager.get_monthly_plans(latest_plan.id)
                
                financial_data["plans"] = [p.to_dict() for p in monthly_plans]
                
                # Расчет projected metrics
                if monthly_plans:
                    projected_mrr = monthly_plans[-1].plan_mrr if monthly_plans else 0
                    financial_data["metrics"]["projected"] = {
                        "projected_mrr": projected_mrr,
                        "growth_rate": self._calculate_projected_growth(monthly_plans)
                    }
        except ImportError:
            # Mock данные для разработки
            financial_data["actuals"] = [
                {"actual_mrr": 50000, "actual_burn_rate": 30000, "actual_runway": 12}
            ]
            financial_data["metrics"]["latest"] = {
                "mrr": 50000,
                "burn_rate": 30000,
                "runway": 12
            }
            financial_data["metrics"]["projected"] = {
                "projected_mrr": 75000,
                "growth_rate": 0.1
            }
        
        return financial_data
    
    def _calculate_projected_growth(self, monthly_plans: List) -> float:
        """Расчет projected growth rate"""
        
        if len(monthly_plans) < 2:
            return 0
        
        start_mrr = monthly_plans[0].plan_mrr
        end_mrr = monthly_plans[-1].plan_mrr
        
        if start_mrr > 0:
            months = len(monthly_plans)
            cagr = (end_mrr / start_mrr) ** (12 / months) - 1
            return cagr
        
        return 0
    
    def _get_metrics_summary(self, company_data: Dict[str, Any],
                            financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Получение summary метрик"""
        
        metrics = {
            "current": {},
            "historical": {},
            "projected": {},
            "benchmarks": {}
        }
        
        # Current metrics
        metrics["current"] = {
            "mrr": company_data.get("current_mrr", 0),
            "customers": company_data.get("current_customers", 0),
            "arpu": company_data.get("current_mrr", 0) / max(company_data.get("current_customers", 1), 1),
            "team_size": company_data.get("team_size", 1),
            "cash_balance": company_data.get("cash_balance", 0),
            "ltv": 5000,  # Пример
            "cac": 1000,  # Пример
            "ltv_cac_ratio": 5.0,
            "gross_margin": 0.8,
            "cac_payback": 12,
            "runway": financial_data.get("metrics", {}).get("latest", {}).get("runway", 12)
        }
        
        # Historical metrics из actuals
        if financial_data.get("actuals"):
            actuals = financial_data["actuals"]
            
            if len(actuals) >= 3:
                # Расчет growth rate
                mrr_values = [a.get("actual_mrr", 0) for a in actuals[-3:]]
                if mrr_values[0] > 0:
                    growth_rate = (mrr_values[-1] - mrr_values[0]) / mrr_values[0] / 3  # Monthly average
                    metrics["historical"]["growth_rate"] = growth_rate
                
                # Расчет churn rate если есть данные
                if all("actual_churned_customers" in a for a in actuals[-3:]):
                    total_churned = sum(a.get("actual_churned_customers", 0) for a in actuals[-3:])
                    avg_customers = company_data.get("current_customers", 0)
                    if avg_customers > 0:
                        metrics["historical"]["churn_rate"] = total_churned / 3 / avg_customers
        
        # Projected metrics
        if financial_data.get("metrics", {}).get("projected"):
            metrics["projected"] = financial_data["metrics"]["projected"]
        
        # Benchmark comparison
        stage = company_data.get("stage", "pre_seed")
        benchmarks = saas_benchmarks.get_benchmarks(stage)
        
        if benchmarks:
            metrics["benchmarks"] = benchmarks
        
        return metrics
    
    def _calculate_valuation(self, company_data: Dict[str, Any],
                            financial_data: Dict[str, Any],
                            funding_round: str) -> Dict[str, Any]:
        """Расчет valuation"""
        
        # Разные методы valuation в зависимости от стадии
        
        current_mrr = company_data.get("current_mrr", 0)
        growth_rate = financial_data.get("metrics", {}).get("projected", {}).get("growth_rate", 0.1)
        
        if funding_round == "pre_seed":
            # Pre-seed: часто основано на team и market potential
            valuation = max(1000000, current_mrr * 12 * 10)  # Минимум $1M
            
            method = "Market-based (pre-seed typical range)"
            multiples = "N/A (pre-revenue)"
            
        elif funding_round == "seed":
            # Seed: обычно ARR multiple
            arr = current_mrr * 12
            
            if arr > 0:
                # Multiple зависит от growth rate
                base_multiple = 10
                growth_adjustment = min(growth_rate * 100, 50) / 10  # До 5x за growth
                
                multiple = base_multiple + growth_adjustment
                valuation = arr * multiple
                
                method = "ARR Multiple"
                multiples = f"{multiple:.1f}x ARR"
            else:
                valuation = 3000000  # Fallback для pre-revenue seed
                method = "Market-based (pre-revenue seed)"
                multiples = "N/A"
        
        elif funding_round == "series_a":
            # Series A: более сложный расчет
            arr = current_mrr * 12
            
            if arr > 0:
                # Multiple based on growth, margins, and market
                base_multiple = 8
                
                # Growth adjustment
                growth_score = min(growth_rate * 100 / 20, 2.5)  # Normalize growth
                
                # Margin adjustment (предполагаем 80% для SaaS)
                margin_score = 1.2
                
                # Market size adjustment
                market_score = 1.1
                
                total_multiple = base_multiple * growth_score * margin_score * market_score
                valuation = arr * total_multiple
                
                method = "Discounted Cash Flow + Market Multiples"
                multiples = f"{total_multiple:.1f}x ARR"
            else:
                valuation = 8000000  # Fallback
                method = "Market-based"
                multiples = "N/A"
        
        else:
            # Для более поздних раундов
            arr = current_mrr * 12
            valuation = arr * 8  # Консервативный multiple
            method = "Industry Standard Multiple"
            multiples = "8x ARR"
        
        # Добавляем диапазон
        valuation_range = {
            "low": valuation * 0.7,
            "mid": valuation,
            "high": valuation * 1.3
        }
        
        return {
            "amount": valuation,
            "range": valuation_range,
            "method": method,
            "multiples": multiples,
            "assumptions": {
                "current_arr": current_mrr * 12,
                "growth_rate": growth_rate,
                "funding_round": funding_round
            }
        }
    
    def _calculate_funding_ask(self, company_data: Dict[str, Any],
                              financial_data: Dict[str, Any],
                              funding_round: str) -> float:
        """Расчет запрашиваемой суммы финансирования"""
        
        # Основано на runway needs и planned growth
        
        current_cash = company_data.get("cash_balance", 0)
        burn_rate = financial_data.get("metrics", {}).get("latest", {}).get("burn_rate", 10000)
        
        if funding_round == "pre_seed":
            # Pre-seed: обычно 12-18 месяцев runway
            target_runway = 18
            ask_amount = max(burn_rate * target_runway - current_cash, 500000)
            
        elif funding_round == "seed":
            # Seed: 18-24 месяцев runway
            target_runway = 24
            ask_amount = max(burn_rate * target_runway - current_cash, 2000000)
            
        elif funding_round == "series_a":
            # Series A: 24+ месяцев runway + growth capital
            target_runway = 30
            growth_capital = company_data.get("current_mrr", 0) * 12 * 2  # 2x ARR для роста
            ask_amount = max(burn_rate * target_runway - current_cash + growth_capital, 8000000)
            
        else:
            # По умолчанию: 18 месяцев runway
            target_runway = 18
            ask_amount = max(burn_rate * target_runway - current_cash, 1000000)
        
        # Округление
        if ask_amount < 1000000:
            ask_amount = round(ask_amount / 50000) * 50000  # Округление до $50k
        else:
            ask_amount = round(ask_amount / 250000) * 250000  # Округление до $250k
        
        return ask_amount
    
    def _create_pitch_deck_slides(self, company_data: Dict[str, Any],
                                 financial_data: Dict[str, Any],
                                 metrics_summary: Dict[str, Any],
                                 funding_round: str,
                                 ask_amount: float,
                                 valuation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Создание слайдов pitch deck"""
        
        slides = []
        
        # Slide 1: Cover
        slides.append({
            "number": 1,
            "title": company_data.get("company_name", "Company Name"),
            "subtitle": f"{funding_round.replace('_', ' ').title()} Round",
            "content": {
                "tagline": "Revolutionizing [Industry] with [Product]",
                "contact": {
                    "founder": "CEO Name",
                    "email": "ceo@company.com",
                    "website": "company.com"
                },
                "date": datetime.now().strftime("%B %Y")
            },
            "type": "cover"
        })
        
        # Slide 2: Problem
        slides.append({
            "number": 2,
            "title": "The Problem",
            "content": {
                "problem_statement": "Current solutions are [inefficient/expensive/complex]",
                "pain_points": [
                    "Pain point 1 costing businesses $X annually",
                    "Pain point 2 causing Y% productivity loss",
                    "Pain point 3 affecting Z million users"
                ],
                "market_gap": "No solution addresses all three key needs"
            },
            "type": "problem"
        })
        
        # Slide 3: Solution
        slides.append({
            "number": 3,
            "title": "Our Solution",
            "content": {
                "solution_description": "[Product Name] is a [type of solution] that [value proposition]",
                "key_features": [
                    "Feature 1: [Benefit]",
                    "Feature 2: [Benefit]",
                    "Feature 3: [Benefit]"
                ],
                "unique_value": "What makes us different: [unique selling proposition]"
            },
            "type": "solution"
        })
        
        # Slide 4: Market Opportunity
        slides.append({
            "number": 4,
            "title": "Market Opportunity",
            "content": {
                "tam": "$X Billion Total Addressable Market",
                "sam": "$Y Billion Serviceable Addressable Market",
                "som": "$Z Billion Serviceable Obtainable Market",
                "growth_rate": "Market growing at C% annually",
                "key_drivers": [
                    "Driver 1: [explanation]",
                    "Driver 2: [explanation]",
                    "Driver 3: [explanation]"
                ]
            },
            "type": "market"
        })
        
        # Slide 5: Product
        slides.append({
            "number": 5,
            "title": "Product",
            "content": {
                "product_vision": "To become the [goal] for [target market]",
                "current_status": "Launched with [features]",
                "roadmap": [
                    "Next 3 months: [features]",
                    "Next 6 months: [features]",
                    "Next 12 months: [features]"
                ],
                "technology": "Built on modern stack: [technologies]"
            },
            "type": "product"
        })
        
        # Slide 6: Traction
        slides.append({
            "number": 6,
            "title": "Traction",
            "content": {
                "revenue": f"MRR: ${company_data.get('current_mrr', 0):,.0f}",
                "customers": f"Customers: {company_data.get('current_customers', 0):,.0f}",
                "growth": f"Monthly Growth: {metrics_summary.get('historical', {}).get('growth_rate', 0)*100:.1f}%",
                "key_metrics": [
                    f"LTV: ${metrics_summary.get('current', {}).get('ltv', 0):,.0f}",
                    f"CAC: ${metrics_summary.get('current', {}).get('cac', 0):,.0f}",
                    f"LTV/CAC: {metrics_summary.get('current', {}).get('ltv_cac_ratio', 0):.1f}x"
                ],
                "milestones": [
                    "Launched product in [Month Year]",
                    "Reached $Xk MRR in [Month Year]",
                    "Onboarded Y key customers"
                ]
            },
            "type": "traction"
        })
        
        # Slide 7: Business Model
        slides.append({
            "number": 7,
            "title": "Business Model",
            "content": {
                "pricing": f"${company_data.get('monthly_price', 0):.0f}/month per user",
                "revenue_streams": [
                    "Subscription fees",
                    "Enterprise contracts",
                    "Professional services"
                ],
                "customer_acquisition": "Through [channels]",
                "unit_economics": {
                    "cac_payback": f"{metrics_summary.get('current', {}).get('cac_payback', 12):.0f} months",
                    "gross_margin": f"{metrics_summary.get('current', {}).get('gross_margin', 0.8)*100:.0f}%",
                    "net_revenue_retention": "120%+"
                }
            },
            "type": "business_model"
        })
        
        # Slide 8: Competition
        slides.append({
            "number": 8,
            "title": "Competitive Landscape",
            "content": {
                "competitors": [
                    {"name": "Competitor 1", "strengths": "[strengths]", "weaknesses": "[weaknesses]"},
                    {"name": "Competitor 2", "strengths": "[strengths]", "weaknesses": "[weaknesses]"},
                    {"name": "Competitor 3", "strengths": "[strengths]", "weaknesses": "[weaknesses]"}
                ],
                "competitive_advantage": [
                    "Advantage 1: [details]",
                    "Advantage 2: [details]",
                    "Advantage 3: [details]"
                ],
                "market_position": "We are positioned as [positioning]"
            },
            "type": "competition"
        })
        
        # Slide 9: Team
        slides.append({
            "number": 9,
            "title": "Team",
            "content": {
                "founders": [
                    {"name": "Founder 1", "role": "CEO", "background": "[background]"},
                    {"name": "Founder 2", "role": "CTO", "background": "[background]"}
                ],
                "key_hires": [
                    {"name": "Team Member 1", "role": "Role", "background": "[background]"},
                    {"name": "Team Member 2", "role": "Role", "background": "[background]"}
                ],
                "advisors": [
                    {"name": "Advisor 1", "role": "Advisor Role", "background": "[background]"}
                ]
            },
            "type": "team"
        })
        
        # Slide 10: Financials
        slides.append({
            "number": 10,
            "title": "Financial Projections",
            "content": {
                "current_state": {
                    "mrr": f"${company_data.get('current_mrr', 0):,.0f}",
                    "burn_rate": f"${financial_data.get('metrics', {}).get('latest', {}).get('burn_rate', 0):,.0f}/month",
                    "runway": f"{financial_data.get('metrics', {}).get('latest', {}).get('runway', 0):.1f} months"
                },
                "projections": {
                    "year_1": f"${financial_data.get('metrics', {}).get('projected', {}).get('projected_mrr', 0)*12:,.0f} ARR",
                    "year_2": f"${financial_data.get('metrics', {}).get('projected', {}).get('projected_mrr', 0)*12*2.5:,.0f} ARR",
                    "year_3": f"${financial_data.get('metrics', {}).get('projected', {}).get('projected_mrr', 0)*12*6:,.0f} ARR"
                },
                "key_assumptions": [
                    f"{metrics_summary.get('projected', {}).get('growth_rate', 0.1)*100:.0f}% monthly growth",
                    f"{metrics_summary.get('current', {}).get('gross_margin', 0.8)*100:.0f}% gross margin",
                    "CAC payback < 12 months"
                ]
            },
            "type": "financials"
        })
        
        # Slide 11: Funding
        slides.append({
            "number": 11,
            "title": "Funding",
            "content": {
                "previous_funding": {
                    "amount": "$Xk",
                    "investors": "[Investor 1, Investor 2]",
                    "date": "[Month Year]"
                },
                "current_round": {
                    "amount": f"${ask_amount:,.0f}",
                    "valuation": f"${valuation.get('amount', 0):,.0f}",
                    "round": funding_round.replace('_', ' ').title()
                },
                "use_of_funds": {
                    "product": "40%",
                    "sales_marketing": "30%",
                    "team": "20%",
                    "operations": "10%"
                }
            },
            "type": "funding"
        })
        
        # Slide 12: Ask
        slides.append({
            "number": 12,
            "title": "The Ask",
            "content": {
                "funding_need": f"${ask_amount:,.0f}",
                "valuation": f"${valuation.get('amount', 0):,.0f} pre-money",
                "milestones": [
                    f"Reach ${company_data.get('current_mrr', 0)*4:,.0f} MRR",
                    "Expand to [new market]",
                    "Launch [new product]",
                    "Build team to [size] people"
                ],
                "next_steps": [
                    "Schedule follow-up meeting",
                    "Provide detailed financial model",
                    "Customer introductions",
                    "Due diligence materials"
                ]
            },
            "type": "ask"
        })
        
        return slides
    
    def _create_financial_projections(self, company_data: Dict[str, Any],
                                     financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создание финансовых проекций"""
        
        projections = {
            "income_statement": {},
            "balance_sheet": {},
            "cash_flow": {},
            "key_metrics": {}
        }
        
        current_mrr = company_data.get("current_mrr", 0)
        growth_rate = financial_data.get("metrics", {}).get("projected", {}).get("growth_rate", 0.1)
        
        # 3-Year Projections
        for year in [1, 2, 3]:
            year_key = f"year_{year}"
            
            # Revenue Projections
            if year == 1:
                arr = current_mrr * 12 * (1 + growth_rate) ** 6  # Среднее за год
            else:
                arr = current_mrr * 12 * (1 + growth_rate) ** (6 + 12 * (year - 1))
            
            # Cost Projections (типичные для SaaS)
            cogs = arr * 0.2  # 20% COGS
            rnd = arr * 0.3 if year == 1 else arr * 0.25  # R&D
            sales_marketing = arr * 0.4 if year == 1 else arr * 0.35  # Sales & Marketing
            gna = arr * 0.2  # G&A
            
            total_costs = cogs + rnd + sales_marketing + gna
            gross_profit = arr - cogs
            ebitda = gross_profit - (rnd + sales_marketing + gna)
            
            projections["income_statement"][year_key] = {
                "revenue": arr,
                "cogs": cogs,
                "gross_profit": gross_profit,
                "rnd": rnd,
                "sales_marketing": sales_marketing,
                "gna": gna,
                "ebitda": ebitda,
                "ebitda_margin": ebitda / arr if arr > 0 else 0
            }
            
            # Key Metrics Projections
            customers = company_data.get("current_customers", 0) * (1 + growth_rate) ** (12 * year)
            arpu = arr / customers if customers > 0 else 0
            
            projections["key_metrics"][year_key] = {
                "arr": arr,
                "customers": customers,
                "arpu": arpu,
                "cac": arr * 0.35 / (customers * 0.3) if customers > 0 else 0,  # Предположение
                "ltv": arpu * 36,  # 3-year LTV
                "gross_margin": 0.8,
                "net_revenue_retention": 1.2
            }
        
        return projections
    
    def _get_market_data(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Получение данных рынка"""
        
        # Здесь можно добавить реальные данные рынка
        # Пока используем mock данные
        
        industry = company_data.get("industry", "SaaS")
        
        market_data = {
            "industry": industry,
            "market_size": {
                "tam": 50000000000,  # $50B
                "sam": 10000000000,   # $10B
                "som": 500000000      # $500M
            },
            "growth_rates": {
                "industry": 0.15,  # 15% annually
                "segment": 0.25    # 25% for our segment
            },
            "key_trends": [
                "Trend 1: Digital transformation accelerating",
                "Trend 2: Cloud adoption increasing",
                "Trend 3: Remote work driving SaaS demand"
            ],
            "competitive_landscape": {
                "leaders": ["Company A", "Company B"],
                "challengers": ["Company C", "Company D"],
                "niche_players": ["Company E", "Company F"]
            }
        }
        
        return market_data
    
    def _get_team_info(self, company_id: int) -> Dict[str, Any]:
        """Получение информации о команде"""
        
        # Здесь можно добавить реальные данные команды из БД
        # Пока используем mock данные
        
        team_info = {
            "founders": [
                {
                    "name": "Alex Johnson",
                    "title": "CEO",
                    "background": "Former PM at Tech Giant, CS degree from Stanford",
                    "linkedin": "linkedin.com/in/alexjohnson"
                },
                {
                    "name": "Sam Lee",
                    "title": "CTO",
                    "background": "Ex-Google engineer, PhD in Computer Science",
                    "linkedin": "linkedin.com/in/samlee"
                }
            ],
            "team_size": 8,
            "key_hires": [
                {
                    "name": "Taylor Smith",
                    "title": "Head of Sales",
                    "background": "Built sales team at SaaS Company",
                    "linkedin": "linkedin.com/in/taylorsmith"
                }
            ],
            "advisors": [
                {
                    "name": "Dr. Maria Chen",
                    "role": "Technical Advisor",
                    "background": "Professor at MIT, AI expert"
                }
            ]
        }
        
        return team_info
    
    def _create_pitch_deck_visualizations(self, company_data: Dict[str, Any],
                                         financial_data: Dict[str, Any],
                                         metrics_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Создание визуализаций для pitch deck"""
        
        visualizations = {}
        
        try:
            # Импортируем visualization engine если доступен
            from services.utils.visualization import visualization_engine
            VISUALIZATION_AVAILABLE = True
        except ImportError:
            VISUALIZATION_AVAILABLE = False
        
        if VISUALIZATION_AVAILABLE and PLOTLY_AVAILABLE:
            # MRR Growth Chart
            if financial_data.get("plans"):
                try:
                    mrr_chart = visualization_engine.create_mrr_growth_chart(financial_data["plans"])
                    visualizations["mrr_growth"] = self._fig_to_html(mrr_chart)
                except:
                    pass
            
            # Financial Metrics Table
            if metrics_summary.get("current"):
                try:
                    metrics_table = visualization_engine.create_metrics_table(metrics_summary["current"])
                    visualizations["metrics_table"] = self._fig_to_html(metrics_table)
                except:
                    pass
        
        # Market Size Chart
        if PLOTLY_AVAILABLE:
            market_data = self._get_market_data(company_data)
            if market_data.get("market_size"):
                fig = go.Figure()
                
                sizes = market_data["market_size"]
                labels = ['TAM', 'SAM', 'SOM']
                values = [sizes['tam'], sizes['sam'], sizes['som']]
                
                fig.add_trace(go.Bar(
                    x=labels,
                    y=values,
                    text=[f"${v/1e9:.1f}B" for v in values],
                    textposition='auto',
                    marker_color=['#2E86C1', '#3498DB', '#5DADE2']
                ))
                
                fig.update_layout(
                    title="Market Opportunity",
                    yaxis_title="Market Size ($)",
                    showlegend=False,
                    height=400
                )
                
                visualizations["market_size"] = self._fig_to_html(fig)
        
        return visualizations
    
    def _fig_to_html(self, fig) -> str:
        """Конвертация plotly figure в HTML"""
        if PLOTLY_AVAILABLE:
            return pio.to_html(fig, full_html=False)
        return ""
    
    def _generate_pitch_deck_recommendations(self, company_data: Dict[str, Any],
                                           metrics_summary: Dict[str, Any],
                                           valuation: Dict[str, Any]) -> List[str]:
        """Генерация рекомендаций для pitch deck"""
        
        recommendations = []
        
        # Рекомендации на основе метрик
        current_metrics = metrics_summary.get("current", {})
        
        # LTV/CAC рекомендации
        ltv_cac_ratio = current_metrics.get("ltv_cac_ratio", 0)
        if ltv_cac_ratio < 3:
            recommendations.append(
                "Improve LTV/CAC ratio before fundraising. Current ratio is below SaaS benchmark of 3x."
            )
        
        # Growth рекомендации
        growth_rate = metrics_summary.get("historical", {}).get("growth_rate", 0)
        if growth_rate < 0.1:
            recommendations.append(
                "Accelerate growth to at least 10% monthly before Series A fundraising."
            )
        
        # Runway рекомендации
        runway = current_metrics.get("runway", 0)
        if runway < 6:
            recommendations.append(
                "Extend runway to at least 6 months before starting fundraising process."
            )
        
        # Valuation рекомендации
        if valuation.get("amount", 0) > 10000000 and company_data.get("current_mrr", 0) < 50000:
            recommendations.append(
                "Consider adjusting valuation expectations based on current traction."
            )
        
        # Общие рекомендации
        recommendations.extend([
            "Prepare detailed financial model with 3-year projections",
            "Build advisory board with industry experts",
            "Secure customer testimonials and case studies",
            "Develop clear use-of-funds breakdown",
            "Practice pitch with multiple investor personas"
        ])
        
        return recommendations
    
    def generate_investment_memo(self, company_id: int,
                                investment_amount: float,
                                valuation: float) -> Dict[str, Any]:
        """
        Генерация investment memo
        
        Args:
            company_id: ID компании
            investment_amount: Сумма инвестиций
            valuation: Valuation компании
        
        Returns:
            Dict с investment memo
        """
        
        # Получение данных компании
        company_data = self._get_company_data(company_id)
        
        if not company_data:
            return {
                "success": False,
                "error": "Company data not found"
            }
        
        # Получение финансовых данных
        financial_data = self._get_financial_data(company_id)
        
        # Получение метрик
        metrics_summary = self._get_metrics_summary(company_data, financial_data)
        
        # Анализ инвестиционной возможности
        investment_analysis = self._analyze_investment_opportunity(
            company_data, financial_data, investment_amount, valuation
        )
        
        # Создание investment memo
        investment_memo = {
            "report_type": "investment_memo",
            "company": company_data,
            "investment_details": {
                "amount": investment_amount,
                "valuation": valuation,
                "ownership": investment_amount / valuation if valuation > 0 else 0
            },
            "sections": self._create_investment_memo_sections(
                company_data, financial_data, metrics_summary, investment_analysis
            ),
            "financial_analysis": self._create_detailed_financial_analysis(financial_data),
            "risk_assessment": self._assess_investment_risks(company_data, financial_data),
            "recommendation": self._generate_investment_recommendation(investment_analysis),
            "generated_date": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "report": investment_memo,
            "export_formats": ["pdf", "docx"],
            "estimated_pages": 20
        }
    
    def _analyze_investment_opportunity(self, company_data: Dict[str, Any],
                                       financial_data: Dict[str, Any],
                                       investment_amount: float,
                                       valuation: float) -> Dict[str, Any]:
        """Анализ инвестиционной возможности"""
        
        analysis = {
            "valuation_analysis": {},
            "return_potential": {},
            "comparables": {},
            "investment_thesis": {}
        }
        
        current_mrr = company_data.get("current_mrr", 0)
        growth_rate = financial_data.get("metrics", {}).get("projected", {}).get("growth_rate", 0.1)
        
        # Valuation Analysis
        arr = current_mrr * 12
        revenue_multiple = valuation / arr if arr > 0 else 0
        
        analysis["valuation_analysis"] = {
            "current_arr": arr,
            "revenue_multiple": revenue_multiple,
            "industry_average_multiple": 10.0,
            "premium_discount": f"{(revenue_multiple / 10.0 - 1) * 100:.1f}%",
            "justification": "Based on growth rate, market position, and team"
        }
        
        # Return Potential
        # Project 5-year exit scenario
        exit_multiple = 8.0  # Консервативный exit multiple
        projected_arr_5yr = arr * (1 + growth_rate) ** 60  # 5 years monthly compounding
        exit_valuation = projected_arr_5yr * exit_multiple
        ownership = investment_amount / valuation
        exit_proceeds = exit_valuation * ownership
        
        analysis["return_potential"] = {
            "investment_amount": investment_amount,
            "ownership_percentage": ownership * 100,
            "projected_exit_valuation": exit_valuation,
            "projected_exit_proceeds": exit_proceeds,
            "multiple_on_capital": exit_proceeds / investment_amount,
            "irr": self._calculate_irr(investment_amount, exit_proceeds, 5)
        }
        
        # Comparables Analysis
        analysis["comparables"] = {
            "public_comparables": [
                {"company": "Public Co 1", "multiple": 12.0, "growth": 25},
                {"company": "Public Co 2", "multiple": 10.0, "growth": 30},
                {"company": "Public Co 3", "multiple": 8.0, "growth": 20}
            ],
            "recent_transactions": [
                {"company": "Private Co 1", "multiple": 15.0, "stage": "Series B"},
                {"company": "Private Co 2", "multiple": 12.0, "stage": "Series A"}
            ]
        }
        
        # Investment Thesis
        analysis["investment_thesis"] = {
            "primary_thesis": "Investing in [Company] because of [reason 1], [reason 2], and [reason 3]",
            "key_bets": [
                "Bet 1: Market will grow at X% annually",
                "Bet 2: Company can capture Y% market share",
                "Bet 3: Team can execute on roadmap"
            ],
            "catalysts": [
                "Product launch in Q3",
                "Enterprise partnership announcement",
                "International expansion"
            ]
        }
        
        return analysis
    
    def _calculate_irr(self, investment: float, exit_proceeds: float, years: int) -> float:
        """Расчет IRR"""
        
        # Простой расчет IRR
        if investment <= 0:
            return 0
        
        multiple = exit_proceeds / investment
        irr = multiple ** (1 / years) - 1
        
        return irr
    
    def _create_investment_memo_sections(self, company_data: Dict[str, Any],
                                        financial_data: Dict[str, Any],
                                        metrics_summary: Dict[str, Any],
                                        investment_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Создание разделов investment memo"""
        
        sections = {}
        
        # Executive Summary
        sections["executive_summary"] = {
            "company_overview": f"{company_data.get('company_name')} is a [description]",
            "investment_highlights": [
                f"Strong traction: ${company_data.get('current_mrr', 0):,.0f} MRR",
                f"Rapid growth: {metrics_summary.get('historical', {}).get('growth_rate', 0)*100:.1f}% monthly",
                f"Experienced team with [background]",
                f"Large market opportunity: ${self._get_market_data(company_data).get('market_size', {}).get('tam', 0)/1e9:.1f}B TAM"
            ],
            "investment_terms": {
                "amount": f"${investment_analysis.get('investment_details', {}).get('amount', 0):,.0f}",
                "valuation": f"${investment_analysis.get('investment_details', {}).get('valuation', 0):,.0f}",
                "ownership": f"{investment_analysis.get('investment_details', {}).get('ownership', 0)*100:.1f}%"
            },
            "recommendation": investment_analysis.get("recommendation", "Invest")
        }
        
        # Investment Thesis
        sections["investment_thesis"] = investment_analysis.get("investment_thesis", {})
        
        # Market Analysis
        market_data = self._get_market_data(company_data)
        sections["market_analysis"] = {
            "market_size": market_data.get("market_size", {}),
            "growth_trends": market_data.get("growth_rates", {}),
            "key_drivers": market_data.get("key_trends", []),
            "competitive_landscape": market_data.get("competitive_landscape", {})
        }
        
        # Product & Technology
        sections["product_technology"] = {
            "product_description": "[Product description]",
            "technology_stack": "[Technology stack]",
            "ip_status": "Patents pending in [countries]",
            "roadmap": [
                "Q3: Feature launch",
                "Q4: Platform expansion",
                "Next year: International rollout"
            ]
        }
        
        # Financial Analysis
        sections["financial_analysis"] = {
            "current_financials": {
                "mrr": company_data.get("current_mrr", 0),
                "burn_rate": financial_data.get("metrics", {}).get("latest", {}).get("burn_rate", 0),
                "runway": financial_data.get("metrics", {}).get("latest", {}).get("runway", 0)
            },
            "key_metrics": metrics_summary.get("current", {}),
            "projections": self._create_financial_projections(company_data, financial_data),
            "valuation_analysis": investment_analysis.get("valuation_analysis", {})
        }
        
        # Team Assessment
        team_info = self._get_team_info(company_data.get("id", 0))
        sections["team_assessment"] = {
            "founders": team_info.get("founders", []),
            "team_strengths": [
                "Technical expertise in [domain]",
                "Previous startup experience",
                "Industry connections"
            ],
            "gaps": [
                "Need head of marketing",
                "Could use board member with exit experience"
            ]
        }
        
        # Risk Assessment
        sections["risks"] = self._assess_investment_risks(company_data, financial_data)
        
        # Return Analysis
        sections["return_analysis"] = investment_analysis.get("return_potential", {})
        
        # Recommendation
        sections["recommendation"] = {
            "decision": investment_analysis.get("recommendation", "Invest"),
            "rationale": "Based on [reasons]",
            "conditions": [
                "Condition 1: [detail]",
                "Condition 2: [detail]"
            ],
            "next_steps": [
                "Complete due diligence",
                "Finalize legal documents",
                "Schedule board seat"
            ]
        }
        
        return sections
    
    def _create_detailed_financial_analysis(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создание детального финансового анализа"""
        
        analysis = {
            "historical_performance": {},
            "unit_economics": {},
            "financial_health": {},
            "sensitivity_analysis": {}
        }
        
        # Historical Performance
        if financial_data.get("actuals"):
            actuals = financial_data["actuals"]
            
            if len(actuals) >= 3:
                analysis["historical_performance"] = {
                    "revenue_growth": self._calculate_revenue_growth(actuals),
                    "cost_efficiency": self._calculate_cost_efficiency(actuals),
                    "profitability_trend": self._calculate_profitability_trend(actuals)
                }
        
        # Unit Economics
        analysis["unit_economics"] = {
            "cac_analysis": {
                "current_cac": 0,  # Нужны данные
                "cac_trend": "stable",
                "cac_by_channel": {"channel1": 1000, "channel2": 1500}
            },
            "ltv_analysis": {
                "current_ltv": 0,  # Нужны данные
                "ltv_trend": "improving",
                "ltv_components": {"base": 5000, "expansion": 2000}
            },
            "payback_period": 12  # месяцев
        }
        
        # Financial Health
        analysis["financial_health"] = {
            "liquidity": {
                "current_ratio": 2.5,
                "quick_ratio": 2.0,
                "cash_burn_rate": financial_data.get("metrics", {}).get("latest", {}).get("burn_rate", 0)
            },
            "efficiency": {
                "asset_turnover": 1.2,
                "working_capital_turnover": 2.5
            }
        }
        
        # Sensitivity Analysis
        analysis["sensitivity_analysis"] = {
            "scenarios": [
                {"scenario": "Base Case", "arr_5yr": 10000000, "valuation": 80000000},
                {"scenario": "Upside Case", "arr_5yr": 25000000, "valuation": 200000000},
                {"scenario": "Downside Case", "arr_5yr": 5000000, "valuation": 40000000}
            ],
            "key_variables": ["Growth Rate", "CAC", "Churn Rate"],
            "break_even_analysis": {
                "months_to_breakeven": 24,
                "arr_at_breakeven": 2000000
            }
        }
        
        return analysis
    
    def _calculate_revenue_growth(self, actuals: List[Dict]) -> Dict[str, Any]:
        """Расчет роста выручки"""
        
        if len(actuals) < 2:
            return {"insufficient_data": True}
        
        mrr_values = [a.get("actual_mrr", 0) for a in actuals]
        
        growth_rates = []
        for i in range(1, len(mrr_values)):
            if mrr_values[i-1] > 0:
                growth_rate = (mrr_values[i] - mrr_values[i-1]) / mrr_values[i-1]
                growth_rates.append(growth_rate)
        
        if growth_rates:
            avg_growth = np.mean(growth_rates)
            volatility = np.std(growth_rates)
            
            return {
                "average_monthly_growth": avg_growth,
                "growth_volatility": volatility,
                "growth_trend": "accelerating" if len(growth_rates) >= 3 and growth_rates[-1] > growth_rates[0] else "decelerating"
            }
        
        return {"insufficient_data": True}
    
    def _calculate_cost_efficiency(self, actuals: List[Dict]) -> Dict[str, Any]:
        """Расчет эффективности затрат"""
        
        # Упрощенный расчет
        return {
            "cost_per_mrr_dollar": 0.8,  # $0.8 cost per $1 MRR
            "efficiency_trend": "improving",
            "key_cost_drivers": ["Salaries", "Cloud Infrastructure", "Marketing"]
        }
    
    def _calculate_profitability_trend(self, actuals: List[Dict]) -> Dict[str, Any]:
        """Расчет тренда profitability"""
        
        # Упрощенный расчет
        return {
            "gross_margin_trend": "stable",
            "operating_margin_trend": "improving",
            "path_to_profitability": "24 months"
        }
    
    def _assess_investment_risks(self, company_data: Dict[str, Any],
                                financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Оценка инвестиционных рисков"""
        
        risks = {
            "market_risks": [],
            "execution_risks": [],
            "financial_risks": [],
            "team_risks": [],
            "mitigation_strategies": []
        }
        
        # Market Risks
        risks["market_risks"] = [
            {
                "risk": "Market saturation",
                "probability": "medium",
                "impact": "high",
                "description": "Increased competition could reduce market share"
            },
            {
                "risk": "Regulatory changes",
                "probability": "low",
                "impact": "high",
                "description": "New regulations could increase compliance costs"
            }
        ]
        
        # Execution Risks
        runway = financial_data.get("metrics", {}).get("latest", {}).get("runway", 0)
        
        risks["execution_risks"] = [
            {
                "risk": "Short runway",
                "probability": "high" if runway < 6 else "medium",
                "impact": "critical",
                "description": f"Only {runway:.1f} months of runway remaining"
            },
            {
                "risk": "Product development delays",
                "probability": "medium",
                "impact": "high",
                "description": "Could miss key milestones"
            }
        ]
        
        # Financial Risks
        ltv_cac_ratio = company_data.get("ltv_cac_ratio", 0)
        
        risks["financial_risks"] = [
            {
                "risk": "Poor unit economics",
                "probability": "medium" if ltv_cac_ratio < 3 else "low",
                "impact": "high",
                "description": f"LTV/CAC ratio of {ltv_cac_ratio:.1f}x below benchmark"
            },
            {
                "risk": "Burn rate too high",
                "probability": "medium",
                "impact": "high",
                "description": "Could require additional funding sooner than expected"
            }
        ]
        
        # Team Risks
        team_size = company_data.get("team_size", 0)
        
        risks["team_risks"] = [
            {
                "risk": "Key person dependency",
                "probability": "medium",
                "impact": "high",
                "description": "Heavy reliance on founders"
            },
            {
                "risk": "Team scaling challenges",
                "probability": "medium",
                "impact": "medium",
                "description": f"Current team of {team_size} may struggle with rapid growth"
            }
        ]
        
        # Mitigation Strategies
        risks["mitigation_strategies"] = [
            "Diversify revenue streams",
            "Build cash reserves",
            "Hire key positions early",
            "Establish board oversight",
            "Regular financial reviews"
        ]
        
        return risks
    
    def _generate_investment_recommendation(self, investment_analysis: Dict[str, Any]) -> str:
        """Генерация инвестиционной рекомендации"""
        
        return_potential = investment_analysis.get("return_potential", {})
        multiple = return_potential.get("multiple_on_capital", 0)
        
        if multiple >= 10:
            return "Strong Invest (10x+ potential)"
        elif multiple >= 5:
            return "Invest (5-10x potential)"
        elif multiple >= 3:
            return "Consider (3-5x potential)"
        else:
            return "Pass (<3x potential)"
    
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
investor_report_generator = InvestorReportGenerator()

# Экспортируем полезные функции
def generate_investor_pitch_deck(company_id: int,
                                funding_round: str = "seed",
                                ask_amount: float = 0) -> Dict[str, Any]:
    """Публичная функция для генерации pitch deck"""
    return investor_report_generator.generate_pitch_deck(company_id, funding_round, ask_amount)

def generate_investment_memo(company_id: int,
                            investment_amount: float,
                            valuation: float) -> Dict[str, Any]:
    """Публичная функция для генерации investment memo"""
    return investor_report_generator.generate_investment_memo(company_id, investment_amount, valuation)

def export_investor_report(report_data: Dict[str, Any],
                          format_str: str,
                          filename: Optional[str] = None) -> Union[bytes, str, None]:
    """Публичная функция для экспорта отчета инвестора"""
    return investor_report_generator.export_report(report_data, format_str, filename)