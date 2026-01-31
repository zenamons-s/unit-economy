"""
Советник для Pre-Seed SaaS стартапов
Предоставляет экспертные рекомендации для ранних стадий
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Mapping, Optional, Tuple, Union

from database.db_manager import db_manager
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class PreSeedChallenge:
    """Вызов, с которым сталкивается Pre-Seed стартап"""
    name: str
    category: str  # product, market, team, funding, growth
    severity: str  # critical, high, medium, low
    description: str
    symptoms: List[str]
    solutions: List[str]
    success_metrics: List[str]
    timeframe: str  # immediate, short_term, medium_term

class PreSeedAdvisor:
    """
    Советник для Pre-Seed SaaS стартапов
    Основан на паттернах успешных стартапов и распространенных ошибках
    """
    
    def __init__(self):
        self.challenges = self._load_challenges()
        self.patterns = self._load_success_patterns()
        self.common_mistakes = self._load_common_mistakes()

    def get_company_data(self, company_id: int) -> Dict[str, Any]:
        """Получение данных компании из базы данных по ID."""
        return self._load_company_data(company_id)

    def _resolve_company_data(
        self, company_data: Union[int, Mapping[str, Any]]
    ) -> Dict[str, Any]:
        """Приведение входных данных к словарю с данными компании."""
        if isinstance(company_data, int):
            return self._load_company_data(company_data)
        if isinstance(company_data, Mapping):
            return dict(company_data)
        logger.warning("Неожиданный тип company_data: %s", type(company_data))
        return {"name": "Unnamed Company", "stage": "pre_seed"}

    def _load_company_data(self, company_id: int) -> Dict[str, Any]:
        """Загрузка данных компании из БД и нормализация."""
        company = db_manager.get_company(company_id)
        if not company:
            logger.warning("Компания с id=%s не найдена.", company_id)
            return {"id": company_id, "name": "Unnamed Company", "stage": "pre_seed"}
        company_dict = company.to_dict()
        if not company_dict.get("name"):
            company_dict["name"] = "Unnamed Company"
        if not company_dict.get("stage"):
            company_dict["stage"] = "pre_seed"
        return company_dict
    
    def _load_challenges(self) -> List[PreSeedChallenge]:
        """Загрузка типичных вызовов для Pre-Seed"""
        
        return [
            PreSeedChallenge(
                name="Отсутствие Product-Market Fit",
                category="product",
                severity="critical",
                description="Продукт не решает реальную проблему для достаточного количества клиентов",
                symptoms=[
                    "Низкий уровень удержания пользователей",
                    "Медленный рост без платных маркетинговых каналов",
                    "Клиенты не готовы платить за продукт",
                    "Низкая частота использования продукта"
                ],
                solutions=[
                    "Провести 50+ интервью с потенциальными клиентами",
                    "Создать MVP, решающий одну ключевую проблему",
                    "Использовать подход Jobs-to-be-Done",
                    "Тестировать разные гипотезы ценностного предложения"
                ],
                success_metrics=[
                    "NPS > 30",
                    "Месячный retention > 40%",
                    "Более 3 активных пользователей на аккаунт",
                    "Сарафанный рост > 20% новых пользователей"
                ],
                timeframe="short_term"
            ),
            
            PreSeedChallenge(
                name="Недостаточный Runway",
                category="funding",
                severity="critical",
                description="Недостаточно денег для достижения следующих ключевых метрик",
                symptoms=[
                    "Runway < 6 месяцев",
                    "Невозможность нанять ключевых сотрудников",
                    "Постоянный стресс из-за финансов",
                    "Отсутствие бюджета на эксперименты"
                ],
                solutions=[
                    "Сократить burn rate на 20-30%",
                    "Фокусироваться только на revenue-generating активностях",
                    "Найти angel инвесторов или бизнес-ангелов",
                    "Рассмотреть revenue-based financing",
                    "Применить бережливый подход к разработке"
                ],
                success_metrics=[
                    "Runway > 12 месяцев",
                    "Burn rate < 1.5x MRR",
                    "Месячный рост MRR > 20%",
                    "Наличие 3+ месяцев emergency fund"
                ],
                timeframe="immediate"
            ),
            
            PreSeedChallenge(
                name="Высокий CAC",
                category="growth",
                severity="high",
                description="Стоимость привлечения клиента слишком высока для бизнес-модели",
                symptoms=[
                    "CAC > LTV/3",
                    "CAC payback > 12 месяцев",
                    "Ограниченный рост из-за стоимости привлечения",
                    "Низкая рентабельность на клиенте"
                ],
                solutions=[
                    "Фокусироваться на organic каналах роста",
                    "Запустить реферальную программу",
                    "Оптимизировать воронку конверсии",
                    "Тестировать разные ценовые стратегии",
                    "Улучшить onboarding процесс"
                ],
                success_metrics=[
                    "CAC payback < 9 месяцев",
                    "LTV/CAC > 3",
                    "Organic трафик > 30% от общего",
                    "Конверсия сайта > 3%"
                ],
                timeframe="medium_term"
            ),
            
            PreSeedChallenge(
                name="Проблемы с командой",
                category="team",
                severity="high",
                description="Нехватка нужных компетенций или проблемы в команде",
                symptoms=[
                    "Медленная скорость разработки",
                    "Высокий turnover",
                    "Конфликты в команде",
                    "Отсутствие ключевых ролей"
                ],
                solutions=[
                    "Нанять технического сооснователя",
                    "Аутсорсить non-core функции",
                    "Внедрить agile процессы",
                    "Определить четкие роли и ответственности",
                    "Создать сильную культуру"
                ],
                success_metrics=[
                    "Скорость разработки features > 2 в месяц",
                    "Employee NPS > 40",
                    "Наличие всех ключевых ролей",
                    "Низкий уровень конфликтов"
                ],
                timeframe="medium_term"
            ),
            
            PreSeedChallenge(
                name="Слабые Unit Economics",
                category="market",
                severity="high",
                description="Бизнес-модель не масштабируется из-за плохих unit economics",
                symptoms=[
                    "Отрицательная валовая маржа",
                    "Высокие переменные затраты",
                    "Низкая пожизненная ценность клиента",
                    "Неспособность к масштабированию"
                ],
                solutions=[
                    "Увеличить цены на 20-50%",
                    "Снизить переменные затраты",
                    "Улучшить удержание клиентов",
                    "Добавить дополнительные потоки выручки",
                    "Оптимизировать инфраструктурные затраты"
                ],
                success_metrics=[
                    "Валовая маржа > 70%",
                    "LTV > 3x CAC",
                    "Net Revenue Retention > 100%",
                    "Переменные затраты < 30% от выручки"
                ],
                timeframe="medium_term"
            )
        ]
    
    def _load_success_patterns(self) -> List[Dict[str, Any]]:
        """Загрузка паттернов успешных SaaS стартапов"""
        
        return [
            {
                "name": "Product-Led Growth (PLG)",
                "description": "Рост через продукт, а не через продажи",
                "key_characteristics": [
                    "Freemium или free trial модель",
                    "Самостоятельный onboarding",
                    "Вирусные механики в продукте",
                    "Data-driven улучшение продукта"
                ],
                "best_for": [
                    "B2B SaaS с низким ACV (<$10k)",
                    "Продукты с низким порогом входа",
                    "Рынки с высокой конкуренцией",
                    "Глобальные рынки"
                ],
                "key_metrics": [
                    "Free to paid conversion > 5%",
                    "Virality coefficient > 0.5",
                    "Time to value < 1 день",
                    "Product qualified leads > 50%"
                ],
                "examples": ["Slack", "Notion", "Figma", "Zoom"]
            },
            
            {
                "name": "Sales-Led Growth (SLG)",
                "description": "Рост через прямые продажи",
                "key_characteristics": [
                    "Высокий ACV (>$20k)",
                    "Длинный цикл продаж",
                    "Enterprise клиенты",
                    "Комплексные решения"
                ],
                "best_for": [
                    "B2B SaaS с высоким ACV",
                    "Решения для enterprise",
                    "Сложные продукты",
                    "Нишевые рынки"
                ],
                "key_metrics": [
                    "Sales cycle < 90 дней",
                    "Win rate > 25%",
                    "ACV > $20k",
                    "Quota attainment > 80%"
                ],
                "examples": ["Salesforce", "HubSpot", "Workday", "ServiceNow"]
            },
            
            {
                "name": "Marketplace-Led Growth",
                "description": "Рост через создание рынка/платформы",
                "key_characteristics": [
                    "Двусторонняя платформа",
                    "Сетевой эффект",
                    "Транзакционная модель",
                    "Комиссия с транзакций"
                ],
                "best_for": [
                    "Рынки с fragmentation",
                    "Сервисы по требованию",
                    "Платформы для фрилансеров",
                    "B2B маркетплейсы"
                ],
                "key_metrics": [
                    "Take rate > 10%",
                    "Liquidity > 70%",
                    "Network effects коэффициент > 1",
                    "GMV growth > 30% monthly"
                ],
                "examples": ["Upwork", "Fiverr", "Amazon AWS Marketplace"]
            },
            
            {
                "name": "Content-Led Growth",
                "description": "Рост через создание ценного контента",
                "key_characteristics": [
                    "Сильный бренд через контент",
                    "Organic трафик как основной канал",
                    "Комьюнити вокруг продукта",
                    "Thought leadership"
                ],
                "best_for": [
                    "Сложные продукты, требующие обучения",
                    "Рынки с high intent трафиком",
                    "Продукты для креаторов",
                    "B2B SaaS с длинным циклом принятия решения"
                ],
                "key_metrics": [
                    "Organic трафик > 50% от общего",
                    "Content conversion rate > 2%",
                    "Email list growth > 10% monthly",
                    "Brand search volume growth > 20%"
                ],
                "examples": ["HubSpot", "Ahrefs", "Buffer", "Intercom"]
            }
        ]
    
    def _load_common_mistakes(self) -> List[Dict[str, Any]]:
        """Загрузка распространенных ошибок Pre-Seed стартапов"""
        
        return [
            {
                "mistake": "Слишком ранний найм продавцов",
                "description": "Нанять sales team до достижения product-market fit",
                "impact": "Высокий burn rate без результатов, demotivated team",
                "solution": "Сначала достичь PMF, founders должны делать первые продажи",
                "timing": "Нанимать продавцов только после 10+ платных клиентов и clear sales playbook"
            },
            
            {
                "mistake": "Сложный продукт",
                "description": "Создание продукта со слишком большим количеством функций",
                "impact": "Долгая разработка, сложный onboarding, confused customers",
                "solution": "Начать с одного killer feature, который решает одну проблему",
                "timing": "MVP должен быть запущен за 3-6 месяцев"
            },
            
            {
                "mistake": "Неправильный pricing",
                "description": "Слишком низкие цены или сложная pricing структура",
                "impact": "Оставить деньги на столе или отпугнуть клиентов",
                "solution": "Тестировать разные pricing модели, начинать с value-based pricing",
                "timing": "Пересматривать pricing каждые 6 месяцев"
            },
            
            {
                "mistake": "Игнорирование retention",
                "description": "Фокус только на acquisition, а не на retention",
                "impact": "High churn, низкий LTV, невозможность масштабирования",
                "solution": "С первого дня измерять retention, инвестировать в customer success",
                "timing": "Начинать работать над retention с первого клиента"
            },
            
            {
                "mistake": "Отсутствие финансового планирования",
                "description": "Не отслеживать burn rate, runway и unit economics",
                "impact": "Внезапное окончание денег, паника, плохие решения",
                "solution": "Внедрить ежемесячный финансовый контроль, планировать на 12+ месяцев",
                "timing": "Начинать финансовое планирование с первого дня"
            }
        ]
    
    def analyze_company(self, company_data: Union[int, Mapping[str, Any]]) -> Dict[str, Any]:
        """Анализ компании и выявление проблем"""

        company_data = self._resolve_company_data(company_data)

        analysis = {
            "company_name": company_data.get("name", "Unnamed Company"),
            "stage": company_data.get("stage", "pre_seed"),
            "analysis_date": datetime.now().isoformat(),
            "identified_challenges": [],
            "recommended_patterns": [],
            "common_mistakes_detected": [],
            "action_plan": [],
            "risk_assessment": {}
        }
        
        # Анализируем метрики компании
        metrics = company_data.get("metrics", {})
        
        # Выявляем вызовы на основе метрик
        analysis["identified_challenges"] = self._identify_challenges(metrics, company_data)
        
        # Рекомендуем подходящие паттерны роста
        analysis["recommended_patterns"] = self._recommend_patterns(company_data)
        
        # Проверяем на распространенные ошибки
        analysis["common_mistakes_detected"] = self._detect_mistakes(company_data)
        
        # Создаем план действий
        analysis["action_plan"] = self._create_action_plan(
            analysis["identified_challenges"],
            analysis["recommended_patterns"]
        )
        
        # Оценка рисков
        analysis["risk_assessment"] = self._assess_risks(analysis)
        
        return analysis
    
    def _identify_challenges(self, metrics: Dict[str, float], company_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Идентификация вызовов на основе метрик компании"""
        
        identified = []
        
        # Проверяем каждый вызов
        for challenge in self.challenges:
            if self._is_challenge_relevant(challenge, metrics, company_data):
                identified.append({
                    "name": challenge.name,
                    "category": challenge.category,
                    "severity": challenge.severity,
                    "description": challenge.description,
                    "solutions": challenge.solutions,
                    "timeframe": challenge.timeframe
                })
        
        # Сортируем по серьезности
        severity_order = {"critical": 1, "high": 2, "medium": 3, "low": 4}
        identified.sort(key=lambda x: severity_order.get(x["severity"], 5))
        
        return identified
    
    def _is_challenge_relevant(self, challenge: PreSeedChallenge, 
                             metrics: Dict[str, float], 
                             company_data: Dict[str, Any]) -> bool:
        """Проверка, актуален ли вызов для компании"""
        
        # Проверяем по метрикам
        if challenge.name == "Отсутствие Product-Market Fit":
            # Проверяем метрики PMF
            mrr_growth = metrics.get("mrr_growth_monthly", 0)
            churn_rate = metrics.get("monthly_churn_rate", 0.1)
            nrr = metrics.get("net_revenue_retention", 0.9)
            
            return (mrr_growth < 0.15 or churn_rate > 0.1 or nrr < 1.0)
        
        elif challenge.name == "Недостаточный Runway":
            runway = metrics.get("runway_months", 0)
            burn_rate = company_data.get("burn_rate", 0)
            cash_balance = company_data.get("cash_balance", 0)
            
            return (runway < 6 or cash_balance < burn_rate * 6)
        
        elif challenge.name == "Высокий CAC":
            cac = metrics.get("cac", 0)
            cac_payback = metrics.get("cac_payback_months", 0)
            ltv_cac = metrics.get("ltv_cac_ratio", 0)
            
            return (cac_payback > 12 or ltv_cac < 3)
        
        elif challenge.name == "Проблемы с командой":
            team_size = company_data.get("team_size", 1)
            has_tech_cofounder = company_data.get("has_tech_cofounder", False)
            
            return (team_size > 3 and not has_tech_cofounder)
        
        elif challenge.name == "Слабые Unit Economics":
            gross_margin = metrics.get("gross_margin", 0)
            variable_costs_ratio = metrics.get("variable_costs_ratio", 0.5)
            
            return (gross_margin < 0.7 or variable_costs_ratio > 0.4)
        
        return False
    
    def _recommend_patterns(self, company_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Рекомендация паттернов роста на основе характеристик компании"""
        
        recommendations = []
        avg_revenue_per_customer = company_data.get("avg_revenue_per_customer", 0)
        product_complexity = company_data.get("product_complexity", "medium")
        market_type = company_data.get("market_type", "b2b")
        
        for pattern in self.patterns:
            score = self._calculate_pattern_fit_score(pattern, company_data)
            
            if score >= 0.6:  # 60% совпадение или выше
                recommendations.append({
                    "name": pattern["name"],
                    "description": pattern["description"],
                    "fit_score": round(score * 100, 1),
                    "key_characteristics": pattern["key_characteristics"],
                    "key_metrics": pattern["key_metrics"],
                    "reason": self._get_pattern_recommendation_reason(pattern, company_data)
                })
        
        # Сортируем по score
        recommendations.sort(key=lambda x: x["fit_score"], reverse=True)
        
        return recommendations[:2]  # Возвращаем топ-2 рекомендации
    
    def _calculate_pattern_fit_score(self, pattern: Dict[str, Any], 
                                   company_data: Dict[str, Any]) -> float:
        """Расчет score совпадения паттерна с компанией"""
        
        score = 0
        total_weights = 0
        
        # Проверяем best_for условия
        avg_revenue = company_data.get("avg_revenue_per_customer", 0)
        market_type = company_data.get("market_type", "b2b")
        product_type = company_data.get("product_type", "software")
        
        for condition in pattern.get("best_for", []):
            if self._check_condition(condition, avg_revenue, market_type, product_type):
                score += 1
                total_weights += 1
        
        # Нормализуем score
        if total_weights > 0:
            return score / total_weights
        return 0
    
    def _check_condition(self, condition: str, avg_revenue: float, 
                        market_type: str, product_type: str) -> bool:
        """Проверка условия паттерна"""
        
        condition_lower = condition.lower()
        
        if "b2b" in condition_lower and market_type != "b2b":
            return False
        
        if "acv" in condition_lower:
            if "<$10k" in condition_lower and avg_revenue > 10000:
                return False
            if ">$20k" in condition_lower and avg_revenue < 20000:
                return False
        
        return True
    
    def _get_pattern_recommendation_reason(self, pattern: Dict[str, Any], 
                                         company_data: Dict[str, Any]) -> str:
        """Получение причины рекомендации паттерна"""
        
        reasons = {
            "Product-Led Growth (PLG)": "Ваш продукт имеет низкий порог входа и может использоваться самостоятельно",
            "Sales-Led Growth (SLG)": "Ваш продукт требует объяснения ценности и имеет высокий ACV",
            "Marketplace-Led Growth": "Вы создаете платформу для соединения двух сторон рынка",
            "Content-Led Growth": "Ваш рынок требует обучения и у вас есть экспертиза для создания контента"
        }
        
        return reasons.get(pattern["name"], "Подходит под характеристики вашего бизнеса")
    
    def _detect_mistakes(self, company_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Выявление распространенных ошибок"""
        
        detected = []
        
        for mistake in self.common_mistakes:
            if self._is_mistake_present(mistake, company_data):
                detected.append({
                    "mistake": mistake["mistake"],
                    "description": mistake["description"],
                    "impact": mistake["impact"],
                    "solution": mistake["solution"],
                    "timing": mistake["timing"]
                })
        
        return detected
    
    def _is_mistake_present(self, mistake: Dict[str, Any], 
                           company_data: Dict[str, Any]) -> bool:
        """Проверка наличия ошибки"""
        
        mistake_name = mistake["mistake"]
        
        if mistake_name == "Слишком ранний найм продавцов":
            team_size = company_data.get("team_size", 0)
            sales_team_size = company_data.get("sales_team_size", 0)
            paying_customers = company_data.get("paying_customers", 0)
            
            return (sales_team_size > 0 and paying_customers < 10)
        
        elif mistake_name == "Сложный продукт":
            time_to_mvp = company_data.get("time_to_mvp_months", 0)
            feature_count = company_data.get("feature_count", 0)
            
            return (time_to_mvp > 6 or feature_count > 10)
        
        elif mistake_name == "Отсутствие финансового планирования":
            has_financial_plan = company_data.get("has_financial_plan", False)
            tracks_metrics = company_data.get("tracks_metrics", False)
            
            return (not has_financial_plan or not tracks_metrics)
        
        return False
    
    def _create_action_plan(self, challenges: List[Dict[str, Any]], 
                           patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Создание плана действий"""
        
        action_plan = []
        
        # Добавляем действия для критических вызовов
        critical_challenges = [c for c in challenges if c["severity"] == "critical"]
        
        for challenge in critical_challenges[:2]:  # Берем 2 самых критичных
            for solution in challenge["solutions"][:2]:  # Берем 2 первых решения
                action_plan.append({
                    "action": solution,
                    "category": challenge["category"],
                    "priority": "critical",
                    "timeframe": challenge["timeframe"],
                    "expected_outcome": f"Решить вызов: {challenge['name']}",
                    "success_metrics": ["Улучшение ключевых метрик по вызову"]
                })
        
        # Добавляем действия по рекомендованным паттернам
        if patterns:
            pattern = patterns[0]  # Берем лучший паттерн
            for characteristic in pattern["key_characteristics"][:2]:
                action_plan.append({
                    "action": f"Внедрить: {characteristic}",
                    "category": "growth_strategy",
                    "priority": "high",
                    "timeframe": "medium_term",
                    "expected_outcome": f"Реализовать паттерн {pattern['name']}",
                    "success_metrics": pattern["key_metrics"][:2]
                })
        
        # Добавляем общие best practices
        general_actions = [
            {
                "action": "Еженедельный обзор метрик",
                "category": "operations",
                "priority": "high",
                "timeframe": "immediate",
                "expected_outcome": "Быстрое реагирование на проблемы",
                "success_metrics": ["Время реакции на проблемы < 7 дней"]
            },
            {
                "action": "Ежемесячное планирование на 90 дней",
                "category": "planning",
                "priority": "medium",
                "timeframe": "immediate",
                "expected_outcome": "Четкие цели и приоритеты",
                "success_metrics": ["Выполнение квартальных целей > 70%"]
            }
        ]
        
        action_plan.extend(general_actions)
        
        return action_plan
    
    def _assess_risks(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Оценка рисков компании"""
        
        risks = {
            "survival_risk": "low",
            "growth_risk": "medium",
            "team_risk": "low",
            "market_risk": "medium",
            "financial_risk": "low",
            "overall_risk": "medium",
            "risk_factors": [],
            "mitigation_strategies": []
        }
        
        # Анализируем вызовы для определения рисков
        critical_challenges = len([c for c in analysis["identified_challenges"] 
                                 if c["severity"] == "critical"])
        high_challenges = len([c for c in analysis["identified_challenges"] 
                             if c["severity"] == "high"])
        
        if critical_challenges >= 2:
            risks["survival_risk"] = "high"
            risks["overall_risk"] = "high"
            risks["risk_factors"].append("Множество критических вызовов")
            risks["mitigation_strategies"].append(
                "Сфокусироваться на 1-2 самых критичных проблемах, сократить расходы"
            )
        
        if high_challenges >= 3:
            risks["growth_risk"] = "high"
            risks["risk_factors"].append("Много высокоприоритетных вызовов")
            risks["mitigation_strategies"].append(
                "Приоритизировать решения, создать phase-based roadmap"
            )
        
        # Добавляем общие mitigation strategies
        if risks["overall_risk"] in ["high", "medium"]:
            risks["mitigation_strategies"].extend([
                "Создать emergency plan на случай cash flow проблем",
                "Диверсифицировать каналы привлечения клиентов",
                "Построить strong advisory board",
                "Регулярно тестировать business assumptions"
            ])
        
        return risks
    
    def generate_quarterly_plan(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Генерация квартального плана для Pre-Seed стартапа"""
        
        # Определяем текущий квартал
        current_date = datetime.now()
        quarter = (current_date.month - 1) // 3 + 1
        year = current_date.year
        
        # Базовые цели для Pre-Seed
        base_objectives = {
            "q1": ["Достичь первых 10 платных клиентов", "Запустить MVP", "Определить ICP"],
            "q2": ["Достичь $10k ARR", "Улучшить product-market fit", "Оптимизировать onboarding"],
            "q3": ["Достичь $25k ARR", "Найти repeatable sales motion", "Улучшить retention"],
            "q4": ["Достичь $50k ARR", "Подготовиться к Seed раунду", "Построить scalable processes"]
        }
        
        # Адаптируем цели под компанию
        current_arr = company_data.get("current_arr", 0)
        paying_customers = company_data.get("paying_customers", 0)
        
        if current_arr < 10000:
            quarter_goals = base_objectives["q1"]
        elif current_arr < 25000:
            quarter_goals = base_objectives["q2"]
        elif current_arr < 50000:
            quarter_goals = base_objectives["q3"]
        else:
            quarter_goals = base_objectives["q4"]
        
        # Создаем детальный план
        quarterly_plan = {
            "quarter": f"Q{quarter} {year}",
            "timeframe": {
                "start": f"{year}-{(quarter-1)*3+1:02d}-01",
                "end": f"{year}-{quarter*3:02d}-31"
            },
            "objectives": quarter_goals,
            "key_results": self._generate_key_results(quarter_goals, company_data),
            "initiatives": self._generate_initiatives(quarter_goals),
            "success_criteria": [
                f"Достичь {len(quarter_goals)} из {len(quarter_goals)} целей",
                "Улучшить ключевые метрики на 20%",
                "Получить позитивный feedback от 5+ клиентов"
            ],
            "risks": [
                "Нехватка ресурсов для выполнения плана",
                "Изменения на рынке",
                "Проблемы с продуктом",
                "Конкурентное давление"
            ],
            "mitigations": [
                "Регулярный review прогресса",
                "Гибкое планирование",
                "Быстрое тестирование гипотез",
                "Фокус на differentiation"
            ]
        }
        
        return quarterly_plan
    
    def _generate_key_results(self, objectives: List[str], 
                            company_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Генерация ключевых результатов для целей"""
        
        key_results = []
        
        for objective in objectives:
            if "платных клиентов" in objective:
                current_customers = company_data.get("paying_customers", 0)
                target = current_customers * 2 if current_customers > 0 else 10
                
                key_results.append({
                    "objective": objective,
                    "metric": "Количество платных клиентов",
                    "current": current_customers,
                    "target": target,
                    "unit": "клиентов"
                })
            
            elif "ARR" in objective:
                current_arr = company_data.get("current_arr", 0)
                # Цель: увеличить ARR в 2-3 раза за квартал
                target = current_arr * 2.5 if current_arr > 0 else 10000
                
                key_results.append({
                    "objective": objective,
                    "metric": "Annual Recurring Revenue",
                    "current": current_arr,
                    "target": target,
                    "unit": "USD"
                })
            
            elif "product-market fit" in objective.lower():
                key_results.append({
                    "objective": objective,
                    "metric": "Product-Market Fit Score",
                    "current": 0,
                    "target": 40,
                    "unit": "score (0-100)"
                })
        
        return key_results
    
    def _generate_initiatives(self, objectives: List[str]) -> List[Dict[str, Any]]:
        """Генерация инициатив для достижения целей"""
        
        initiatives = []
        initiative_counter = 1
        
        for objective in objectives:
            if "клиентов" in objective:
                initiatives.append({
                    "id": f"I{initiative_counter}",
                    "name": "Acquisition Program",
                    "objective": objective,
                    "description": "Запуск программы привлечения первых клиентов",
                    "activities": [
                        "Cold outreach к 100 потенциальным клиентам",
                        "Участие в 3 industry events",
                        "Запуск referral программы",
                        "Контент-маркетинг: 4 статьи в месяц"
                    ],
                    "owner": "Founder/CEO",
                    "timeline": "6-8 недель",
                    "budget": "$2,000 - $5,000",
                    "success_metrics": ["Cost per acquisition < $500", "Conversion rate > 2%"]
                })
                initiative_counter += 1
            
            elif "MVP" in objective:
                initiatives.append({
                    "id": f"I{initiative_counter}",
                    "name": "MVP Development",
                    "objective": objective,
                    "description": "Разработка и запуск минимально жизнеспособного продукта",
                    "activities": [
                        "User research с 20+ потенциальными клиентами",
                        "Прототипирование key workflows",
                        "Разработка core features",
                        "Beta тестирование с 5 компаниями"
                    ],
                    "owner": "CTO/Lead Developer",
                    "timeline": "8-12 недель",
                    "budget": "$10,000 - $20,000",
                    "success_metrics": ["Time to MVP < 12 недель", "User satisfaction > 7/10"]
                })
                initiative_counter += 1
        
        return initiatives
    
    def get_funding_readiness_assessment(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Оценка готовности к следующему раунду финансирования"""
        
        # Критерии для Seed раунда
        seed_criteria = {
            "metrics": {
                "mrr": {"target": 25000, "weight": 0.3},
                "growth_rate": {"target": 0.2, "weight": 0.25},
                "gross_margin": {"target": 0.7, "weight": 0.15},
                "ltv_cac": {"target": 3.0, "weight": 0.2},
                "runway": {"target": 6, "weight": 0.1}
            },
            "team": {
                "has_technical_cofounder": True,
                "team_size": 3,
                "key_roles_filled": ["CEO", "CTO", "Product"]
            },
            "product": {
                "has_pmf": True,
                "customer_feedback_positive": True,
                "scalable_architecture": True
            },
            "market": {
                "tam": 1000000000,  # $1B
                "competitive_advantage": True,
                "growth_potential": True
            }
        }
        
        # Оцениваем текущее состояние
        readiness_score = 0
        max_score = 0
        gaps = []
        strengths = []
        
        # Оцениваем метрики
        metrics = company_data.get("metrics", {})
        for metric_name, criteria in seed_criteria["metrics"].items():
            max_score += criteria["weight"] * 100
            current_value = metrics.get(metric_name, 0)
            target = criteria["target"]
            
            if current_value >= target:
                readiness_score += criteria["weight"] * 100
                strengths.append(f"Метрика {metric_name} выше целевой: {current_value} >= {target}")
            else:
                gap = target - current_value
                gap_percentage = (gap / target) * 100 if target > 0 else 100
                readiness_score += criteria["weight"] * max(0, 100 - gap_percentage)
                gaps.append(f"Метрика {metric_name} ниже целевой: {current_value} < {target} (gap: {gap_percentage:.1f}%)")
        
        # Рассчитываем общий readiness score
        if max_score > 0:
            readiness_percentage = (readiness_score / max_score) * 100
        else:
            readiness_percentage = 0
        
        # Определяем статус готовности
        if readiness_percentage >= 80:
            status = "ready"
            recommendation = "Можно начинать подготовку к Seed раунду"
        elif readiness_percentage >= 60:
            status = "almost_ready"
            recommendation = "Улучшить 1-2 ключевые метрики перед началом fundraising"
        else:
            status = "not_ready"
            recommendation = "Сфокусироваться на достижении key milestones перед fundraising"
        
        return {
            "readiness_score": round(readiness_percentage, 1),
            "status": status,
            "recommendation": recommendation,
            "gaps": gaps,
            "strengths": strengths,
            "next_steps": self._get_funding_next_steps(status, gaps),
            "ideal_timing": self._calculate_funding_timing(readiness_percentage, company_data)
        }
    
    def _get_funding_next_steps(self, status: str, gaps: List[str]) -> List[str]:
        """Получение следующих шагов для подготовки к fundraising"""
        
        if status == "ready":
            return [
                "Подготовить pitch deck",
                "Составить список target investors",
                "Подготовить financial model на 3 года",
                "Собрать references от клиентов",
                "Назначить первые встречи с инвесторами"
            ]
        elif status == "almost_ready":
            return [
                "Сфокусироваться на закрытии выявленных gaps",
                "Улучшить storytelling вокруг traction",
                "Начать building relationships с инвесторами",
                "Подготовить материалы для due diligence",
                "Определить ideal valuation expectations"
            ]
        else:
            return [
                "Создать 90-дневный план по улучшению метрик",
                "Фокусироваться на product и customer development",
                "Уменьшить burn rate для увеличения runway",
                "Искать angel investors или advisors",
                "Участвовать в accelerator programs"
            ]
    
    def _calculate_funding_timing(self, readiness_score: float, 
                                company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Расчет оптимального времени для fundraising"""
        
        runway = company_data.get("runway_months", 0)
        current_date = datetime.now()
        
        if readiness_score >= 70 and runway < 9:
            # Срочно нужно финансирование
            timing = "immediate"
            suggested_start = current_date
            suggested_close = current_date + timedelta(days=90)
        elif readiness_score >= 60:
            # Можно начинать подготовку
            timing = "in_1_3_months"
            suggested_start = current_date + timedelta(days=30)
            suggested_close = current_date + timedelta(days=120)
        else:
            # Нужно улучшать метрики
            timing = "in_3_6_months"
            suggested_start = current_date + timedelta(days=90)
            suggested_close = current_date + timedelta(days=180)
        
        return {
            "timing": timing,
            "suggested_start": suggested_start.strftime("%Y-%m-%d"),
            "suggested_close": suggested_close.strftime("%Y-%m-%d"),
            "runway_at_funding": max(0, runway - 3),  # Оставляем 3 месяца буфер
            "key_milestones_to_hit": self._get_funding_milestones(readiness_score)
        }
    
    def _get_funding_milestones(self, readiness_score: float) -> List[str]:
        """Получение milestones для достижения перед fundraising"""
        
        if readiness_score < 60:
            return [
                "Достичь $10k MRR",
                "Показать 20%+ monthly growth",
                "Иметь 10+ referenceable customers",
                "Доказать product-market fit через retention metrics"
            ]
        elif readiness_score < 70:
            return [
                "Достичь $25k MRR",
                "Показать 15%+ monthly growth 3 месяца подряд",
                "Иметь clear path to $100k MRR",
                "Построить repeatable sales process"
            ]
        else:
            return [
                "Подготовить investor materials",
                "Line up第一批 investor meetings",
                "Определить use of funds",
                "Подготовить due diligence package"
            ]

# Создаем глобальный экземпляр советника
pre_seed_advisor = PreSeedAdvisor()

# Экспортируем полезные функции
def analyze_pre_seed_company(company_data: Dict[str, Any]) -> Dict[str, Any]:
    """Публичная функция для анализа Pre-Seed компании"""
    return pre_seed_advisor.analyze_company(company_data)

def get_quarterly_plan(company_data: Dict[str, Any]) -> Dict[str, Any]:
    """Публичная функция для получения квартального плана"""
    return pre_seed_advisor.generate_quarterly_plan(company_data)

def assess_funding_readiness(company_data: Dict[str, Any]) -> Dict[str, Any]:
    """Публичная функция для оценки готовности к funding"""
    return pre_seed_advisor.get_funding_readiness_assessment(company_data)
