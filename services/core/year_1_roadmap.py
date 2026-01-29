"""
Дорожная карта на первый год для Pre-Seed SaaS стартапа
Помощь в планировании ключевых этапов и метрик
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import json
import pandas as pd
import numpy as np

@dataclass
class Milestone:
    """Временная точка на roadmap"""
    id: str
    name: str
    description: str
    category: str  # product, marketing, sales, team, funding
    priority: str  # critical, high, medium, low
    target_date: datetime
    dependencies: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    owner: str = ""
    status: str = "planned"  # planned, in_progress, completed, delayed, cancelled
    actual_date: Optional[datetime] = None
    notes: str = ""

@dataclass
class QuarterPlan:
    """План на квартал"""
    quarter: str  # "Q1 2024"
    start_date: datetime
    end_date: datetime
    theme: str
    objectives: List[str]
    key_results: List[Dict[str, Any]]
    milestones: List[Milestone]
    budget: float = 0.0
    team_size: int = 0

class Year1Roadmap:
    """
    Дорожная карта на первый год для SaaS стартапа
    Помогает спланировать ключевые этапы роста
    """
    
    def __init__(self):
        self.current_date = datetime.now()
        self.quarter_names = ["Q1", "Q2", "Q3", "Q4"]
        
        # Базовые этапы для Pre-Seed SaaS
        self.base_milestones = self._load_base_milestones()
    
    def _load_base_milestones(self) -> List[Milestone]:
        """Загрузка базовых этапов для первого года"""
        
        # Начинаем с текущей даты
        start_date = self.current_date
        
        milestones = [
            # Quarter 1: Foundation
            Milestone(
                id="M1",
                name="Запуск MVP",
                description="Запустить минимально жизнеспособный продукт с core features",
                category="product",
                priority="critical",
                target_date=start_date + timedelta(days=30),
                success_criteria=[
                    "Продукт решает одну ключевую проблему",
                    "Готовы к onboard первых 10 beta пользователей",
                    "Базовый UI/UX готов",
                    "Нет critical bugs"
                ],
                owner="CTO/Lead Developer"
            ),
            
            Milestone(
                id="M2",
                name="Первые 10 Beta пользователей",
                description="Привлечь первых 10 beta пользователей для тестирования",
                category="marketing",
                priority="critical",
                target_date=start_date + timedelta(days=45),
                dependencies=["M1"],
                success_criteria=[
                    "10 активных beta пользователей",
                    "Сбор фидбека от всех пользователей",
                    "NPS > 30",
                    "Daily active users > 5"
                ],
                owner="CEO/Founder"
            ),
            
            Milestone(
                id="M3",
                name="Определение ICP",
                description="Определить Ideal Customer Profile",
                category="sales",
                priority="high",
                target_date=start_date + timedelta(days=60),
                dependencies=["M2"],
                success_criteria=[
                    "Четкое описание ICP",
                    "Понимание pains & gains",
                    "Определены каналы привлечения",
                    "Разработано ценностное предложение"
                ],
                owner="CEO/Founder"
            ),
            
            # Quarter 2: Validation
            Milestone(
                id="M4",
                name="Первые платные клиенты",
                description="Конвертировать beta пользователей в платных клиентов",
                category="sales",
                priority="critical",
                target_date=start_date + timedelta(days=90),
                dependencies=["M3"],
                success_criteria=[
                    "5+ платных клиентов",
                    "MRR > $1,000",
                    "Готов sales playbook",
                    "Определен CAC"
                ],
                owner="CEO/Founder"
            ),
            
            Milestone(
                id="M5",
                name="Product-Market Fit Validation",
                description="Подтвердить product-market fit через метрики",
                category="product",
                priority="critical",
                target_date=start_date + timedelta(days=120),
                dependencies=["M4"],
                success_criteria=[
                    "NPS > 40",
                    "Месячный retention > 40%",
                    "Пользователи готовы рекомендовать",
                    "Оценка PMF > 40/100"
                ],
                owner="CEO/Founder"
            ),
            
            Milestone(
                id="M6",
                name="Оптимизация onboarding",
                description="Улучшить процесс onboarding новых пользователей",
                category="product",
                priority="high",
                target_date=start_date + timedelta(days=135),
                dependencies=["M5"],
                success_criteria=[
                    "Time to value < 1 день",
                    "Onboarding completion > 70%",
                    "Уменьшение support tickets",
                    "Улучшение первых 7 дней retention"
                ],
                owner="Product Manager"
            ),
            
            # Quarter 3: Scaling
            Milestone(
                id="M7",
                name="Достижение $5k MRR",
                description="Достичь $5,000 месячной выручки",
                category="sales",
                priority="critical",
                target_date=start_date + timedelta(days=180),
                dependencies=["M6"],
                success_criteria=[
                    "MRR > $5,000",
                    "20+ платных клиентов",
                    "Месячный рост > 20%",
                    "LTV/CAC > 2"
                ],
                owner="CEO/Founder"
            ),
            
            Milestone(
                id="M8",
                name="Нанять первого sales человека",
                description="Нанять первого сотрудника в sales",
                category="team",
                priority="high",
                target_date=start_date + timedelta(days=210),
                dependencies=["M7"],
                success_criteria=[
                    "Найден подходящий кандидат",
                    "Определены KPIs",
                    "Sales process документирован",
                    "Оборудование и tools готовы"
                ],
                owner="CEO/Founder"
            ),
            
            Milestone(
                id="M9",
                name="Запуск реферальной программы",
                description="Запустить программу для viral роста",
                category="marketing",
                priority="medium",
                target_date=start_date + timedelta(days=225),
                dependencies=["M7"],
                success_criteria=[
                    "Реферальная программа запущена",
                    "Virality coefficient > 0.1",
                    "> 10% новых пользователей через рефералы",
                    "Увеличилось organic growth"
                ],
                owner="Marketing Lead"
            ),
            
            # Quarter 4: Growth
            Milestone(
                id="M10",
                name="Достижение $10k MRR",
                description="Достичь $10,000 месячной выручки",
                category="sales",
                priority="critical",
                target_date=start_date + timedelta(days=270),
                dependencies=["M8", "M9"],
                success_criteria=[
                    "MRR > $10,000",
                    "40+ платных клиентов",
                    "Месячный рост > 15%",
                    "Positive unit economics"
                ],
                owner="CEO/Founder"
            ),
            
            Milestone(
                id="M11",
                name="Подготовка к Seed раунду",
                description="Подготовить материалы и pitch для Seed раунда",
                category="funding",
                priority="high",
                target_date=start_date + timedelta(days=300),
                dependencies=["M10"],
                success_criteria=[
                    "Pitch deck готов",
                    "Financial model на 3 года",
                    "Список target investors",
                    "Due diligence package"
                ],
                owner="CEO/Founder"
            ),
            
            Milestone(
                id="M12",
                name="Годовой обзор и планирование",
                description="Провести обзор года и спланировать следующий год",
                category="planning",
                priority="medium",
                target_date=start_date + timedelta(days=330),
                dependencies=["M10"],
                success_criteria=[
                    "Годовой отчет готов",
                    "План на следующий год",
                    "Уроки learned документированы",
                    "Командный retrospective проведен"
                ],
                owner="CEO/Founder"
            )
        ]
        
        return milestones
    
    def create_custom_roadmap(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Создание кастомной дорожной карты на основе данных компании
        
        Args:
            company_data: Данные компании для кастомизации roadmap
        
        Returns:
            Dict с кастомной дорожной картой
        """
        
        # Анализируем текущее состояние компании
        current_state = self._analyze_current_state(company_data)
        
        # Адаптируем базовые этапы
        custom_milestones = self._adapt_milestones(current_state)
        
        # Создаем квартальные планы
        quarter_plans = self._create_quarter_plans(custom_milestones)
        
        # Рассчитываем ресурсы
        resource_plan = self._calculate_resource_plan(quarter_plans, company_data)
        
        # Генерируем риски и mitigation strategies
        risk_analysis = self._analyze_risks(custom_milestones, company_data)
        
        # Создаем метрики успеха
        success_metrics = self._define_success_metrics(custom_milestones)
        
        return {
            "company_name": company_data.get("name", "Unnamed Company"),
            "current_state": current_state,
            "roadmap_start_date": self.current_date.strftime("%Y-%m-%d"),
            "roadmap_end_date": (self.current_date + timedelta(days=365)).strftime("%Y-%m-%d"),
            "milestones": custom_milestones,
            "quarter_plans": quarter_plans,
            "resource_plan": resource_plan,
            "risk_analysis": risk_analysis,
            "success_metrics": success_metrics,
            "timeline_visualization": self._create_timeline_visualization(custom_milestones),
            "created_at": datetime.now().isoformat()
        }
    
    def _analyze_current_state(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ текущего состояния компании"""
        
        current_state = {
            "stage": company_data.get("stage", "pre_seed"),
            "has_mvp": company_data.get("has_mvp", False),
            "has_paying_customers": company_data.get("has_paying_customers", False),
            "current_mrr": company_data.get("current_mrr", 0),
            "team_size": company_data.get("team_size", 1),
            "runway_months": company_data.get("runway_months", 0),
            "key_strengths": [],
            "key_challenges": [],
            "readiness_level": "early"  # early, mid, late
        }
        
        # Определяем readiness level
        if current_state["has_paying_customers"] and current_state["current_mrr"] > 0:
            if current_state["current_mrr"] >= 10000:
                current_state["readiness_level"] = "late"
            elif current_state["current_mrr"] >= 1000:
                current_state["readiness_level"] = "mid"
        
        # Определяем strengths
        if current_state["team_size"] >= 3:
            current_state["key_strengths"].append("Команда с нужными компетенциями")
        
        if current_state["runway_months"] >= 12:
            current_state["key_strengths"].append("Достаточный runway")
        elif current_state["runway_months"] < 6:
            current_state["key_challenges"].append("Ограниченный runway")
        
        if not current_state["has_mvp"]:
            current_state["key_challenges"].append("Нет MVP")
        
        if not current_state["has_paying_customers"]:
            current_state["key_challenges"].append("Нет платных клиентов")
        
        return current_state
    
    def _adapt_milestones(self, current_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Адаптация этапов под текущее состояние"""
        
        adapted_milestones = []
        
        for milestone in self.base_milestones:
            milestone_dict = self._milestone_to_dict(milestone)
            
            # Адаптируем даты в зависимости от readiness level
            if current_state["readiness_level"] == "mid":
                # Сдвигаем даты на 3 месяца вперед для уже продвинутых компаний
                original_date = milestone.target_date
                new_date = original_date - timedelta(days=90)  # Начинаем раньше
                milestone_dict["target_date"] = new_date.strftime("%Y-%m-%d")
            
            elif current_state["readiness_level"] == "late":
                # Пропускаем уже пройденные этапы
                if milestone.id in ["M1", "M2", "M3", "M4"]:
                    milestone_dict["status"] = "completed"
                    milestone_dict["actual_date"] = (self.current_date - timedelta(days=30)).strftime("%Y-%m-%d")
                
                # Сдвигаем оставшиеся этапы
                original_date = milestone.target_date
                new_date = original_date - timedelta(days=180)
                milestone_dict["target_date"] = new_date.strftime("%Y-%m-%d")
            
            # Адаптируем приоритеты в зависимости от challenges
            if "Ограниченный runway" in current_state["key_challenges"]:
                if "финансирование" in milestone.name.lower() or "mrr" in milestone.name.lower():
                    milestone_dict["priority"] = "critical"
            
            adapted_milestones.append(milestone_dict)
        
        return adapted_milestones
    
    def _milestone_to_dict(self, milestone: Milestone) -> Dict[str, Any]:
        """Преобразование объекта Milestone в словарь"""
        
        return {
            "id": milestone.id,
            "name": milestone.name,
            "description": milestone.description,
            "category": milestone.category,
            "priority": milestone.priority,
            "target_date": milestone.target_date.strftime("%Y-%m-%d"),
            "dependencies": milestone.dependencies,
            "success_criteria": milestone.success_criteria,
            "owner": milestone.owner,
            "status": milestone.status,
            "actual_date": milestone.actual_date.strftime("%Y-%m-%d") if milestone.actual_date else None,
            "notes": milestone.notes
        }
    
    def _create_quarter_plans(self, milestones: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Создание квартальных планов на основе этапов"""
        
        quarter_plans = []
        current_year = self.current_date.year
        
        # Группируем этапы по кварталам
        for quarter_num in range(1, 5):
            quarter_name = f"Q{quarter_num} {current_year}"
            
            # Даты квартала
            if quarter_num == 1:
                start_date = datetime(current_year, 1, 1)
                end_date = datetime(current_year, 3, 31)
            elif quarter_num == 2:
                start_date = datetime(current_year, 4, 1)
                end_date = datetime(current_year, 6, 30)
            elif quarter_num == 3:
                start_date = datetime(current_year, 7, 1)
                end_date = datetime(current_year, 9, 30)
            else:  # quarter_num == 4
                start_date = datetime(current_year, 10, 1)
                end_date = datetime(current_year, 12, 31)
            
            # Фильтруем этапы этого квартала
            quarter_milestones = []
            for milestone in milestones:
                try:
                    milestone_date = datetime.strptime(milestone["target_date"], "%Y-%m-%d")
                    if start_date <= milestone_date <= end_date:
                        quarter_milestones.append(milestone)
                except:
                    continue
            
            # Определяем тему квартала на основе этапов
            theme = self._determine_quarter_theme(quarter_num, quarter_milestones)
            
            # Определяем objectives
            objectives = self._determine_quarter_objectives(quarter_num, quarter_milestones)
            
            # Определяем key results
            key_results = self._determine_quarter_key_results(quarter_num, objectives)
            
            # Создаем план квартала
            quarter_plan = {
                "quarter": quarter_name,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "theme": theme,
                "objectives": objectives,
                "key_results": key_results,
                "milestones": quarter_milestones,
                "budget": self._estimate_quarter_budget(quarter_num, quarter_milestones),
                "team_size": self._estimate_team_size(quarter_num)
            }
            
            quarter_plans.append(quarter_plan)
        
        return quarter_plans
    
    def _determine_quarter_theme(self, quarter_num: int, 
                                milestones: List[Dict[str, Any]]) -> str:
        """Определение темы квартала"""
        
        themes = {
            1: "Foundation & Validation",
            2: "Product-Market Fit & Early Traction",
            3: "Scaling & Process Building",
            4: "Growth & Fundraising Preparation"
        }
        
        return themes.get(quarter_num, "Planning & Execution")
    
    def _determine_quarter_objectives(self, quarter_num: int, 
                                     milestones: List[Dict[str, Any]]) -> List[str]:
        """Определение целей квартала"""
        
        # Базовые цели по кварталам
        base_objectives = {
            1: [
                "Запустить MVP и привлечь первых пользователей",
                "Определить Ideal Customer Profile",
                "Начать сбор обратной связи и данных"
            ],
            2: [
                "Конвертировать первых платных клиентов",
                "Подтвердить Product-Market Fit",
                "Оптимизировать ключевые процессы"
            ],
            3: [
                "Достичь значимого MRR ($5k+)",
                "Построить repeatable sales process",
                "Нанять ключевых сотрудников"
            ],
            4: [
                "Достичь $10k+ MRR",
                "Подготовиться к следующему раунду финансирования",
                "Спланировать следующий год роста"
            ]
        }
        
        return base_objectives.get(quarter_num, [])
    
    def _determine_quarter_key_results(self, quarter_num: int, 
                                      objectives: List[str]) -> List[Dict[str, Any]]:
        """Определение ключевых результатов квартала"""
        
        key_results = []
        
        kr_templates = {
            1: [
                {"objective": objectives[0], "kr": "Запустить MVP с 3 core features", "metric": "features", "target": 3},
                {"objective": objectives[0], "kr": "Привлечь 10+ beta пользователей", "metric": "beta_users", "target": 10},
                {"objective": objectives[1], "kr": "Провести 20+ customer interviews", "metric": "interviews", "target": 20},
                {"objective": objectives[2], "kr": "Собрать feedback от всех beta пользователей", "metric": "feedback_rate", "target": 100}
            ],
            2: [
                {"objective": objectives[0], "kr": "Конвертировать 5+ платных клиентов", "metric": "paying_customers", "target": 5},
                {"objective": objectives[0], "kr": "Достичь $1k+ MRR", "metric": "mrr", "target": 1000},
                {"objective": objectives[1], "kr": "Достичь NPS > 40", "metric": "nps", "target": 40},
                {"objective": objectives[2], "kr": "Уменьшить time to value до 1 дня", "metric": "ttv_days", "target": 1}
            ],
            3: [
                {"objective": objectives[0], "kr": "Достичь $5k+ MRR", "metric": "mrr", "target": 5000},
                {"objective": objectives[0], "kr": "Иметь 20+ платных клиентов", "metric": "customers", "target": 20},
                {"objective": objectives[1], "kr": "Документировать sales process", "metric": "process_documented", "target": 1},
                {"objective": objectives[2], "kr": "Нанять 2 ключевых сотрудника", "metric": "new_hires", "target": 2}
            ],
            4: [
                {"objective": objectives[0], "kr": "Достичь $10k+ MRR", "metric": "mrr", "target": 10000},
                {"objective": objectives[0], "kr": "Иметь 40+ платных клиентов", "metric": "customers", "target": 40},
                {"objective": objectives[1], "kr": "Подготовить pitch deck", "metric": "deck_ready", "target": 1},
                {"objective": objectives[2], "kr": "Создать план на следующий год", "metric": "plan_created", "target": 1}
            ]
        }
        
        return kr_templates.get(quarter_num, [])
    
    def _estimate_quarter_budget(self, quarter_num: int, 
                                milestones: List[Dict[str, Any]]) -> float:
        """Оценка бюджета на квартал"""
        
        # Базовые бюджеты по кварталам (в рублях)
        base_budgets = {
            1: 500000,  # 500k руб. - разработка MVP, базовый маркетинг
            2: 750000,  # 750k руб. - улучшение продукта, ранние продажи
            3: 1000000, # 1M руб. - найм, масштабирование
            4: 1250000  # 1.25M руб. - подготовка к fundraising, growth
        }
        
        return base_budgets.get(quarter_num, 500000)
    
    def _estimate_team_size(self, quarter_num: int) -> int:
        """Оценка размера команды на квартал"""
        
        # Прогноз размера команды по кварталам
        team_sizes = {
            1: 3,  # Founder, Tech Lead, возможно Product
            2: 4,  # + Marketing/Sales
            3: 6,  # + Developers, Sales
            4: 8   # + дополнительные роли
        }
        
        return team_sizes.get(quarter_num, 3)
    
    def _calculate_resource_plan(self, quarter_plans: List[Dict[str, Any]], 
                               company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Расчет плана ресурсов"""
        
        total_budget = sum(qp["budget"] for qp in quarter_plans)
        current_cash = company_data.get("cash_balance", 0)
        
        # Анализ финансирования
        funding_needed = max(0, total_budget - current_cash)
        funding_timing = []
        
        if funding_needed > 0:
            # Определяем когда нужно финансирование
            cumulative_spend = 0
            for i, qp in enumerate(quarter_plans):
                cumulative_spend += qp["budget"]
                if cumulative_spend > current_cash and not funding_timing:
                    funding_timing.append({
                        "quarter": qp["quarter"],
                        "amount_needed": cumulative_spend - current_cash,
                        "timing": "before" if i == 0 else f"during {qp['quarter']}"
                    })
        
        # План найма
        hiring_plan = []
        current_team_size = company_data.get("team_size", 1)
        
        for i, qp in enumerate(quarter_plans):
            if qp["team_size"] > current_team_size:
                hires_needed = qp["team_size"] - current_team_size
                hiring_plan.append({
                    "quarter": qp["quarter"],
                    "hires_needed": hires_needed,
                    "key_roles": self._get_key_roles_for_quarter(i + 1),
                    "estimated_cost": hires_needed * 150000  # 150k руб./мес на сотрудника
                })
                current_team_size = qp["team_size"]
        
        return {
            "financial_summary": {
                "total_budget_year": total_budget,
                "current_cash": current_cash,
                "funding_needed": funding_needed,
                "runway_months": current_cash / (total_budget / 12) if total_budget > 0 else 0,
                "burn_rate_monthly": total_budget / 12
            },
            "funding_timing": funding_timing,
            "hiring_plan": hiring_plan,
            "key_resource_assumptions": [
                "Зарплаты: 150k руб./мес на сотрудника",
                "Маркетинг: 20-30% от бюджета",
                "Разработка: 40-50% от бюджета",
                "Офис/инфраструктура: 10-15% от бюджета"
            ]
        }
    
    def _get_key_roles_for_quarter(self, quarter_num: int) -> List[str]:
        """Получение ключевых ролей для найма в квартал"""
        
        roles_by_quarter = {
            1: ["Product Manager", "UI/UX Designer"],
            2: ["Marketing Specialist", "Sales Development Rep"],
            3: ["Senior Developer", "Customer Success Manager"],
            4: ["Head of Sales", "Finance Manager"]
        }
        
        return roles_by_quarter.get(quarter_num, [])
    
    def _analyze_risks(self, milestones: List[Dict[str, Any]], 
                      company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ рисков дорожной карты"""
        
        risks = []
        mitigations = []
        
        # Анализируем критические этапы
        critical_milestones = [m for m in milestones if m["priority"] == "critical"]
        
        for milestone in critical_milestones:
            risk = self._identify_milestone_risk(milestone, company_data)
            if risk:
                risks.append(risk)
                mitigations.append(self._suggest_mitigation(risk))
        
        # Общие риски
        general_risks = [
            {
                "risk": "Нехватка финансирования",
                "probability": "high",
                "impact": "critical",
                "description": "Недостаточно денег для выполнения плана",
                "trigger": "Runway < 3 месяцев"
            },
            {
                "risk": "Проблемы с наймом",
                "probability": "medium",
                "impact": "high",
                "description": "Не удается найти нужных специалистов",
                "trigger": "Вакансии открыты > 60 дней"
            },
            {
                "risk": "Технические сложности",
                "probability": "medium",
                "impact": "high",
                "description": "Задержки в разработке или технические проблемы",
                "trigger": "Пропуск сроков по этапам разработки"
            },
            {
                "risk": "Конкуренция",
                "probability": "medium",
                "impact": "medium",
                "description": "Появление сильных конкурентов или копирование",
                "trigger": "Потеря market share или клиентов"
            }
        ]
        
        risks.extend(general_risks)
        
        # Общие mitigation strategies
        general_mitigations = [
            "Регулярный мониторинг cash flow и runway",
            "Начинать hiring process заранее",
            "Иметь technical debt management plan",
            "Постоянный market research и competitive analysis",
            "Гибкое планирование и регулярные корректировки"
        ]
        
        mitigations.extend([{"strategy": m} for m in general_mitigations])
        
        return {
            "identified_risks": risks,
            "mitigation_strategies": mitigations,
            "risk_monitoring_framework": {
                "frequency": "еженедельно",
                "metrics": ["runway", "hiring_progress", "development_velocity", "customer_acquisition"],
                "escalation_process": "immediate для critical risks"
            }
        }
    
    def _identify_milestone_risk(self, milestone: Dict[str, Any], 
                                company_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Идентификация рисков для конкретного этапа"""
        
        milestone_name = milestone["name"].lower()
        
        if "mrr" in milestone_name:
            current_mrr = company_data.get("current_mrr", 0)
            # Предполагаем, что target MRR указан в success criteria
            for criteria in milestone.get("success_criteria", []):
                if "mrr" in criteria.lower() or "$" in criteria:
                    # Пытаемся извлечь целевое значение
                    import re
                    numbers = re.findall(r'\$?(\d+[kK]?)', criteria)
                    if numbers:
                        target_str = numbers[0]
                        if 'k' in target_str.lower():
                            target = float(target_str.lower().replace('k', '')) * 1000
                        else:
                            target = float(target_str)
                        
                        if target > current_mrr * 3:  # Если цель в 3+ раза больше текущего
                            return {
                                "risk": f"Амбициозная цель MRR для {milestone['name']}",
                                "probability": "medium",
                                "impact": "high",
                                "description": f"Цель ${target:,.0f} может быть слишком амбициозной при текущем MRR ${current_mrr:,.0f}",
                                "trigger": "Отставание от плана по MRR на 40%+"
                            }
        
        elif "найм" in milestone_name or "hiring" in milestone_name:
            current_team_size = company_data.get("team_size", 1)
            if current_team_size < 3:  # Маленькая команда
                return {
                    "risk": f"Сложности с наймом для {milestone['name']}",
                    "probability": "high",
                    "impact": "high",
                    "description": "Маленькой команде сложно проводить hiring process",
                    "trigger": "Вакансии открыты > 30 дней без подходящих кандидатов"
                }
        
        return None
    
    def _suggest_mitigation(self, risk: Dict[str, Any]) -> Dict[str, Any]:
        """Предложение mitigation strategy для риска"""
        
        risk_name = risk["risk"].lower()
        
        mitigations = {
            "mrr": {
                "strategy": "Разбить цель на smaller milestones",
                "actions": [
                    "Фокусироваться на улучшении conversion rate",
                    "Тестировать разные pricing модели",
                    "Улучшить retention для увеличения LTV",
                    "Экспериментировать с новыми каналами привлечения"
                ],
                "contingency": "Если через 2 месяца отставание > 30%, пересмотреть цели"
            },
            "найм": {
                "strategy": "Начать hiring process заранее",
                "actions": [
                    "Использовать recruitment agencies",
                    "Активно работать с referrals",
                    "Создать strong employer brand",
                    "Предложить competitive compensation package"
                ],
                "contingency": "Рассмотреть contractors или outsourcing для critical функций"
            }
        }
        
        for key in mitigations:
            if key in risk_name:
                return {
                    "risk": risk["risk"],
                    **mitigations[key]
                }
        
        # Default mitigation
        return {
            "risk": risk["risk"],
            "strategy": "Регулярный мониторинг и early intervention",
            "actions": ["Установить early warning indicators", "Регулярные check-ins"],
            "contingency": "Иметь backup plan"
        }
    
    def _define_success_metrics(self, milestones: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Определение метрик успеха для дорожной карты"""
        
        metrics = {
            "financial_metrics": [
                {"metric": "MRR", "target": 10000, "unit": "USD", "frequency": "monthly"},
                {"metric": "ARR", "target": 120000, "unit": "USD", "frequency": "annual"},
                {"metric": "Gross Margin", "target": 0.8, "unit": "percentage", "frequency": "monthly"},
                {"metric": "Runway", "target": 12, "unit": "months", "frequency": "monthly"}
            ],
            "customer_metrics": [
                {"metric": "Paying Customers", "target": 40, "unit": "customers", "frequency": "monthly"},
                {"metric": "Net Revenue Retention", "target": 1.1, "unit": "ratio", "frequency": "monthly"},
                {"metric": "CAC", "target": 20000, "unit": "RUB", "frequency": "monthly"},
                {"metric": "LTV/CAC Ratio", "target": 3.0, "unit": "ratio", "frequency": "quarterly"}
            ],
            "product_metrics": [
                {"metric": "NPS", "target": 40, "unit": "score", "frequency": "quarterly"},
                {"metric": "Monthly Active Users", "target": 100, "unit": "users", "frequency": "monthly"},
                {"metric": "Feature Adoption Rate", "target": 0.6, "unit": "percentage", "frequency": "monthly"},
                {"metric": "Product-Market Fit Score", "target": 40, "unit": "score", "frequency": "quarterly"}
            ],
            "team_metrics": [
                {"metric": "Team Size", "target": 8, "unit": "people", "frequency": "quarterly"},
                {"metric": "Employee NPS", "target": 30, "unit": "score", "frequency": "semi-annual"},
                {"metric": "Time to Hire", "target": 45, "unit": "days", "frequency": "quarterly"}
            ]
        }
        
        # Tracking framework
        tracking = {
            "dashboard_frequency": "weekly",
            "review_meetings": [
                {"type": "Weekly Leadership", "focus": "Progress against plan"},
                {"type": "Monthly All-Hands", "focus": "Company-wide updates"},
                {"type": "Quarterly Board", "focus": "Strategic review and planning"}
            ],
            "reporting": [
                {"report": "Weekly Metrics", "audience": "Leadership Team", "format": "Dashboard"},
                {"report": "Monthly Business Review", "audience": "All Employees", "format": "Presentation"},
                {"report": "Quarterly Investor Update", "audience": "Investors", "format": "Email + Deck"}
            ]
        }
        
        return {
            "metrics": metrics,
            "tracking_framework": tracking,
            "success_criteria": [
                "Достичь 80%+ целей по кварталам",
                "Positive unit economics (LTV/CAC > 3)",
                "Достаточный runway для следующего раунда (12+ месяцев)",
                "Команда мотивирована и aligned с целями"
            ]
        }
    
    def _create_timeline_visualization(self, milestones: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Создание визуализации таймлайна"""
        
        # Группируем этапы по категориям
        categories = {}
        for milestone in milestones:
            category = milestone["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append(milestone)
        
        # Создаем timeline data
        timeline_data = []
        for milestone in milestones:
            timeline_data.append({
                "id": milestone["id"],
                "name": milestone["name"],
                "category": milestone["category"],
                "priority": milestone["priority"],
                "target_date": milestone["target_date"],
                "owner": milestone["owner"],
                "status": milestone["status"]
            })
        
        # Сортируем по дате
        timeline_data.sort(key=lambda x: x["target_date"])
        
        return {
            "timeline_data": timeline_data,
            "categories": list(categories.keys()),
            "total_milestones": len(milestones),
            "critical_milestones": len([m for m in milestones if m["priority"] == "critical"]),
            "timeline_start": min([m["target_date"] for m in milestones]) if milestones else "",
            "timeline_end": max([m["target_date"] for m in milestones]) if milestones else ""
        }
    
    def get_quarterly_focus_areas(self, quarter: int) -> Dict[str, Any]:
        """
        Получение фокусных областей для квартала
        
        Args:
            quarter: Номер квартала (1-4)
        
        Returns:
            Dict с фокусными областями
        """
        
        focus_areas = {
            1: {
                "theme": "Foundation",
                "key_focus_areas": [
                    {
                        "area": "Product Development",
                        "priority": "critical",
                        "key_activities": [
                            "Разработка MVP",
                            "User testing",
                            "Bug fixing и stabilization"
                        ],
                        "success_metrics": ["MVP launched", "User feedback collected", "Critical bugs resolved"]
                    },
                    {
                        "area": "Customer Discovery",
                        "priority": "critical",
                        "key_activities": [
                            "Customer interviews",
                            "Market research",
                            "ICP definition"
                        ],
                        "success_metrics": ["20+ interviews completed", "Clear ICP defined", "Value proposition validated"]
                    },
                    {
                        "area": "Team Building",
                        "priority": "high",
                        "key_activities": [
                            "Определение roles",
                            "Найм key positions",
                            "Создание culture"
                        ],
                        "success_metrics": ["Key roles defined", "First hires made", "Culture document created"]
                    }
                ]
            },
            2: {
                "theme": "Validation",
                "key_focus_areas": [
                    {
                        "area": "Revenue Generation",
                        "priority": "critical",
                        "key_activities": [
                            "First sales",
                            "Pricing experiments",
                            "Payment integration"
                        ],
                        "success_metrics": ["First paying customers", "Pricing model validated", "Revenue stream established"]
                    },
                    {
                        "area": "Product-Market Fit",
                        "priority": "critical",
                        "key_activities": [
                            "Retention analysis",
                            "Feature adoption tracking",
                            "Customer satisfaction measurement"
                        ],
                        "success_metrics": ["Retention > 40%", "PMF score > 40", "NPS > 30"]
                    },
                    {
                        "area": "Process Development",
                        "priority": "medium",
                        "key_activities": [
                            "Sales process definition",
                            "Customer support setup",
                            "Onboarding optimization"
                        ],
                        "success_metrics": ["Sales playbook created", "Support system in place", "Onboarding time reduced"]
                    }
                ]
            },
            3: {
                "theme": "Scaling",
                "key_focus_areas": [
                    {
                        "area": "Growth Acceleration",
                        "priority": "critical",
                        "key_activities": [
                            "Marketing scale-up",
                            "Sales team expansion",
                            "Channel partnerships"
                        ],
                        "success_metrics": ["MRR growth > 20%", "CAC optimized", "New channels tested"]
                    },
                    {
                        "area": "Team Scaling",
                        "priority": "high",
                        "key_activities": [
                            "Additional hiring",
                            "Management training",
                            "Culture scaling"
                        ],
                        "success_metrics": ["Team size doubled", "Managers trained", "Culture maintained"]
                    },
                    {
                        "area": "Operational Excellence",
                        "priority": "medium",
                        "key_activities": [
                            "Process automation",
                            "Metrics dashboard",
                            "Financial controls"
                        ],
                        "success_metrics": ["Key processes automated", "Real-time dashboards", "Financial reporting improved"]
                    }
                ]
            },
            4: {
                "theme": "Growth & Funding",
                "key_focus_areas": [
                    {
                        "area": "Fundraising Preparation",
                        "priority": "critical",
                        "key_activities": [
                            "Pitch deck creation",
                            "Financial modeling",
                            "Investor outreach"
                        ],
                        "success_metrics": ["Deck completed", "Model validated", "Investor meetings scheduled"]
                    },
                    {
                        "area": "Strategic Growth",
                        "priority": "high",
                        "key_activities": [
                            "Market expansion",
                            "Product roadmap planning",
                            "Competitive positioning"
                        ],
                        "success_metrics": ["New markets identified", "Roadmap for next year", "Competitive analysis updated"]
                    },
                    {
                        "area": "Organizational Development",
                        "priority": "medium",
                        "key_activities": [
                            "Leadership development",
                            "Succession planning",
                            "Annual planning"
                        ],
                        "success_metrics": ["Leadership team strengthened", "Succession plan in place", "Next year plan created"]
                    }
                ]
            }
        }
        
        return focus_areas.get(quarter, {})
    
    def generate_execution_plan(self, roadmap: Dict[str, Any]) -> Dict[str, Any]:
        """
        Генерация детального плана исполнения
        
        Args:
            roadmap: Дорожная карта, созданная create_custom_roadmap
        
        Returns:
            Dict с детальным планом исполнения
        """
        
        execution_plan = {
            "weekly_structure": self._create_weekly_structure(),
            "meeting_rhythm": self._create_meeting_rhythm(),
            "decision_framework": self._create_decision_framework(),
            "progress_tracking": self._create_progress_tracking(),
            "communication_plan": self._create_communication_plan()
        }
        
        return execution_plan
    
    def _create_weekly_structure(self) -> Dict[str, Any]:
        """Создание недельной структуры работы"""
        
        return {
            "monday": {
                "focus": "Planning & Strategy",
                "activities": [
                    "Weekly planning meeting",
                    "Goal setting for the week",
                    "Priority alignment"
                ],
                "outcome": "Clear priorities for the week"
            },
            "tuesday_thursday": {
                "focus": "Execution",
                "activities": [
                    "Deep work on key projects",
                    "Customer meetings",
                    "Product development"
                ],
                "outcome": "Progress on key initiatives"
            },
            "friday": {
                "focus": "Review & Learning",
                "activities": [
                    "Weekly review meeting",
                    "Metrics analysis",
                    "Retrospective",
                    "Learning session"
                ],
                "outcome": "Lessons learned and plan for next week"
            },
            "weekend": {
                "focus": "Rest & Recharge",
                "guidelines": [
                    "No work emails",
                    "Time for hobbies and family",
                    "Physical activity",
                    "Mental recharge"
                ]
            }
        }
    
    def _create_meeting_rhythm(self) -> Dict[str, Any]:
        """Создание ритма встреч"""
        
        return {
            "daily": {
                "meeting": "15-minute Standup",
                "duration": "15 минут",
                "participants": "Whole team",
                "purpose": "Alignment, blockers, daily plan",
                "agenda": [
                    "What did you accomplish yesterday?",
                    "What will you work on today?",
                    "Any blockers or needs?"
                ]
            },
            "weekly": {
                "meeting": "Leadership Sync",
                "duration": "60 минут",
                "participants": "Leadership team",
                "purpose": "Strategic alignment, progress review",
                "agenda": [
                    "Review of weekly metrics",
                    "Progress on key initiatives",
                    "Strategic decisions needed",
                    "Risk assessment"
                ]
            },
            "biweekly": {
                "meeting": "All-Hands",
                "duration": "30 минут",
                "participants": "All employees",
                "purpose": "Company updates, transparency",
                "agenda": [
                    "Company updates from leadership",
                    "Team highlights",
                    "Q&A session",
                    "Recognition"
                ]
            },
            "monthly": {
                "meeting": "Board Meeting",
                "duration": "90 минут",
                "participants": "Board members, leadership",
                "purpose": "Governance, strategic review",
                "agenda": [
                    "Financial review",
                    "Progress against plan",
                    "Strategic discussions",
                    "Decision making"
                ]
            },
            "quarterly": {
                "meeting": "Strategy Offsite",
                "duration": "1-2 дня",
                "participants": "Leadership team",
                "purpose": "Strategic planning, team building",
                "agenda": [
                    "Review of quarter",
                    "Planning for next quarter",
                    "Team building activities",
                    "Big picture thinking"
                ]
            }
        }
    
    def _create_decision_framework(self) -> Dict[str, Any]:
        """Создание framework для принятия решений"""
        
        return {
            "decision_types": {
                "type_a": {
                    "description": "Big, irreversible decisions",
                    "examples": ["Pivoting business model", "Major hiring", "Large expenditures"],
                    "process": "DACI Framework (Driver, Approver, Contributors, Informed)",
                    "timeframe": "1-2 недели",
                    "approval": "Board/CEO"
                },
                "type_b": {
                    "description": "Important, reversible decisions",
                    "examples": ["Feature prioritization", "Marketing campaigns", "Team structure"],
                    "process": "RAPID Framework (Recommend, Agree, Perform, Input, Decide)",
                    "timeframe": "3-5 дней",
                    "approval": "Leadership team"
                },
                "type_c": {
                    "description": "Small, reversible decisions",
                    "examples": ["Tool selection", "Process changes", "Team activities"],
                    "process": "Consult then decide",
                    "timeframe": "1-2 дня",
                    "approval": "Team lead/Manager"
                }
            },
            "decision_principles": [
                "Speed over perfection for reversible decisions",
                "Data-informed but not data-paralyzed",
                "Default to transparency",
                "Learn from every decision"
            ],
            "escalation_process": {
                "level_1": "Discuss with team lead",
                "level_2": "Escalate to department head",
                "level_3": "Bring to leadership team",
                "level_4": "Board decision if needed"
            }
        }
    
    def _create_progress_tracking(self) -> Dict[str, Any]:
        """Создание системы отслеживания прогресса"""
        
        return {
            "tracking_tools": {
                "project_management": ["Jira", "Asana", "Trello", "Monday.com"],
                "communication": ["Slack", "Microsoft Teams", "Discord"],
                "documentation": ["Notion", "Confluence", "Google Workspace"],
                "metrics": ["Google Analytics", "Mixpanel", "Amplitude", "Custom dashboards"]
            },
            "key_performance_indicators": {
                "daily": ["Active users", "Revenue", "Support tickets", "Deployment frequency"],
                "weekly": ["MRR growth", "Customer acquisition", "Team velocity", "Product quality"],
                "monthly": ["Financial metrics", "Customer satisfaction", "Employee engagement", "Strategic goals"]
            },
            "reporting_frequency": {
                "daily": "Team standup metrics",
                "weekly": "Leadership dashboard",
                "monthly": "Board report",
                "quarterly": "Investor update"
            },
            "success_criteria": {
                "green": "On track or ahead of plan",
                "yellow": "Slightly behind, manageable",
                "red": "Significantly behind, intervention needed"
            }
        }
    
    def _create_communication_plan(self) -> Dict[str, Any]:
        """Создание плана коммуникаций"""
        
        return {
            "internal_communications": {
                "transparency_level": "High",
                "channels": {
                    "announcements": "Company-wide email + All-hands",
                    "updates": "Slack announcements channel",
                    "discussions": "Team channels + Direct messages",
                    "documentation": "Notion wiki + Google Drive"
                },
                "frequency": {
                    "daily": "Team updates",
                    "weekly": "Company updates",
                    "monthly": "Performance review",
                    "quarterly": "Strategy share"
                }
            },
            "external_communications": {
                "stakeholders": {
                    "investors": "Monthly updates + Quarterly meetings",
                    "customers": "Newsletter + Product updates",
                    "partners": "Regular check-ins + Joint planning",
                    "press": "Press releases + Media relations"
                },
                "messaging": {
                    "vision": "Clear, consistent vision statement",
                    "value_prop": "Customer-focused value proposition",
                    "differentiation": "Unique selling points",
                    "progress": "Transparent progress sharing"
                }
            },
            "crisis_communication": {
                "plan": "Pre-defined crisis communication plan",
                "team": "Crisis response team identified",
                "channels": "Designated communication channels",
                "messaging": "Clear, honest, timely messaging"
            }
        }

# Создаем глобальный экземпляр roadmap planner
year1_roadmap = Year1Roadmap()

# Экспортируем полезные функции
def create_company_roadmap(company_data: Dict[str, Any]) -> Dict[str, Any]:
    """Публичная функция для создания дорожной карты"""
    return year1_roadmap.create_custom_roadmap(company_data)

def get_quarterly_focus(quarter: int) -> Dict[str, Any]:
    """Публичная функция для получения фокусных областей квартала"""
    return year1_roadmap.get_quarterly_focus_areas(quarter)

def generate_execution_strategy(roadmap: Dict[str, Any]) -> Dict[str, Any]:
    """Публичная функция для генерации стратегии исполнения"""
    return year1_roadmap.generate_execution_plan(roadmap)