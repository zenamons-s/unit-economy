"""
AI рекомендации для SaaS компаний
Использует LLM для анализа данных и генерации рекомендаций
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

# Импорт GigaChat интеграции
try:
    from gigachat_analyst import GigaChatAnalyst
    GIGACHAT_AVAILABLE = True
except ImportError:
    GIGACHAT_AVAILABLE = False
    print("GigaChatAnalyst not available. Using mock recommendations.")

@dataclass
class AIRecommendation:
    """Рекомендация от AI"""
    id: str
    category: str
    title: str
    description: str
    priority: str  # low, medium, high, critical
    confidence: float  # 0-1
    action_items: List[str]
    expected_impact: str  # low, medium, high
    timeframe: str  # immediate, short_term, long_term
    metrics_affected: List[str]
    implementation_difficulty: str  # easy, medium, hard
    created_at: datetime
    data_sources: List[str]
    
    # Добавьте это поле для приоритизации
    weight: float = 0.0

class AIRecommendationEngine:
    """
    Движок AI рекомендаций для SaaS компаний
    Анализирует данные и генерирует персонализированные рекомендации
    """
    
    def __init__(self, use_gigachat: bool = True):
        self.use_gigachat = use_gigachat and GIGACHAT_AVAILABLE
        
        if self.use_gigachat and GIGACHAT_AVAILABLE:
            try:
                self.analyst = GigaChatAnalyst()
            except Exception as e:
                print(f"Error initializing GigaChat: {e}")
                self.analyst = None
                self.use_gigachat = False
        else:
            self.analyst = None
        
        # Кэш рекомендаций
        self.recommendations_cache = {}
        
        # Шаблоны рекомендаций для разных ситуаций
        self.recommendation_templates = {
            "high_burn_rate": {
                "category": "financial_health",
                "priority": "critical",
                "template": "Высокий burn rate ${burn_rate:.0f}/мес. Рекомендуется: {actions}",
                "actions": [
                    "Сократить non-essential расходы",
                    "Оптимизировать облачные расходы",
                    "Пересмотреть маркетинговый бюджет",
                    "Рассмотреть сокращение команды"
                ]
            },
            "low_ltv_cac": {
                "category": "unit_economics",
                "priority": "high",
                "template": "Низкий LTV/CAC ratio {ratio:.1f}x. Рекомендуется: {actions}",
                "actions": [
                    "Улучшить retention через product improvements",
                    "Снизить CAC через оптимизацию маркетинга",
                    "Увеличить цены",
                    "Улучшить onboarding"
                ]
            },
            "short_runway": {
                "category": "fundraising",
                "priority": "critical",
                "template": "Короткий runway {runway:.1f} мес. Рекомендуется: {actions}",
                "actions": [
                    "Начать emergency fundraising",
                    "Сократить burn rate на 30%+",
                    "Расследовать bridge financing",
                    "Подготовить план сокращения"
                ]
            },
            "revenue_growth_slow": {
                "category": "growth",
                "priority": "medium",
                "template": "Медленный рост выручки {growth:.1%}/мес. Рекомендуется: {actions}",
                "actions": [
                    "Активизировать sales efforts",
                    "Запустить новые маркетинговые кампании",
                    "Улучшить conversion rates",
                    "Расширить target market"
                ]
            },
            "high_churn": {
                "category": "retention",
                "priority": "high",
                "template": "Высокий churn {churn:.1%}. Рекомендуется: {actions}",
                "actions": [
                    "Провести exit interviews с уходящими клиентами",
                    "Улучшить customer success",
                    "Добавить features по feedback",
                    "Пересмотреть pricing tiers"
                ]
            }
        }
    
    def analyze_company(self, company_id: int) -> Dict[str, Any]:
        """
        Комплексный анализ компании и генерация рекомендаций
        
        Args:
            company_id: ID компании
        
        Returns:
            Dict с анализом и рекомендациями
        """
        
        # Получение данных компании
        company_data = self._get_company_data(company_id)
        
        if not company_data:
            return {
                "success": False,
                "error": "Company data not found"
            }
        
        # Анализ текущего состояния
        current_analysis = self._analyze_current_state(company_data)
        
        # Анализ трендов
        trend_analysis = self._analyze_trends(company_id, company_data)
        
        # Анализ отклонений от плана
        variance_analysis = self._analyze_variances(company_id)
        
        # Генерация рекомендаций
        recommendations = self._generate_recommendations(
            company_data, current_analysis, trend_analysis, variance_analysis
        )
        
        # Приоритизация рекомендаций
        prioritized_recommendations = self._prioritize_recommendations(recommendations)
        
        # Создание action plan
        action_plan = self._create_action_plan(prioritized_recommendations)
        
        return {
            "success": True,
            "company_id": company_id,
            "analysis_date": datetime.now().isoformat(),
            "current_analysis": current_analysis,
            "trend_analysis": trend_analysis,
            "variance_analysis": variance_analysis,
            "recommendations": recommendations,
            "prioritized_recommendations": prioritized_recommendations,
            "action_plan": action_plan,
            "key_insights": self._extract_key_insights(
                current_analysis, trend_analysis, recommendations
            )
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
        
        # Получение планов
        plans = db_manager.get_financial_plans(company_id)
        
        # Конвертация в dict
        company_dict = company.to_dict()
        company_dict["financials"] = [f.to_dict() for f in financials]
        company_dict["plans"] = [p.to_dict() for p in plans]
        
        return company_dict
    
    def _analyze_current_state(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ текущего состояния компании"""
        
        analysis = {
            "financial_health": {},
            "growth_metrics": {},
            "unit_economics": {},
            "team_metrics": {},
            "risk_factors": []
        }
        
        # Извлекаем последние финансовые данные
        financials = company_data.get("financials", [])
        if not financials:
            return analysis
        
        latest_financial = max(financials, key=lambda x: (x["year"], x["month_number"]))
        
        # Financial health analysis
        burn_rate = latest_financial.get("actual_burn_rate", 0)
        runway = latest_financial.get("actual_runway", 0)
        
        analysis["financial_health"] = {
            "burn_rate": burn_rate,
            "runway_months": runway,
            "cash_balance": company_data.get("cash_balance", 0),
            "status": self._assess_financial_health(burn_rate, runway),
            "issues": self._identify_financial_issues(burn_rate, runway)
        }
        
        # Growth metrics
        mrr = latest_financial.get("actual_mrr", 0)
        new_customers = latest_financial.get("actual_new_customers", 0)
        churned_customers = latest_financial.get("actual_churned_customers", 0)
        
        analysis["growth_metrics"] = {
            "mrr": mrr,
            "new_customers": new_customers,
            "net_new_customers": new_customers - churned_customers,
            "growth_rate": self._calculate_growth_rate(financials),
            "churn_rate": (churned_customers / company_data.get("current_customers", 1) 
                          if company_data.get("current_customers", 0) > 0 else 0)
        }
        
        # Unit economics
        marketing_spend = latest_financial.get("actual_marketing_spend", 0)
        
        analysis["unit_economics"] = {
            "cac": marketing_spend / new_customers if new_customers > 0 else 0,
            "ltv": self._estimate_ltv(company_data, financials),
            "ltv_cac_ratio": 0,  # Будет рассчитано после LTV
            "payback_period": self._estimate_payback_period(company_data, financials),
            "gross_margin": self._estimate_gross_margin(latest_financial)
        }
        
        # Рассчитываем LTV/CAC ratio
        ltv = analysis["unit_economics"]["ltv"]
        cac = analysis["unit_economics"]["cac"]
        analysis["unit_economics"]["ltv_cac_ratio"] = ltv / cac if cac > 0 else 0
        
        # Team metrics
        analysis["team_metrics"] = {
            "team_size": company_data.get("team_size", 1),
            "revenue_per_employee": mrr / company_data.get("team_size", 1) 
                                   if company_data.get("team_size", 0) > 0 else 0,
            "burn_per_employee": burn_rate / company_data.get("team_size", 1) 
                               if company_data.get("team_size", 0) > 0 else 0
        }
        
        # Risk factors
        analysis["risk_factors"] = self._identify_risk_factors(analysis)
        
        return analysis
    
    def _assess_financial_health(self, burn_rate: float, runway: float) -> Dict[str, Any]:
        """Оценка финансового здоровья"""
        
        if runway == float('inf') or burn_rate <= 0:
            return {
                "status": "healthy",
                "color": "green",
                "description": "Positive cash flow или очень долгий runway"
            }
        elif runway >= 18:
            return {
                "status": "excellent",
                "color": "green",
                "description": "Более 1.5 лет runway, отличная позиция"
            }
        elif runway >= 12:
            return {
                "status": "good",
                "color": "blue",
                "description": "1+ год runway, стабильная позиция"
            }
        elif runway >= 9:
            return {
                "status": "warning",
                "color": "yellow",
                "description": "Менее года runway, требуется внимание"
            }
        elif runway >= 6:
            return {
                "status": "concerning",
                "color": "orange",
                "description": "Менее 9 месяцев, требуется action"
            }
        elif runway >= 3:
            return {
                "status": "critical",
                "color": "red",
                "description": "Менее 6 месяцев, emergency меры"
            }
        else:
            return {
                "status": "emergency",
                "color": "darkred",
                "description": "Критически мало времени"
            }
    
    def _identify_financial_issues(self, burn_rate: float, runway: float) -> List[str]:
        """Идентификация финансовых проблем"""
        
        issues = []
        
        if burn_rate > 100000:  # Пример threshold
            issues.append("Очень высокий burn rate")
        
        if runway < 12:
            issues.append(f"Короткий runway: {runway:.1f} месяцев")
        
        if runway < 6:
            issues.append("Критически короткий runway, требуется emergency action")
        
        return issues
    
    def _calculate_growth_rate(self, financials: List[Dict]) -> float:
        """Расчет роста MRR"""
        
        if len(financials) < 2:
            return 0
        
        # Берем последние 3 месяца для расчета
        recent = sorted(financials, key=lambda x: (x["year"], x["month_number"]), reverse=True)[:3]
        recent.reverse()  # В хронологическом порядке
        
        if len(recent) < 2:
            return 0
        
        # Рассчитываем среднемесячный рост
        growth_rates = []
        for i in range(1, len(recent)):
            prev_mrr = recent[i-1].get("actual_mrr", 0)
            curr_mrr = recent[i].get("actual_mrr", 0)
            
            if prev_mrr > 0:
                growth_rate = (curr_mrr - prev_mrr) / prev_mrr
                growth_rates.append(growth_rate)
        
        return np.mean(growth_rates) if growth_rates else 0
    
    def _estimate_ltv(self, company_data: Dict, financials: List[Dict]) -> float:
        """Оценка LTV"""
        
        if not financials:
            return 0
        
        # Берем средний MRR на клиента
        latest = max(financials, key=lambda x: (x["year"], x["month_number"]))
        mrr = latest.get("actual_mrr", 0)
        customers = company_data.get("current_customers", 0)
        
        if customers <= 0:
            return 0
        
        avg_mrr_per_customer = mrr / customers
        
        # Оцениваем lifetime на основе churn
        churn_rate = self._estimate_churn_rate(financials, company_data)
        if churn_rate <= 0:
            lifetime = 12  # Default
        else:
            lifetime = 1 / churn_rate
        
        return avg_mrr_per_customer * lifetime
    
    def _estimate_churn_rate(self, financials: List[Dict], 
                            company_data: Dict) -> float:
        """Оценка churn rate"""
        
        if len(financials) < 3:
            return 0.05  # Default 5%
        
        # Рассчитываем средний churn за последние 3 месяца
        recent = sorted(financials, key=lambda x: (x["year"], x["month_number"]), 
                       reverse=True)[:3]
        
        total_churned = sum(f.get("actual_churned_customers", 0) for f in recent)
        avg_customers = company_data.get("current_customers", 0)
        
        if avg_customers <= 0:
            return 0.05
        
        monthly_churn = total_churned / 3 / avg_customers
        return monthly_churn
    
    def _estimate_payback_period(self, company_data: Dict, 
                                financials: List[Dict]) -> float:
        """Оценка CAC payback period"""
        
        if not financials:
            return 0
        
        latest = max(financials, key=lambda x: (x["year"], x["month_number"]))
        
        cac = latest.get("actual_marketing_spend", 0) / latest.get("actual_new_customers", 1)
        avg_mrr = latest.get("actual_mrr", 0) / company_data.get("current_customers", 1)
        
        if avg_mrr <= 0:
            return 0
        
        return cac / avg_mrr
    
    def _estimate_gross_margin(self, financial_data: Dict) -> float:
        """Оценка gross margin"""
        
        revenue = financial_data.get("actual_mrr", 0)
        cloud_costs = financial_data.get("actual_cloud_services", 0)
        
        if revenue <= 0:
            return 0.8  # Default для SaaS
        
        # Для SaaS обычно 80%+ gross margin
        cost_of_goods = cloud_costs * 0.3  # Примерная оценка
        gross_profit = revenue - cost_of_goods
        
        return gross_profit / revenue if revenue > 0 else 0
    
    def _identify_risk_factors(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Идентификация факторов риска"""
        
        risks = []
        
        # Financial risks
        financial_health = analysis["financial_health"]
        if financial_health["status"] in ["warning", "concerning", "critical", "emergency"]:
            risks.append({
                "category": "financial",
                "severity": "high",
                "description": f"Проблемы с финансовым здоровьем: {financial_health['description']}",
                "mitigation": "Сократить расходы, ускорить fundraising"
            })
        
        # Growth risks
        growth_metrics = analysis["growth_metrics"]
        if growth_metrics["growth_rate"] < 0.05:  # Менее 5% monthly growth
            risks.append({
                "category": "growth",
                "severity": "medium",
                "description": "Медленный рост выручки",
                "mitigation": "Активизировать sales и marketing"
            })
        
        # Unit economics risks
        unit_economics = analysis["unit_economics"]
        if unit_economics["ltv_cac_ratio"] < 3.0:
            risks.append({
                "category": "unit_economics",
                "severity": "high",
                "description": f"Низкий LTV/CAC ratio: {unit_economics['ltv_cac_ratio']:.1f}x",
                "mitigation": "Улучшить retention или снизить CAC"
            })
        
        if unit_economics["payback_period"] > 18:
            risks.append({
                "category": "unit_economics",
                "severity": "medium",
                "description": f"Долгий CAC payback: {unit_economics['payback_period']:.1f} месяцев",
                "mitigation": "Оптимизировать маркетинговые каналы"
            })
        
        # Team risks
        team_metrics = analysis["team_metrics"]
        if team_metrics["burn_per_employee"] > 20000:  # $20k/мес на сотрудника
            risks.append({
                "category": "team",
                "severity": "medium",
                "description": "Высокий burn rate на сотрудника",
                "mitigation": "Оптимизировать team efficiency"
            })
        
        return risks
    
    def _analyze_trends(self, company_id: int, 
                       company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ трендов компании"""
        
        trends = {
            "revenue_trend": {},
            "customer_trend": {},
            "burn_rate_trend": {},
            "efficiency_trend": {}
        }
        
        financials = company_data.get("financials", [])
        if len(financials) < 3:
            return trends
        
        # Сортируем по дате
        sorted_financials = sorted(financials, 
                                  key=lambda x: (x["year"], x["month_number"]))
        
        # Revenue trend
        mrr_values = [f.get("actual_mrr", 0) for f in sorted_financials[-6:]]  # Последние 6 месяцев
        if len(mrr_values) >= 2:
            revenue_growth = self._calculate_trend_growth(mrr_values)
            trends["revenue_trend"] = {
                "direction": "up" if revenue_growth > 0.05 else "down" if revenue_growth < -0.05 else "flat",
                "strength": abs(revenue_growth),
                "growth_rate": revenue_growth,
                "volatility": np.std(mrr_values) / np.mean(mrr_values) if np.mean(mrr_values) > 0 else 0
            }
        
        # Customer trend
        customer_values = [company_data.get("current_customers", 0)]  # Нужны исторические данные
        # TODO: Добавить исторические данные по клиентам
        
        # Burn rate trend
        burn_values = [f.get("actual_burn_rate", 0) for f in sorted_financials[-6:]]
        if len(burn_values) >= 2:
            burn_trend = self._calculate_trend_growth(burn_values)
            trends["burn_rate_trend"] = {
                "direction": "up" if burn_trend > 0.05 else "down" if burn_trend < -0.05 else "flat",
                "strength": abs(burn_trend),
                "trend_value": burn_trend,
                "is_positive": burn_trend < 0  # Снижение burn rate - хорошо
            }
        
        # Efficiency trend (LTV/CAC)
        # TODO: Рассчитать historical efficiency metrics
        
        return trends
    
    def _calculate_trend_growth(self, values: List[float]) -> float:
        """Расчет роста тренда"""
        
        if len(values) < 2:
            return 0
        
        # Простой расчет: процент изменения от первого к последнему
        first = values[0]
        last = values[-1]
        
        if first <= 0:
            return 0
        
        return (last - first) / first
    
    def _analyze_variances(self, company_id: int) -> Dict[str, Any]:
        """Анализ отклонений от плана"""
        
        from services.financial_system.variance_analyzer import analyze_plan_variance
        
        # Получаем последний план компании
        from database.db_manager import db_manager
        plans = db_manager.get_financial_plans(company_id)
        
        if not plans:
            return {"no_plans": True}
        
        latest_plan = max(plans, key=lambda x: x.created_at)
        
        # Анализируем отклонения
        variance_result = analyze_plan_variance(
            company_id, latest_plan.id
        )
        
        if "error" in variance_result:
            return {"error": variance_result["error"]}
        
        # Упрощаем результат для AI анализа
        simplified = {
            "has_variances": len(variance_result.get("significant_variances", [])) > 0,
            "significant_variances_count": len(variance_result.get("significant_variances", [])),
            "critical_variances": [v for v in variance_result.get("significant_variances", []) 
                                  if v.get("significance") == "critical"],
            "worst_performing_metrics": variance_result.get("variance_summary", {}).get("worst_performing_metrics", []),
            "avg_variance": variance_result.get("variance_summary", {}).get("overall_avg_variance", "0%")
        }
        
        return simplified
    
    def _generate_recommendations(self, company_data: Dict[str, Any],
                                 current_analysis: Dict[str, Any],
                                 trend_analysis: Dict[str, Any],
                                 variance_analysis: Dict[str, Any]) -> List[AIRecommendation]:
        """Генерация рекомендаций"""
        
        recommendations = []
        
        # Генерация на основе текущего состояния
        recommendations.extend(self._generate_current_state_recommendations(current_analysis))
        
        # Генерация на основе трендов
        recommendations.extend(self._generate_trend_based_recommendations(trend_analysis))
        
        # Генерация на основе отклонений
        recommendations.extend(self._generate_variance_based_recommendations(variance_analysis))
        
        # Использование GigaChat для advanced рекомендаций
        if self.use_gigachat:
            advanced_recommendations = self._generate_ai_recommendations(
                company_data, current_analysis, recommendations
            )
            recommendations.extend(advanced_recommendations)
        
        # Удаление дубликатов
        unique_recommendations = self._remove_duplicate_recommendations(recommendations)
        
        return unique_recommendations
    
    def _generate_current_state_recommendations(self, 
                                               current_analysis: Dict[str, Any]) -> List[AIRecommendation]:
        """Генерация рекомендаций на основе текущего состояния"""
        
        recommendations = []
        
        # Financial health recommendations
        financial_health = current_analysis["financial_health"]
        burn_rate = financial_health.get("burn_rate", 0)
        runway = financial_health.get("runway_months", 0)
        
        if burn_rate > 50000:  # Пример threshold
            rec = AIRecommendation(
                id=f"fin_health_{datetime.now().timestamp()}",
                category="financial_health",
                title="Высокий Burn Rate",
                description=f"Burn rate ${burn_rate:,.0f}/мес требует оптимизации",
                priority="high" if burn_rate > 100000 else "medium",
                confidence=0.8,
                action_items=[
                    "Провести детальный анализ расходов",
                    "Идентифицировать non-essential costs",
                    "Оптимизировать облачные расходы",
                    "Пересмотреть контракты с поставщиками"
                ],
                expected_impact="high",
                timeframe="short_term",
                metrics_affected=["burn_rate", "runway"],
                implementation_difficulty="medium",
                created_at=datetime.now(),
                data_sources=["financial_analysis"]
            )
            recommendations.append(rec)
        
        if runway < 12:
            rec = AIRecommendation(
                id=f"runway_{datetime.now().timestamp()}",
                category="fundraising",
                title="Короткий Runway",
                description=f"Runway {runway:.1f} месяцев требует внимания",
                priority="critical" if runway < 6 else "high" if runway < 9 else "medium",
                confidence=0.9,
                action_items=[
                    "Начать подготовку к fundraising",
                    "Обновить pitch deck",
                    "Составить список target investors",
                    "Подготовить financial projections"
                ],
                expected_impact="high",
                timeframe="immediate" if runway < 6 else "short_term",
                metrics_affected=["runway", "cash_balance"],
                implementation_difficulty="hard",
                created_at=datetime.now(),
                data_sources=["financial_analysis"]
            )
            recommendations.append(rec)
        
        # Unit economics recommendations
        unit_economics = current_analysis["unit_economics"]
        ltv_cac_ratio = unit_economics.get("ltv_cac_ratio", 0)
        
        if ltv_cac_ratio < 3.0 and ltv_cac_ratio > 0:
            rec = AIRecommendation(
                id=f"ltv_cac_{datetime.now().timestamp()}",
                category="unit_economics",
                title="Низкий LTV/CAC Ratio",
                description=f"LTV/CAC ratio {ltv_cac_ratio:.1f}x ниже оптимального",
                priority="high" if ltv_cac_ratio < 2.0 else "medium",
                confidence=0.7,
                action_items=[
                    "Улучшить customer retention",
                    "Оптимизировать маркетинговые каналы",
                    "Рассмотреть увеличение цен",
                    "Улучшить onboarding процесс"
                ],
                expected_impact="medium",
                timeframe="medium_term",
                metrics_affected=["ltv_cac_ratio", "cac", "ltv"],
                implementation_difficulty="hard",
                created_at=datetime.now(),
                data_sources=["unit_economics_analysis"]
            )
            recommendations.append(rec)
        
        return recommendations
    
    def _generate_trend_based_recommendations(self, 
                                             trend_analysis: Dict[str, Any]) -> List[AIRecommendation]:
        """Генерация рекомендаций на основе трендов"""
        
        recommendations = []
        
        # Revenue trend recommendations
        revenue_trend = trend_analysis.get("revenue_trend", {})
        revenue_direction = revenue_trend.get("direction", "flat")
        revenue_growth = revenue_trend.get("growth_rate", 0)
        
        if revenue_direction == "down" and revenue_growth < -0.1:
            rec = AIRecommendation(
                id=f"revenue_trend_{datetime.now().timestamp()}",
                category="growth",
                title="Снижение Выручки",
                description=f"Выручка снижается ({revenue_growth:.1%}/мес)",
                priority="high",
                confidence=0.75,
                action_items=[
                    "Анализировать причины снижения выручки",
                    "Усилить sales efforts",
                    "Запустить промо-кампании",
                    "Пересмотреть pricing strategy"
                ],
                expected_impact="high",
                timeframe="immediate",
                metrics_affected=["mrr", "revenue_growth"],
                implementation_difficulty="medium",
                created_at=datetime.now(),
                data_sources=["trend_analysis"]
            )
            recommendations.append(rec)
        
        # Burn rate trend recommendations
        burn_trend = trend_analysis.get("burn_rate_trend", {})
        burn_direction = burn_trend.get("direction", "flat")
        burn_trend_value = burn_trend.get("trend_value", 0)
        
        if burn_direction == "up" and burn_trend_value > 0.1:
            rec = AIRecommendation(
                id=f"burn_trend_{datetime.now().timestamp()}",
                category="financial_health",
                title="Рост Burn Rate",
                description=f"Burn rate растет ({burn_trend_value:.1%}/мес)",
                priority="medium",
                confidence=0.7,
                action_items=[
                    "Контролировать рост расходов",
                    "Внедрить бюджетные ограничения",
                    "Регулярно пересматривать расходы",
                    "Оптимизировать крупные статьи расходов"
                ],
                expected_impact="medium",
                timeframe="short_term",
                metrics_affected=["burn_rate", "runway"],
                implementation_difficulty="easy",
                created_at=datetime.now(),
                data_sources=["trend_analysis"]
            )
            recommendations.append(rec)
        
        return recommendations
    
    def _generate_variance_based_recommendations(self, 
                                                variance_analysis: Dict[str, Any]) -> List[AIRecommendation]:
        """Генерация рекомендаций на основе отклонений"""
        
        recommendations = []
        
        if not variance_analysis.get("has_variances", False):
            return recommendations
        
        # Рекомендации на основе значимых отклонений
        significant_count = variance_analysis.get("significant_variances_count", 0)
        if significant_count > 0:
            rec = AIRecommendation(
                id=f"variance_{datetime.now().timestamp()}",
                category="planning",
                title="Значимые Отклонения от Плана",
                description=f"Обнаружено {significant_count} значимых отклонений от плана",
                priority="medium",
                confidence=0.8,
                action_items=[
                    "Проанализировать причины отклонений",
                    "Корректировать assumptions планирования",
                    "Обновить financial plan",
                    "Улучшить accuracy прогнозов"
                ],
                expected_impact="medium",
                timeframe="short_term",
                metrics_affected=["plan_accuracy", "variance"],
                implementation_difficulty="medium",
                created_at=datetime.now(),
                data_sources=["variance_analysis"]
            )
            recommendations.append(rec)
        
        # Рекомендации на основе критических отклонений
        critical_variances = variance_analysis.get("critical_variances", [])
        if critical_variances:
            worst_metrics = [v.get("metric", "") for v in critical_variances[:3]]
            rec = AIRecommendation(
                id=f"critical_variance_{datetime.now().timestamp()}",
                category="operations",
                title="Критические Отклонения",
                description=f"Критические отклонения по метрикам: {', '.join(worst_metrics)}",
                priority="critical",
                confidence=0.9,
                action_items=[
                    "Немедленно рассмотреть критические отклонения",
                    "Принять corrective actions",
                    "Уведомить leadership team",
                    "Создать action plan"
                ],
                expected_impact="high",
                timeframe="immediate",
                metrics_affected=worst_metrics,
                implementation_difficulty="hard",
                created_at=datetime.now(),
                data_sources=["variance_analysis"]
            )
            recommendations.append(rec)
        
        return recommendations
    
    def _generate_ai_recommendations(self, company_data: Dict[str, Any],
                                    current_analysis: Dict[str, Any],
                                    existing_recommendations: List[AIRecommendation]) -> List[AIRecommendation]:
        """Генерация рекомендаций с использованием GigaChat"""
        
        if not self.analyst:
            return []
        
        try:
            # Подготавливаем данные для AI
            ai_input = {
                "company_data": {
                    "stage": company_data.get("stage", "pre_seed"),
                    "current_mrr": company_data.get("current_mrr", 0),
                    "current_customers": company_data.get("current_customers", 0),
                    "team_size": company_data.get("team_size", 1)
                },
                "current_analysis": current_analysis,
                "existing_recommendations": [
                    {
                        "title": r.title,
                        "category": r.category,
                        "priority": r.priority
                    }
                    for r in existing_recommendations[:5]  # Ограничиваем количество
                ]
            }
            
            # Формируем prompt для AI
            prompt = f"""
            Ты - финансовый аналитик для SaaS стартапа. Проанализируй данные компании и сгенерируй дополнительные рекомендации.
            
            Данные компании:
            - Стадия: {ai_input['company_data']['stage']}
            - MRR: ${ai_input['company_data']['current_mrr']:,.0f}
            - Клиенты: {ai_input['company_data']['current_customers']}
            - Размер команды: {ai_input['company_data']['team_size']}
            
            Текущий анализ:
            {json.dumps(ai_input['current_analysis'], indent=2, default=str)}
            
            Существующие рекомендации (первые 5):
            {json.dumps(ai_input['existing_recommendations'], indent=2)}
            
            Сгенерируй 3-5 дополнительных рекомендаций, которые:
            1. Не дублируют существующие
            2. Учитывают стадию компании
            3. Практически реализуемы
            4. Имеют измеримый impact
            
            Формат для каждой рекомендации:
            - Категория (financial_health, growth, unit_economics, fundraising, operations, team)
            - Название
            - Описание
            - Приоритет (low, medium, high, critical)
            - 3-4 конкретных action items
            - Ожидаемый impact (low, medium, high)
            - Timeframe (immediate, short_term, medium_term, long_term)
            - Метрики, которые улучшатся
            
            Ответ в формате JSON.
            """
            
            # Получаем ответ от AI
            response = self.analyst.analyze_data(prompt)
            
            # Парсим ответ
            if response and "recommendations" in response:
                ai_recommendations = []
                for rec_data in response["recommendations"]:
                    rec = AIRecommendation(
                        id=f"ai_{datetime.now().timestamp()}_{len(ai_recommendations)}",
                        category=rec_data.get("category", "general"),
                        title=rec_data.get("title", ""),
                        description=rec_data.get("description", ""),
                        priority=rec_data.get("priority", "medium"),
                        confidence=0.7,  # AI confidence
                        action_items=rec_data.get("action_items", []),
                        expected_impact=rec_data.get("expected_impact", "medium"),
                        timeframe=rec_data.get("timeframe", "medium_term"),
                        metrics_affected=rec_data.get("metrics_affected", []),
                        implementation_difficulty=rec_data.get("implementation_difficulty", "medium"),
                        created_at=datetime.now(),
                        data_sources=["ai_analysis", "gigachat"]
                    )
                    ai_recommendations.append(rec)
                
                return ai_recommendations
            
        except Exception as e:
            print(f"Error generating AI recommendations: {e}")
        
        return []
    
    def _remove_duplicate_recommendations(self, 
                                         recommendations: List[AIRecommendation]) -> List[AIRecommendation]:
        """Удаление дублирующихся рекомендаций"""
        
        unique_recommendations = []
        seen_titles = set()
        
        for rec in recommendations:
            # Простая дедупликация по названию
            if rec.title not in seen_titles:
                seen_titles.add(rec.title)
                unique_recommendations.append(rec)
        
        return unique_recommendations
    
    def _prioritize_recommendations(self, 
                                   recommendations: List[AIRecommendation]) -> List[AIRecommendation]:
        """Приоритизация рекомендаций"""
        
        if not recommendations:
            return []
        
        # Присваиваем вес каждой рекомендации
        prioritized = []
        
        for rec in recommendations:
            # Вес на основе priority
            priority_weights = {
                "critical": 100,
                "high": 80,
                "medium": 50,
                "low": 20
            }
            
            # Вес на основе expected impact
            impact_weights = {
                "high": 30,
                "medium": 20,
                "low": 10
            }
            
            # Вес на основе timeframe
            timeframe_weights = {
                "immediate": 40,
                "short_term": 30,
                "medium_term": 20,
                "long_term": 10
            }
            
            # Вес на основе confidence
            confidence_weight = rec.confidence * 20
            
            # Общий вес
            total_weight = (
                priority_weights.get(rec.priority, 0) +
                impact_weights.get(rec.expected_impact, 0) +
                timeframe_weights.get(rec.timeframe, 0) +
                confidence_weight
            )
            
            # Добавляем вес к рекомендации
            rec.weight = total_weight
            prioritized.append(rec)
        
        # Сортируем по весу
        prioritized.sort(key=lambda x: x.weight, reverse=True)
        
        return prioritized
    
    def _create_action_plan(self, 
                           prioritized_recommendations: List[AIRecommendation]) -> Dict[str, Any]:
        """Создание action plan на основе рекомендаций"""
        
        action_plan = {
            "immediate_actions": [],
            "short_term_actions": [],
            "medium_term_actions": [],
            "long_term_actions": []
        }
        
        # Группируем рекомендации по timeframe
        for rec in prioritized_recommendations:
            action_items = []
            
            for i, action in enumerate(rec.action_items, 1):
                action_items.append({
                    "id": f"{rec.id}_action_{i}",
                    "description": action,
                    "recommendation_title": rec.title,
                    "priority": rec.priority,
                    "estimated_effort": self._estimate_effort(rec.implementation_difficulty)
                })
            
            # Добавляем в соответствующий timeframe
            if rec.timeframe == "immediate":
                action_plan["immediate_actions"].extend(action_items)
            elif rec.timeframe == "short_term":
                action_plan["short_term_actions"].extend(action_items)
            elif rec.timeframe == "medium_term":
                action_plan["medium_term_actions"].extend(action_items)
            else:  # long_term
                action_plan["long_term_actions"].extend(action_items)
        
        # Ограничиваем количество действий в каждом timeframe
        for timeframe in action_plan:
            action_plan[timeframe] = action_plan[timeframe][:5]  # Максимум 5 действий
        
        return action_plan
    
    def _estimate_effort(self, difficulty: str) -> str:
        """Оценка effort для действия"""
        
        effort_map = {
            "easy": "1-2 дня",
            "medium": "1-2 недели",
            "hard": "1-2 месяца"
        }
        
        return effort_map.get(difficulty, "1-2 недели")
    
    def _extract_key_insights(self, current_analysis: Dict[str, Any],
                             trend_analysis: Dict[str, Any],
                             recommendations: List[AIRecommendation]) -> List[Dict[str, Any]]:
        """Извлечение ключевых инсайтов"""
        
        insights = []
        
        # Financial health insight
        financial_health = current_analysis["financial_health"]
        if financial_health["status"] in ["critical", "emergency"]:
            insights.append({
                "type": "financial_crisis",
                "title": "Финансовый Кризис",
                "description": financial_health["description"],
                "severity": "critical",
                "recommendation": "Немедленно принять меры по улучшению финансового положения"
            })
        
        # Growth insight
        growth_metrics = current_analysis["growth_metrics"]
        if growth_metrics.get("growth_rate", 0) < 0.05:
            insights.append({
                "type": "growth_stagnation",
                "title": "Стагнация Роста",
                "description": f"Рост выручки всего {growth_metrics['growth_rate']:.1%}/мес",
                "severity": "medium",
                "recommendation": "Активизировать growth initiatives"
            })
        
        # Unit economics insight
        unit_economics = current_analysis["unit_economics"]
        if unit_economics.get("ltv_cac_ratio", 0) < 3.0:
            insights.append({
                "type": "poor_unit_economics",
                "title": "Слабые Unit Economics",
                "description": f"LTV/CAC ratio {unit_economics['ltv_cac_ratio']:.1f}x ниже оптимального",
                "severity": "high",
                "recommendation": "Фокусироваться на улучшении unit economics перед масштабированием"
            })
        
        # Top recommendation insight
        if recommendations:
            top_rec = recommendations[0]
            insights.append({
                "type": "top_recommendation",
                "title": "Главная Рекомендация",
                "description": f"{top_rec.title}: {top_rec.description}",
                "severity": top_rec.priority,
                "recommendation": f"Начать с: {top_rec.action_items[0] if top_rec.action_items else 'Нет действий'}"
            })
        
        return insights
    
    def get_recommendation_by_category(self, company_id: int, 
                                      category: str) -> List[AIRecommendation]:
        """Получение рекомендаций по категории"""
        
        # Проверяем кэш
        cache_key = f"{company_id}_{category}"
        if cache_key in self.recommendations_cache:
            cached = self.recommendations_cache[cache_key]
            if (datetime.now() - cached["timestamp"]).days < 1:  # Кэш на 1 день
                return cached["recommendations"]
        
        # Если нет в кэше, генерируем новые
        analysis_result = self.analyze_company(company_id)
        
        if not analysis_result["success"]:
            return []
        
        recommendations = analysis_result["recommendations"]
        
        # Фильтруем по категории
        category_recommendations = [
            rec for rec in recommendations 
            if rec.category == category or category == "all"
        ]
        
        # Сохраняем в кэш
        self.recommendations_cache[cache_key] = {
            "recommendations": category_recommendations,
            "timestamp": datetime.now()
        }
        
        return category_recommendations
    
    def track_recommendation_implementation(self, recommendation_id: str,
                                           status: str, 
                                           notes: str = "") -> Dict[str, Any]:
        """Отслеживание реализации рекомендации"""
        
        # Здесь будет интеграция с системой отслеживания задач
        # Пока возвращаем mock ответ
        
        return {
            "success": True,
            "recommendation_id": recommendation_id,
            "status": status,
            "updated_at": datetime.now().isoformat(),
            "notes": notes,
            "next_review_date": (datetime.now() + timedelta(days=7)).isoformat()
        }
    def generate_mock_recommendation(self) -> AIRecommendation:
        """Создание mock-рекомендации для тестирования"""
        return AIRecommendation(
            id="mock_001",
            category="financial_health",
            title="Mock Recommendation for Testing",
            description="This is a mock recommendation for application testing",
            priority="medium",
            confidence=0.8,
            action_items=["Test action 1", "Test action 2", "Test action 3"],
            expected_impact="medium",
            timeframe="short_term",
            metrics_affected=["CAC", "LTV"],
            implementation_difficulty="medium",
            created_at=datetime.now(),
            data_sources=["mock_data"]
        )

# Создаем глобальный экземпляр движка рекомендаций
ai_recommendation_engine = AIRecommendationEngine()

# Экспортируем полезные функции
def get_ai_recommendations(company_id: int) -> Dict[str, Any]:
    """Публичная функция для получения AI рекомендаций"""
    return ai_recommendation_engine.analyze_company(company_id)

def get_recommendations_by_category(company_id: int, category: str) -> List[Dict[str, Any]]:
    """Публичная функция для получения рекомендаций по категории"""
    recommendations = ai_recommendation_engine.get_recommendation_by_category(company_id, category)
    
    # Конвертация в dict
    return [
        {
            "id": rec.id,
            "category": rec.category,
            "title": rec.title,
            "description": rec.description,
            "priority": rec.priority,
            "confidence": rec.confidence,
            "action_items": rec.action_items,
            "expected_impact": rec.expected_impact,
            "timeframe": rec.timeframe,
            "metrics_affected": rec.metrics_affected,
            "implementation_difficulty": rec.implementation_difficulty,
            "created_at": rec.created_at.isoformat(),
            "data_sources": rec.data_sources
        }
        for rec in recommendations
    ]