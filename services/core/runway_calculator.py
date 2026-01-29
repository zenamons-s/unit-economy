"""
Калькулятор Runway для SaaS стартапов
Расчет времени до сгорания денег с учетом разных сценариев
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import numpy as np
from dataclasses import dataclass
import plotly.graph_objects as go
import plotly.express as px

@dataclass
class RunwayScenario:
    """Сценарий расчета runway"""
    name: str
    description: str
    assumptions: Dict[str, Any]
    monthly_burn_rate: float
    cash_balance: float
    runway_months: float
    cash_out_date: datetime
    
    # Прогнозы
    projections: Optional[pd.DataFrame] = None
    sensitivity_analysis: Optional[Dict[str, Any]] = None

class RunwayCalculator:
    """
    Продвинутый калькулятор Runway для SaaS стартапов
    С учетом роста, seasonality, fundraising timing
    """
    
    def __init__(self):
        self.default_assumptions = {
            'monthly_growth_rate': 0.10,  # 10% monthly growth
            'seasonality_factor': 1.0,
            'fundraising_probability': 0.7,
            'fundraising_timing_months': 6,
            'fundraising_amount': 0,
            'cost_reduction_possible': 0.15,  # 15% cost reduction possible
            'revenue_acceleration_possible': 0.20  # 20% revenue acceleration possible
        }
    
    def calculate_runway(self, cash_balance: float, monthly_burn_rate: float,
                        monthly_revenue: float = 0, growth_rate: float = 0.0,
                        include_scenarios: bool = True) -> Dict[str, Any]:
        """
        Основной расчет runway
        
        Args:
            cash_balance: Текущий баланс денежных средств
            monthly_burn_rate: Текущий месячный burn rate
            monthly_revenue: Текущая месячная выручка (для расчета net burn)
            growth_rate: Ожидаемый месячный рост выручки
            include_scenarios: Включать анализ сценариев
        
        Returns:
            Dict с расчетами runway
        """
        
        # Базовый расчет
        basic_runway = self._calculate_basic_runway(cash_balance, monthly_burn_rate, monthly_revenue)
        
        # Расчет с учетом роста
        growth_runway = self._calculate_growth_adjusted_runway(
            cash_balance, monthly_burn_rate, monthly_revenue, growth_rate
        )
        
        # Анализ сценариев
        scenarios = {}
        if include_scenarios:
            scenarios = self._analyze_scenarios(cash_balance, monthly_burn_rate, monthly_revenue, growth_rate)
        
        # Анализ чувствительности
        sensitivity = self._perform_sensitivity_analysis(
            cash_balance, monthly_burn_rate, monthly_revenue, growth_rate
        )
        
        # Рекомендации
        recommendations = self._generate_recommendations(basic_runway, growth_runway, scenarios)
        
        # Визуализации
        visualizations = self._create_visualizations(basic_runway, growth_runway, scenarios)
        
        return {
            "calculation_date": datetime.now().isoformat(),
            "input_parameters": {
                "cash_balance": cash_balance,
                "monthly_burn_rate": monthly_burn_rate,
                "monthly_revenue": monthly_revenue,
                "growth_rate": growth_rate,
                "net_burn_rate": monthly_burn_rate - monthly_revenue
            },
            "basic_runway": basic_runway,
            "growth_adjusted_runway": growth_runway,
            "scenarios": scenarios,
            "sensitivity_analysis": sensitivity,
            "recommendations": recommendations,
            "visualizations": visualizations,
            "key_insights": self._extract_key_insights(basic_runway, growth_runway, scenarios)
        }
    
    def _calculate_basic_runway(self, cash_balance: float, 
                               monthly_burn_rate: float,
                               monthly_revenue: float) -> Dict[str, Any]:
        """Базовый расчет runway (без учета роста)"""
        
        net_burn = monthly_burn_rate - monthly_revenue
        
        if net_burn <= 0:
            # Positive cash flow - infinite runway
            runway_months = float('inf')
            cash_out_date = None
            status = "positive_cash_flow"
        else:
            runway_months = cash_balance / net_burn
            cash_out_date = datetime.now() + timedelta(days=runway_months * 30.44)
            status = "burning_cash"
        
        # Категоризация runway
        runway_category = self._categorize_runway(runway_months)
        
        return {
            "net_burn_rate": net_burn,
            "runway_months": runway_months if runway_months != float('inf') else 999,
            "cash_out_date": cash_out_date.isoformat() if cash_out_date else "Never",
            "runway_category": runway_category,
            "status": status,
            "assumptions": "No growth, constant burn rate"
        }
    
    def _calculate_growth_adjusted_runway(self, cash_balance: float,
                                         monthly_burn_rate: float,
                                         monthly_revenue: float,
                                         growth_rate: float) -> Dict[str, Any]:
        """Расчет runway с учетом роста выручки"""
        
        if growth_rate <= 0:
            # Если нет роста, возвращаем базовый расчет
            return self._calculate_basic_runway(cash_balance, monthly_burn_rate, monthly_revenue)
        
        # Симуляция с ростом
        months = 0
        remaining_cash = cash_balance
        current_revenue = monthly_revenue
        projections = []
        
        while remaining_cash > 0 and months < 120:  # Максимум 10 лет
            # Расчет net burn для этого месяца
            net_burn = monthly_burn_rate - current_revenue
            remaining_cash -= net_burn
            
            # Сохраняем projection
            projections.append({
                "month": months + 1,
                "revenue": current_revenue,
                "burn_rate": monthly_burn_rate,
                "net_burn": net_burn,
                "cumulative_cash": max(0, remaining_cash)
            })
            
            # Обновляем для следующего месяца
            current_revenue *= (1 + growth_rate)
            months += 1
            
            if remaining_cash <= 0:
                break
        
        # Расчет точного runway
        if len(projections) > 0:
            if projections[-1]["cumulative_cash"] <= 0:
                # Находим точный месяц, когда закончатся деньги
                if len(projections) >= 2:
                    last_month = projections[-2]
                    this_month = projections[-1]
                    
                    # Интерполяция для точной даты
                    cash_last = last_month["cumulative_cash"]
                    cash_this = this_month["cumulative_cash"]
                    
                    if cash_last > 0 and cash_this < 0:
                        fraction = cash_last / (cash_last - cash_this)
                        exact_months = (len(projections) - 1) + fraction
                    else:
                        exact_months = len(projections)
                else:
                    exact_months = len(projections)
            else:
                exact_months = len(projections)  # Не закончились за симуляционный период
        else:
            exact_months = 0
        
        cash_out_date = datetime.now() + timedelta(days=exact_months * 30.44)
        runway_category = self._categorize_runway(exact_months)
        
        return {
            "runway_months": exact_months,
            "cash_out_date": cash_out_date.isoformat(),
            "runway_category": runway_category,
            "projections": projections[:min(24, len(projections))],  # Ограничиваем 24 месяцами
            "assumptions": f"Monthly revenue growth: {growth_rate*100:.1f}%",
            "months_simulated": len(projections),
            "final_revenue": current_revenue if projections else monthly_revenue,
            "breakeven_possible": any(p["net_burn"] <= 0 for p in projections)
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
    
    def _analyze_scenarios(self, cash_balance: float, monthly_burn_rate: float,
                          monthly_revenue: float, growth_rate: float) -> Dict[str, Any]:
        """Анализ разных сценариев"""
        
        scenarios = {}
        
        # 1. Base Scenario (текущие темпы)
        scenarios["base"] = self._create_scenario(
            name="Base Scenario",
            description="Текущие темпы роста и расходов",
            cash_balance=cash_balance,
            monthly_burn_rate=monthly_burn_rate,
            monthly_revenue=monthly_revenue,
            growth_rate=growth_rate,
            cost_reduction=0,
            revenue_acceleration=0
        )
        
        # 2. Optimistic Scenario (ускоренный рост)
        scenarios["optimistic"] = self._create_scenario(
            name="Optimistic Scenario",
            description="Ускоренный рост выручки на 20%",
            cash_balance=cash_balance,
            monthly_burn_rate=monthly_burn_rate,
            monthly_revenue=monthly_revenue,
            growth_rate=growth_rate * 1.2,
            cost_reduction=0.05,  # 5% cost reduction
            revenue_acceleration=0.20  # 20% revenue acceleration
        )
        
        # 3. Pessimistic Scenario (замедленный рост)
        scenarios["pessimistic"] = self._create_scenario(
            name="Pessimistic Scenario",
            description="Замедленный рост или его отсутствие",
            cash_balance=cash_balance,
            monthly_burn_rate=monthly_burn_rate * 1.1,  # 10% увеличение расходов
            monthly_revenue=monthly_revenue,
            growth_rate=max(0, growth_rate * 0.5),  # 50% снижение роста
            cost_reduction=0,
            revenue_acceleration=0
        )
        
        # 4. Cost Reduction Scenario
        scenarios["cost_reduction"] = self._create_scenario(
            name="Cost Reduction Scenario",
            description="Сокращение расходов на 15%",
            cash_balance=cash_balance,
            monthly_burn_rate=monthly_burn_rate * 0.85,  # 15% reduction
            monthly_revenue=monthly_revenue,
            growth_rate=growth_rate,
            cost_reduction=0.15,
            revenue_acceleration=0
        )
        
        # 5. Fundraising Scenario
        if cash_balance / (monthly_burn_rate - monthly_revenue) < 12:  # Если runway < 12 месяцев
            fundraising_amount = max(monthly_burn_rate * 18, cash_balance * 2)  # 18 месяцев burn или 2x текущего cash
            
            scenarios["fundraising"] = self._create_scenario(
                name="Fundraising Scenario",
                description=f"Привлечение ${fundraising_amount:,.0f} через 6 месяцев",
                cash_balance=cash_balance + fundraising_amount,
                monthly_burn_rate=monthly_burn_rate,
                monthly_revenue=monthly_revenue,
                growth_rate=growth_rate,
                cost_reduction=0,
                revenue_acceleration=0,
                fundraising_timing=6,
                fundraising_amount=fundraising_amount
            )
        
        return scenarios
    
    def _create_scenario(self, name: str, description: str, cash_balance: float,
                        monthly_burn_rate: float, monthly_revenue: float,
                        growth_rate: float, cost_reduction: float,
                        revenue_acceleration: float,
                        fundraising_timing: Optional[int] = None,
                        fundraising_amount: float = 0) -> Dict[str, Any]:
        """Создание сценария"""
        
        # Скорректированные параметры
        adjusted_burn_rate = monthly_burn_rate * (1 - cost_reduction)
        adjusted_growth_rate = growth_rate * (1 + revenue_acceleration)
        
        # Расчет runway
        if growth_rate > 0:
            runway_result = self._calculate_growth_adjusted_runway(
                cash_balance, adjusted_burn_rate, monthly_revenue, adjusted_growth_rate
            )
        else:
            runway_result = self._calculate_basic_runway(
                cash_balance, adjusted_burn_rate, monthly_revenue
            )
        
        # Учет fundraising если предусмотрено
        if fundraising_timing and fundraising_amount > 0:
            runway_months = runway_result["runway_months"]
            if runway_months < fundraising_timing:
                # Fundraising продлевает runway
                extended_runway = fundraising_timing + (fundraising_amount / (adjusted_burn_rate - monthly_revenue))
                runway_result["runway_months"] = extended_runway
                runway_result["cash_out_date"] = (datetime.now() + 
                                                 timedelta(days=extended_runway * 30.44)).isoformat()
                runway_result["runway_category"] = self._categorize_runway(extended_runway)
                runway_result["includes_fundraising"] = True
                runway_result["fundraising_details"] = {
                    "timing_months": fundraising_timing,
                    "amount": fundraising_amount,
                    "extended_runway": extended_runway - runway_months
                }
        
        return {
            "name": name,
            "description": description,
            "assumptions": {
                "monthly_burn_rate": adjusted_burn_rate,
                "growth_rate": adjusted_growth_rate,
                "cost_reduction": cost_reduction,
                "revenue_acceleration": revenue_acceleration,
                "fundraising_timing": fundraising_timing,
                "fundraising_amount": fundraising_amount
            },
            **runway_result
        }
    
    def _perform_sensitivity_analysis(self, cash_balance: float,
                                     monthly_burn_rate: float,
                                     monthly_revenue: float,
                                     growth_rate: float) -> Dict[str, Any]:
        """Анализ чувствительности"""
        
        sensitivity = {
            "burn_rate_impact": [],
            "revenue_impact": [],
            "growth_rate_impact": []
        }
        
        # Анализ чувствительности к burn rate
        for change in [-0.2, -0.1, 0, 0.1, 0.2]:  # -20%, -10%, 0%, +10%, +20%
            adjusted_burn = monthly_burn_rate * (1 + change)
            runway = self._calculate_growth_adjusted_runway(
                cash_balance, adjusted_burn, monthly_revenue, growth_rate
            )
            
            sensitivity["burn_rate_impact"].append({
                "change_percent": change * 100,
                "burn_rate": adjusted_burn,
                "runway_months": runway["runway_months"],
                "runway_change_months": runway["runway_months"] - 
                                       self._calculate_growth_adjusted_runway(
                                           cash_balance, monthly_burn_rate, 
                                           monthly_revenue, growth_rate
                                       )["runway_months"]
            })
        
        # Анализ чувствительности к revenue
        if monthly_revenue > 0:
            for change in [-0.2, -0.1, 0, 0.1, 0.2]:
                adjusted_revenue = monthly_revenue * (1 + change)
                runway = self._calculate_growth_adjusted_runway(
                    cash_balance, monthly_burn_rate, adjusted_revenue, growth_rate
                )
                
                sensitivity["revenue_impact"].append({
                    "change_percent": change * 100,
                    "revenue": adjusted_revenue,
                    "runway_months": runway["runway_months"],
                    "runway_change_months": runway["runway_months"] - 
                                           self._calculate_growth_adjusted_runway(
                                               cash_balance, monthly_burn_rate, 
                                               monthly_revenue, growth_rate
                                           )["runway_months"]
                })
        
        # Анализ чувствительности к growth rate
        if growth_rate > 0:
            for change in [-0.5, -0.25, 0, 0.25, 0.5]:  # -50%, -25%, 0%, +25%, +50%
                adjusted_growth = growth_rate * (1 + change)
                runway = self._calculate_growth_adjusted_runway(
                    cash_balance, monthly_burn_rate, monthly_revenue, adjusted_growth
                )
                
                sensitivity["growth_rate_impact"].append({
                    "change_percent": change * 100,
                    "growth_rate": adjusted_growth,
                    "runway_months": runway["runway_months"],
                    "runway_change_months": runway["runway_months"] - 
                                           self._calculate_growth_adjusted_runway(
                                               cash_balance, monthly_burn_rate, 
                                               monthly_revenue, growth_rate
                                           )["runway_months"]
                })
        
        # Расчет key sensitivities
        sensitivity["key_findings"] = self._extract_sensitivity_insights(sensitivity)
        
        return sensitivity
    
    def _extract_sensitivity_insights(self, sensitivity: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Извлечение инсайтов из анализа чувствительности"""
        
        insights = []
        
        # Анализ burn rate sensitivity
        if sensitivity["burn_rate_impact"]:
            burn_impact = sensitivity["burn_rate_impact"]
            max_impact = max(abs(item["runway_change_months"]) for item in burn_impact)
            
            insights.append({
                "metric": "Burn Rate",
                "sensitivity": "Высокая" if max_impact > 3 else "Умеренная" if max_impact > 1 else "Низкая",
                "impact": f"Изменение burn rate на 10% меняет runway на {abs(burn_impact[2]['runway_change_months']):.1f} месяцев",
                "recommendation": "Тщательно контролировать burn rate" if max_impact > 3 else "Monitor burn rate changes"
            })
        
        # Анализ revenue sensitivity
        if sensitivity["revenue_impact"]:
            revenue_impact = sensitivity["revenue_impact"]
            max_impact = max(abs(item["runway_change_months"]) for item in revenue_impact)
            
            insights.append({
                "metric": "Revenue",
                "sensitivity": "Высокая" if max_impact > 3 else "Умеренная" if max_impact > 1 else "Низкая",
                "impact": f"Увеличение revenue на 10% добавляет {revenue_impact[4]['runway_change_months']:.1f} месяцев runway",
                "recommendation": "Фокусироваться на revenue growth для увеличения runway"
            })
        
        return insights
    
    def _generate_recommendations(self, basic_runway: Dict[str, Any],
                                 growth_runway: Dict[str, Any],
                                 scenarios: Dict[str, Any]) -> Dict[str, Any]:
        """Генерация рекомендаций на основе анализа runway"""
        
        recommendations = {
            "immediate_actions": [],
            "short_term_actions": [],
            "medium_term_actions": [],
            "long_term_actions": []
        }
        
        runway_months = basic_runway["runway_months"]
        runway_category = basic_runway["runway_category"]["category"]
        
        # Рекомендации на основе категории runway
        if runway_category in ["emergency", "critical"]:
            recommendations["immediate_actions"].extend([
                "Сократить burn rate на 20-30% немедленно",
                "Заморозить все non-essential hiring",
                "Перенести или отменить все CAPEX расходы",
                "Начать emergency fundraising process"
            ])
            
            recommendations["short_term_actions"].extend([
                "Рассмотреть bridge financing",
                "Оптимизировать облачные и инфраструктурные расходы",
                "Пересмотреть все контракты и подписки",
                "Фокусироваться только на revenue-generating активностях"
            ])
        
        elif runway_category in ["concerning", "warning"]:
            recommendations["immediate_actions"].extend([
                "Начать подготовку к следующему раунду финансирования",
                "Создать detailed financial plan на 12 месяцев",
                "Оптимизировать marketing spend для улучшения ROI"
            ])
            
            recommendations["short_term_actions"].extend([
                "Рассмотреть revenue-based financing options",
                "Ускорить monetization initiatives",
                "Улучшить cash collection processes",
                "Создать contingency plan на случай delayed fundraising"
            ])
        
        elif runway_category in ["good", "very_good"]:
            recommendations["medium_term_actions"].extend([
                "Использовать runway для стратегических экспериментов",
                "Инвестировать в долгосрочные growth initiatives",
                "Рассчитать optimal fundraising timing",
                "Построить financial model для разных growth scenarios"
            ])
        
        elif runway_category in ["excellent", "infinite"]:
            recommendations["long_term_actions"].extend([
                "Рассмотреть aggressive growth strategies",
                "Инвестировать в team building и culture",
                "Экспериментировать с новыми market segments",
                "Построить sustainable competitive advantages"
            ])
        
        # Общие рекомендации
        general_recommendations = [
            "Ежемесячно пересчитывать runway с актуальными данными",
            "Создать runway dashboard для leadership team",
            "Установить runway triggers для automatic alerts",
            "Интегрировать runway analysis в strategic planning"
        ]
        
        recommendations["general_recommendations"] = general_recommendations
        
        # Рекомендации из анализа сценариев
        if "cost_reduction" in scenarios:
            cost_scenario = scenarios["cost_reduction"]
            if cost_scenario["runway_months"] > runway_months * 1.2:
                recommendations["short_term_actions"].append(
                    f"Cost reduction может увеличить runway на {cost_scenario['runway_months'] - runway_months:.1f} месяцев"
                )
        
        if "optimistic" in scenarios:
            optimistic_scenario = scenarios["optimistic"]
            if optimistic_scenario["runway_months"] > runway_months * 1.3:
                recommendations["medium_term_actions"].append(
                    "Фокусироваться на growth acceleration для значительного увеличения runway"
                )
        
        return recommendations
    
    def _create_visualizations(self, basic_runway: Dict[str, Any],
                              growth_runway: Dict[str, Any],
                              scenarios: Dict[str, Any]) -> Dict[str, Any]:
        """Создание визуализаций для анализа runway"""
        
        visualizations = {}
        
        # 1. Runway Comparison Chart
        fig_comparison = go.Figure()
        
        # Добавляем базовый runway
        fig_comparison.add_trace(go.Bar(
            x=['Basic Runway'],
            y=[basic_runway['runway_months']],
            name='Basic Runway',
            marker_color='blue',
            text=[f"{basic_runway['runway_months']:.1f} мес"],
            textposition='auto'
        ))
        
        # Добавляем growth adjusted runway если отличается
        if growth_runway['runway_months'] != basic_runway['runway_months']:
            fig_comparison.add_trace(go.Bar(
                x=['Growth Adjusted'],
                y=[growth_runway['runway_months']],
                name='With Growth',
                marker_color='green',
                text=[f"{growth_runway['runway_months']:.1f} мес"],
                textposition='auto'
            ))
        
        # Добавляем сценарии
        scenario_names = []
        scenario_runways = []
        
        for name, scenario in scenarios.items():
            scenario_names.append(name.replace('_', ' ').title())
            scenario_runways.append(scenario['runway_months'])
        
        if scenario_names:
            fig_comparison.add_trace(go.Bar(
                x=scenario_names,
                y=scenario_runways,
                name='Scenarios',
                marker_color='orange',
                text=[f"{r:.1f} мес" for r in scenario_runways],
                textposition='auto'
            ))
        
        fig_comparison.update_layout(
            title='Runway Comparison',
            yaxis_title='Months of Runway',
            showlegend=True,
            height=400
        )
        
        visualizations['runway_comparison'] = fig_comparison
        
        # 2. Cash Burn Projection
        if 'projections' in growth_runway and growth_runway['projections']:
            projections = growth_runway['projections']
            months = [p['month'] for p in projections]
            cash_balance = [p['cumulative_cash'] for p in projections]
            revenue = [p['revenue'] for p in projections]
            
            fig_cash = go.Figure()
            
            fig_cash.add_trace(go.Scatter(
                x=months,
                y=cash_balance,
                mode='lines+markers',
                name='Cash Balance',
                line=dict(color='blue', width=3)
            ))
            
            fig_cash.add_trace(go.Scatter(
                x=months,
                y=revenue,
                mode='lines',
                name='Monthly Revenue',
                line=dict(color='green', dash='dash')
            ))
            
            # Добавляем линию нуля
            fig_cash.add_hline(y=0, line_dash="dot", line_color="red", 
                             annotation_text="Cash Out", annotation_position="bottom right")
            
            fig_cash.update_layout(
                title='Cash Balance Projection',
                xaxis_title='Months',
                yaxis_title='Amount',
                height=400
            )
            
            visualizations['cash_projection'] = fig_cash
        
        # 3. Runway Sensitivity Heatmap
        # (Можно добавить если есть данные sensitivity analysis)
        
        return visualizations
    
    def _extract_key_insights(self, basic_runway: Dict[str, Any],
                             growth_runway: Dict[str, Any],
                             scenarios: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Извлечение ключевых инсайтов"""
        
        insights = []
        
        # Основной insight о runway
        runway_months = basic_runway['runway_months']
        category = basic_runway['runway_category']
        
        insights.append({
            "type": "runway_status",
            "title": f"Runway: {runway_months:.1f} месяцев",
            "description": category['description'],
            "severity": category['category'],
            "recommendation": "Следить за burn rate и revenue growth"
        })
        
        # Insight о влиянии роста
        if growth_runway['runway_months'] != runway_months:
            growth_impact = growth_runway['runway_months'] - runway_months
            insights.append({
                "type": "growth_impact",
                "title": f"Рост увеличивает runway на {growth_impact:.1f} месяцев",
                "description": f"При росте {growth_runway['assumptions'].split(': ')[1]}",
                "severity": "positive",
                "recommendation": "Фокусироваться на revenue growth"
            })
        
        # Insight из лучшего сценария
        if scenarios:
            best_scenario = max(scenarios.values(), key=lambda x: x['runway_months'])
            worst_scenario = min(scenarios.values(), key=lambda x: x['runway_months'])
            
            insights.append({
                "type": "scenario_range",
                "title": f"Runway range: {worst_scenario['runway_months']:.1f} - {best_scenario['runway_months']:.1f} месяцев",
                "description": f"Лучший сценарий: {best_scenario['name']}, худший: {worst_scenario['name']}",
                "severity": "info",
                "recommendation": "Готовиться к worst case, стремиться к best case"
            })
        
        # Insight о breakeven possibility
        if 'breakeven_possible' in growth_runway and growth_runway['breakeven_possible']:
            insights.append({
                "type": "breakeven_possible",
                "title": "Достижение breakeven возможно",
                "description": "При текущих темпах роста компания может достичь profitability",
                "severity": "positive",
                "recommendation": "Фокусироваться на ускорении пути к profitability"
            })
        
        return insights
    
    def calculate_fundraising_timing(self, current_runway: float, 
                                    fundraising_process_months: float = 6.0,
                                    buffer_months: float = 3.0) -> Dict[str, Any]:
        """
        Расчет оптимального времени для начала fundraising
        
        Args:
            current_runway: Текущий runway в месяцах
            fundraising_process_months: Время на fundraising process (месяцы)
            buffer_months: Безопасный buffer (месяцы)
        
        Returns:
            Dict с расчетами timing
        """
        
        # Оптимальное время для начала fundraising
        optimal_start = current_runway - fundraising_process_months - buffer_months
        
        # Категоризация timing
        if optimal_start <= 0:
            timing_status = "late"
            timing_description = "Уже поздно начинать, нужно emergency fundraising"
            action = "Немедленно начинать emergency fundraising process"
        elif optimal_start <= 3:
            timing_status = "urgent"
            timing_description = "Срочно нужно начинать fundraising"
            action = "Начать fundraising process в этом месяце"
        elif optimal_start <= 6:
            timing_status = "soon"
            timing_description = "Нужно начинать fundraising в ближайшие месяцы"
            action = "Начать подготовку, начать process через 1-2 месяца"
        else:
            timing_status = "planned"
            timing_description = "Есть время для planned fundraising"
            action = "Начать подготовку, планировать начало через несколько месяцев"
        
        # Рекомендуемые шаги
        if timing_status in ["late", "urgent"]:
            steps = [
                "Немедленно подготовить pitch deck",
                "Начать outreach к инвесторам",
                "Рассмотреть bridge financing options",
                "Сократить расходы для увеличения runway"
            ]
        elif timing_status == "soon":
            steps = [
                "Подготовить pitch deck в течение 2 недель",
                "Составить список target investors",
                "Начать building relationships",
                "Подготовить financial model"
            ]
        else:
            steps = [
                "Начать подготовку materials за 3 месяца до начала",
                "Build relationships with investors",
                "Улучшить key metrics перед fundraising",
                "Создать detailed fundraising plan"
            ]
        
        return {
            "current_runway_months": current_runway,
            "fundraising_process_months": fundraising_process_months,
            "buffer_months": buffer_months,
            "optimal_start_months": max(0, optimal_start),
            "timing_status": timing_status,
            "timing_description": timing_description,
            "recommended_action": action,
            "next_steps": steps,
            "critical_date": datetime.now() + timedelta(days=optimal_start * 30.44) if optimal_start > 0 else datetime.now()
        }
    
    def create_runway_dashboard(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Создание комплексного dashboard для runway analysis
        
        Args:
            company_data: Данные компании
        
        Returns:
            Dict с dashboard данными
        """
        
        # Извлекаем данные компании
        cash_balance = company_data.get("cash_balance", 0)
        monthly_burn = company_data.get("monthly_burn_rate", 0)
        monthly_revenue = company_data.get("current_mrr", 0)
        growth_rate = company_data.get("growth_rate_monthly", 0.1)
        
        # Основной расчет runway
        runway_analysis = self.calculate_runway(
            cash_balance, monthly_burn, monthly_revenue, growth_rate, include_scenarios=True
        )
        
        # Расчет fundraising timing
        current_runway = runway_analysis["basic_runway"]["runway_months"]
        fundraising_timing = self.calculate_fundraising_timing(current_runway)
        
        # Создание dashboard
        dashboard = {
            "summary_metrics": {
                "current_runway": current_runway,
                "runway_category": runway_analysis["basic_runway"]["runway_category"]["label"],
                "cash_balance": cash_balance,
                "monthly_net_burn": monthly_burn - monthly_revenue,
                "months_to_fundraising_start": fundraising_timing["optimal_start_months"],
                "fundraising_timing_status": fundraising_timing["timing_status"]
            },
            "alert_level": self._determine_alert_level(runway_analysis, fundraising_timing),
            "key_actions": self._prioritize_actions(runway_analysis, fundraising_timing),
            "monitoring_metrics": [
                {"metric": "Cash Balance", "frequency": "daily", "threshold": cash_balance * 0.8},
                {"metric": "Monthly Burn Rate", "frequency": "weekly", "threshold": monthly_burn * 1.1},
                {"metric": "Monthly Revenue", "frequency": "weekly", "threshold": monthly_revenue * 0.9},
                {"metric": "Runway", "frequency": "monthly", "threshold": 6}
            ],
            "scenario_planning": self._create_scenario_planning(runway_analysis["scenarios"])
        }
        
        return dashboard
    
    def _determine_alert_level(self, runway_analysis: Dict[str, Any],
                              fundraising_timing: Dict[str, Any]) -> Dict[str, Any]:
        """Определение уровня alert на основе анализа"""
        
        runway_category = runway_analysis["basic_runway"]["runway_category"]["category"]
        timing_status = fundraising_timing["timing_status"]
        
        # Определяем общий alert level
        if runway_category in ["emergency", "critical"] or timing_status in ["late", "urgent"]:
            alert_level = "red"
            message = "🚨 CRITICAL: Immediate action required"
            actions = ["Emergency cost reduction", "Immediate fundraising", "Board meeting"]
        
        elif runway_category in ["concerning", "warning"] or timing_status == "soon":
            alert_level = "orange"
            message = "⚠️ WARNING: Action needed soon"
            actions = ["Start fundraising prep", "Cost optimization", "Financial review"]
        
        elif runway_category in ["good", "very_good"] or timing_status == "planned":
            alert_level = "yellow"
            message = "ℹ️ INFO: Monitor and plan"
            actions = ["Plan fundraising timing", "Optimize growth", "Strategic planning"]
        
        else:
            alert_level = "green"
            message = "✅ GOOD: Healthy runway"
            actions = ["Growth acceleration", "Strategic investments", "Long-term planning"]
        
        return {
            "level": alert_level,
            "message": message,
            "required_actions": actions,
            "next_review_date": (datetime.now() + timedelta(days=7)).isoformat()
        }
    
    def _prioritize_actions(self, runway_analysis: Dict[str, Any],
                           fundraising_timing: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Приоритизация действий на основе анализа"""
        
        actions = []
        
        # Добавляем действия из runway recommendations
        for priority, items in runway_analysis["recommendations"].items():
            if priority != "general_recommendations":
                for item in items:
                    actions.append({
                        "action": item,
                        "priority": priority.replace("_actions", ""),
                        "source": "runway_analysis",
                        "estimated_impact": "high" if "critical" in item.lower() else "medium"
                    })
        
        # Добавляем действия из fundraising timing
        for step in fundraising_timing.get("next_steps", []):
            actions.append({
                "action": step,
                "priority": "high" if fundraising_timing["timing_status"] in ["late", "urgent"] else "medium",
                "source": "fundraising_timing",
                "estimated_impact": "high"
            })
        
        # Сортируем по приоритету
        priority_order = {"immediate": 1, "short_term": 2, "medium_term": 3, "long_term": 4}
        actions.sort(key=lambda x: priority_order.get(x["priority"], 5))
        
        return actions[:5]  # Возвращаем топ-5 действий
    
    def _create_scenario_planning(self, scenarios: Dict[str, Any]) -> Dict[str, Any]:
        """Создание planning для разных сценариев"""
        
        scenario_plans = {}
        
        for name, scenario in scenarios.items():
            scenario_plans[name] = {
                "runway_months": scenario["runway_months"],
                "key_assumptions": scenario["assumptions"],
                "trigger_events": self._identify_scenario_triggers(scenario),
                "mitigation_strategies": self._suggest_scenario_mitigations(scenario),
                "monitoring_indicators": self._define_scenario_indicators(scenario)
            }
        
        return scenario_plans
    
    def _identify_scenario_triggers(self, scenario: Dict[str, Any]) -> List[str]:
        """Идентификация trigger events для сценария"""
        
        triggers = []
        
        if "cost_reduction" in scenario["assumptions"] and scenario["assumptions"]["cost_reduction"] > 0:
            triggers.append(f"Cost reduction of {scenario['assumptions']['cost_reduction']*100:.0f}% achieved")
        
        if "revenue_acceleration" in scenario["assumptions"] and scenario["assumptions"]["revenue_acceleration"] > 0:
            triggers.append(f"Revenue acceleration of {scenario['assumptions']['revenue_acceleration']*100:.0f}% achieved")
        
        if "fundraising_amount" in scenario["assumptions"] and scenario["assumptions"]["fundraising_amount"] > 0:
            triggers.append(f"Fundraising of ${scenario['assumptions']['fundraising_amount']:,.0f} completed")
        
        return triggers
    
    def _suggest_scenario_mitigations(self, scenario: Dict[str, Any]) -> List[str]:
        """Предложение mitigation strategies для сценария"""
        
        mitigations = []
        scenario_name = scenario["name"].lower()
        
        if "pessimistic" in scenario_name:
            mitigations.extend([
                "Build cash reserves",
                "Diversify revenue streams",
                "Establish lines of credit",
                "Reduce fixed costs"
            ])
        
        elif "optimistic" in scenario_name:
            mitigations.extend([
                "Invest in growth opportunities",
                "Build team capacity",
                "Expand market reach",
                "Accelerate product development"
            ])
        
        return mitigations
    
    def _define_scenario_indicators(self, scenario: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Определение indicators для мониторинга сценария"""
        
        indicators = []
        
        if "growth_rate" in scenario["assumptions"]:
            indicators.append({
                "metric": "Monthly Revenue Growth",
                "target": scenario["assumptions"]["growth_rate"],
                "frequency": "monthly",
                "threshold": scenario["assumptions"]["growth_rate"] * 0.8  # 80% of target
            })
        
        if "cost_reduction" in scenario["assumptions"]:
            indicators.append({
                "metric": "Monthly Burn Rate",
                "target": scenario["assumptions"]["monthly_burn_rate"],
                "frequency": "monthly",
                "threshold": scenario["assumptions"]["monthly_burn_rate"] * 1.1  # 10% above target
            })
        
        return indicators

# Создаем глобальный экземпляр калькулятора
runway_calculator = RunwayCalculator()

# Экспортируем полезные функции
def calculate_company_runway(company_data: Dict[str, Any]) -> Dict[str, Any]:
    """Публичная функция для расчета runway компании"""
    cash_balance = company_data.get("cash_balance", 0)
    monthly_burn = company_data.get("monthly_burn_rate", 0)
    monthly_revenue = company_data.get("current_mrr", 0)
    growth_rate = company_data.get("growth_rate_monthly", 0.1)
    
    return runway_calculator.calculate_runway(
        cash_balance, monthly_burn, monthly_revenue, growth_rate, include_scenarios=True
    )

def get_fundraising_timing_advice(current_runway: float) -> Dict[str, Any]:
    """Публичная функция для получения советов по timing fundraising"""
    return runway_calculator.calculate_fundraising_timing(current_runway)

def create_runway_dashboard_data(company_data: Dict[str, Any]) -> Dict[str, Any]:
    """Публичная функция для создания runway dashboard"""
    return runway_calculator.create_runway_dashboard(company_data)