"""
Анализатор отклонений между планом и фактом
Автоматическое выявление причин отклонений и рекомендации
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import plotly.graph_objects as go
from scipy import stats

@dataclass
class VarianceAnalysis:
    """Анализ отклонений"""
    metric: str
    category: str
    planned_value: float
    actual_value: float
    variance_amount: float
    variance_percent: float
    significance: str  # low, medium, high, critical
    root_causes: List[str]
    impact_description: str
    recommendations: List[str]

class VarianceAnalyzer:
    """
    Анализатор отклонений для SaaS метрик
    Сравнивает план с фактом, выявляет root causes, дает рекомендации
    """
    
    def __init__(self):
        self.variance_thresholds = {
            "revenue": 0.10,  # 10%
            "customers": 0.15,  # 15%
            "cac": 0.25,  # 25%
            "churn": 0.30,  # 30%
            "burn_rate": 0.20,  # 20%
            "ltv_cac": 0.35,  # 35%
            "runway": 0.25,  # 25%
        }
        
        self.metric_categories = {
            "revenue": ["plan_total_revenue", "plan_mrr", "plan_new_customers", "plan_expansion_mrr"],
            "costs": ["plan_total_costs", "plan_salaries", "plan_marketing_budget", "plan_cloud_services"],
            "efficiency": ["plan_ltv_cac_ratio", "plan_cac_payback_months", "plan_gross_margin"],
            "cash": ["plan_burn_rate", "plan_runway", "plan_cumulative_cash"]
        }
        
    def analyze_variance(self, planned_data: List[Dict[str, Any]], 
                        actual_data: List[Dict[str, Any]],
                        company_stage: str = "pre_seed") -> Dict[str, Any]:
        """
        Анализ отклонений между планом и фактом
        
        Args:
            planned_data: Запланированные данные по месяцам
            actual_data: Фактические данные по месяцам
            company_stage: Стадия компании для контекста
        
        Returns:
            Dict с анализом отклонений
        """
        
        # Подготовка данных
        aligned_data = self._align_data(planned_data, actual_data)
        
        # Анализ отклонений по метрикам
        variance_analysis = self._calculate_variances(aligned_data)
        
        # Определение значимости отклонений
        significant_variances = self._identify_significant_variances(
            variance_analysis, company_stage
        )
        
        # Анализ root causes
        root_cause_analysis = self._analyze_root_causes(significant_variances, aligned_data)
        
        # Генерация рекомендаций
        recommendations = self._generate_recommendations(root_cause_analysis, company_stage)
        
        # Анализ трендов
        trend_analysis = self._analyze_trends(aligned_data)
        
        # Создание dashboard
        variance_dashboard = self._create_variance_dashboard(
            aligned_data, variance_analysis, significant_variances
        )
        
        return {
            "analysis_date": datetime.now().isoformat(),
            "period_analyzed": f"{len(aligned_data)} месяцев",
            "data_alignment_status": "complete" if len(aligned_data) > 0 else "partial",
            "variance_summary": self._create_variance_summary(variance_analysis),
            "significant_variances": significant_variances,
            "root_cause_analysis": root_cause_analysis,
            "recommendations": recommendations,
            "trend_analysis": trend_analysis,
            "dashboard": variance_dashboard,
            "key_insights": self._extract_key_insights(significant_variances, trend_analysis)
        }
    
    def _align_data(self, planned_data: List[Dict], actual_data: List[Dict]) -> List[Dict]:
        """Выравнивание плановых и фактических данных по месяцам"""
        
        aligned = []
        
        # Создаем словарь фактических данных по месяцам
        actual_by_month = {}
        for actual in actual_data:
            month_key = (actual.get('year'), actual.get('month_number'))
            if month_key:
                actual_by_month[month_key] = actual
        
        # Сопоставляем с плановыми данными
        for planned in planned_data:
            month_key = (planned.get('year'), planned.get('month_number'))
            
            if month_key in actual_by_month:
                aligned.append({
                    'month': month_key,
                    'month_name': planned.get('month_name', f'Месяц {planned.get("month_number")}'),
                    'planned': planned,
                    'actual': actual_by_month[month_key],
                    'has_actual': True
                })
            else:
                aligned.append({
                    'month': month_key,
                    'month_name': planned.get('month_name', f'Месяц {planned.get("month_number")}'),
                    'planned': planned,
                    'actual': None,
                    'has_actual': False
                })
        
        return aligned
    
    def _calculate_variances(self, aligned_data: List[Dict]) -> List[Dict[str, Any]]:
        """Расчет отклонений для каждого месяца и метрики"""
        
        variances = []
        
        for data in aligned_data:
            if not data['has_actual']:
                continue
            
            planned = data['planned']
            actual = data['actual']
            
            # Анализируем ключевые метрики
            metrics_to_analyze = self._get_metrics_to_analyze(planned, actual)
            
            for metric in metrics_to_analyze:
                planned_value = planned.get(metric)
                actual_value = actual.get(metric)
                
                # Пропускаем если данные отсутствуют
                if planned_value is None or actual_value is None:
                    continue
                
                # Пропускаем если значения нулевые (кроме когда это проблема)
                if planned_value == 0 and actual_value == 0:
                    continue
                
                # Расчет отклонений
                variance_amount = actual_value - planned_value
                
                if planned_value != 0:
                    variance_percent = (variance_amount / abs(planned_value)) * 100
                else:
                    variance_percent = 100 if actual_value > 0 else 0
                
                # Определение категории метрики
                metric_category = self._categorize_metric(metric)
                
                variances.append({
                    'month': data['month_name'],
                    'month_number': planned.get('month_number'),
                    'metric': metric,
                    'category': metric_category,
                    'planned': planned_value,
                    'actual': actual_value,
                    'variance_amount': variance_amount,
                    'variance_percent': variance_percent,
                    'absolute_variance_percent': abs(variance_percent)
                })
        
        return variances
    
    def _get_metrics_to_analyze(self, planned: Dict, actual: Dict) -> List[str]:
        """Получение списка метрик для анализа"""
        
        # Основные метрики
        base_metrics = [
            'plan_total_revenue', 'plan_mrr', 'plan_new_customers',
            'plan_total_costs', 'plan_burn_rate', 'plan_runway',
            'plan_ltv_cac_ratio', 'plan_cac_payback_months', 'plan_gross_margin'
        ]
        
        # Проверяем какие метрики есть в обоих наборах данных
        available_metrics = []
        for metric in base_metrics:
            if metric in planned and metric in actual:
                if planned[metric] is not None and actual[metric] is not None:
                    available_metrics.append(metric)
        
        return available_metrics
    
    def _categorize_metric(self, metric: str) -> str:
        """Категоризация метрики"""
        
        for category, metrics in self.metric_categories.items():
            if metric in metrics:
                return category
        
        # Определяем по названию
        if 'revenue' in metric.lower() or 'mrr' in metric.lower():
            return 'revenue'
        elif 'cost' in metric.lower() or 'budget' in metric.lower() or 'salary' in metric.lower():
            return 'costs'
        elif 'cac' in metric.lower() or 'ltv' in metric.lower() or 'margin' in metric.lower():
            return 'efficiency'
        elif 'burn' in metric.lower() or 'runway' in metric.lower() or 'cash' in metric.lower():
            return 'cash'
        else:
            return 'other'
    
    def _identify_significant_variances(self, variances: List[Dict], 
                                       company_stage: str) -> List[Dict]:
        """Идентификация значимых отклонений"""
        
        significant = []
        
        for variance in variances:
            metric = variance['metric']
            variance_percent = variance['absolute_variance_percent']
            
            # Получаем threshold для метрики
            threshold = self._get_variance_threshold(metric, company_stage)
            
            # Определяем значимость
            if variance_percent > threshold * 2:
                significance = 'critical'
            elif variance_percent > threshold * 1.5:
                significance = 'high'
            elif variance_percent > threshold:
                significance = 'medium'
            else:
                significance = 'low'
            
            # Для некоторых метрик significance определяется по-другому
            if metric == 'plan_runway':
                # Для runway отклонение в меньшую сторону критично
                if variance['variance_amount'] < -3:  # Runway сократился на 3+ месяца
                    significance = 'critical' if variance_percent > 30 else 'high'
            
            # Для burn rate отклонение в большую сторону критично
            if metric == 'plan_burn_rate' and variance['variance_amount'] > 0:
                significance = max(significance, 'medium')
            
            if significance in ['medium', 'high', 'critical']:
                variance['significance'] = significance
                significant.append(variance)
        
        return significant
    
    def _get_variance_threshold(self, metric: str, company_stage: str) -> float:
        """Получение threshold для отклонения"""
        
        # Базовые thresholds
        base_threshold = self.variance_thresholds.get(
            self._get_metric_category_key(metric), 0.20
        )
        
        # Корректировка по стадии компании
        stage_adjustments = {
            'pre_seed': 1.5,  # На pre-seed отклонения более ожидаемы
            'seed': 1.3,
            'series_a': 1.1,
            'series_b': 1.0,
            'growth': 0.9,
            'mature': 0.8
        }
        
        adjustment = stage_adjustments.get(company_stage, 1.0)
        
        return base_threshold * adjustment
    
    def _get_metric_category_key(self, metric: str) -> str:
        """Получение ключа категории для метрики"""
        
        if 'revenue' in metric or 'mrr' in metric or 'customer' in metric:
            return 'revenue'
        elif 'cac' in metric:
            return 'cac'
        elif 'churn' in metric:
            return 'churn'
        elif 'burn' in metric:
            return 'burn_rate'
        elif 'ltv' in metric or 'margin' in metric:
            return 'ltv_cac'
        elif 'runway' in metric:
            return 'runway'
        else:
            return 'other'
    
    def _analyze_root_causes(self, significant_variances: List[Dict],
                            aligned_data: List[Dict]) -> List[Dict[str, Any]]:
        """Анализ root causes для значимых отклонений"""
        
        root_causes = []
        
        # Группируем отклонения по месяцам
        variances_by_month = {}
        for variance in significant_variances:
            month = variance['month']
            if month not in variances_by_month:
                variances_by_month[month] = []
            variances_by_month[month].append(variance)
        
        # Анализируем каждый месяц с отклонениями
        for month, month_variances in variances_by_month.items():
            month_data = next((d for d in aligned_data if d['month_name'] == month), None)
            
            if not month_data or not month_data['has_actual']:
                continue
            
            planned = month_data['planned']
            actual = month_data['actual']
            
            # Анализ взаимосвязей между отклонениями
            causes = self._find_interconnected_causes(month_variances, planned, actual)
            
            # Анализ внешних факторов
            external_factors = self._identify_external_factors(month_variances, planned, actual)
            
            # Анализ execution quality
            execution_issues = self._analyze_execution_quality(month_variances, planned, actual)
            
            month_root_causes = {
                'month': month,
                'month_number': month_data['planned'].get('month_number'),
                'significant_variances_count': len(month_variances),
                'primary_causes': causes,
                'external_factors': external_factors,
                'execution_issues': execution_issues,
                'most_critical_variance': max(month_variances, 
                                             key=lambda x: 3 if x['significance'] == 'critical' 
                                                           else 2 if x['significance'] == 'high'
                                                           else 1)
            }
            
            root_causes.append(month_root_causes)
        
        return root_causes
    
    def _find_interconnected_causes(self, variances: List[Dict], 
                                   planned: Dict, actual: Dict) -> List[str]:
        """Поиск взаимосвязанных причин отклонений"""
        
        causes = []
        
        # Проверяем связанные метрики
        variance_metrics = [v['metric'] for v in variances]
        
        # Если отклонения в revenue и новых клиентах
        if ('plan_total_revenue' in variance_metrics and 
            'plan_new_customers' in variance_metrics):
            
            revenue_variance = next(v for v in variances if v['metric'] == 'plan_total_revenue')
            customers_variance = next(v for v in variances if v['metric'] == 'plan_new_customers')
            
            # Анализируем relationship
            planned_arpu = planned['plan_total_revenue'] / planned['plan_new_customers'] if planned['plan_new_customers'] > 0 else 0
            actual_arpu = actual['plan_total_revenue'] / actual['plan_new_customers'] if actual['plan_new_customers'] > 0 else 0
            
            if abs(actual_arpu - planned_arpu) / planned_arpu > 0.2:
                causes.append("Изменение средней цены (ARPU) на клиента")
            else:
                causes.append("Проблемы с customer acquisition")
        
        # Если отклонения в CAC и новых клиентах
        if ('plan_marketing_budget' in variance_metrics and 
            'plan_new_customers' in variance_metrics):
            
            cac_variance = next(v for v in variances if v['metric'] == 'plan_marketing_budget')
            customers_variance = next(v for v in variances if v['metric'] == 'plan_new_customers')
            
            planned_cac = planned['plan_marketing_budget'] / planned['plan_new_customers'] if planned['plan_new_customers'] > 0 else 0
            actual_cac = actual['plan_marketing_budget'] / actual['plan_new_customers'] if actual['plan_new_customers'] > 0 else 0
            
            if actual_cac > planned_cac * 1.5:
                causes.append("Ухудшение эффективности маркетинга (CAC увеличен)")
            elif actual_cac < planned_cac * 0.7:
                causes.append("Улучшение эффективности маркетинга (CAC снижен)")
        
        # Если отклонения в burn rate и revenue
        if ('plan_burn_rate' in variance_metrics and 
            'plan_total_revenue' in variance_metrics):
            
            burn_variance = next(v for v in variances if v['metric'] == 'plan_burn_rate')
            revenue_variance = next(v for v in variances if v['metric'] == 'plan_total_revenue')
            
            if (burn_variance['variance_amount'] > 0 and 
                revenue_variance['variance_amount'] < 0):
                causes.append("Рост расходов при снижении выручки")
            elif (burn_variance['variance_amount'] > 0 and 
                  revenue_variance['variance_amount'] > 0):
                causes.append("Инвестиционный рост (расходы растут быстрее выручки)")
        
        return causes
    
    def _identify_external_factors(self, variances: List[Dict], 
                                  planned: Dict, actual: Dict) -> List[str]:
        """Идентификация внешних факторов"""
        
        factors = []
        
        # Анализируем seasonality impact
        month_number = planned.get('month_number')
        if month_number in [7, 8]:  # Июль-Август
            # Проверяем отклонения в revenue
            revenue_variances = [v for v in variances if 'revenue' in v['metric'].lower() 
                                or 'customer' in v['metric'].lower()]
            if revenue_variances and any(v['variance_amount'] < 0 for v in revenue_variances):
                factors.append("Сезонность: летний спад активности")
        
        # Проверяем макро-факторы через значительные отклонения
        critical_variances = [v for v in variances if v['significance'] in ['high', 'critical']]
        
        if len(critical_variances) >= 3:
            # Если много критических отклонений - возможны внешние факторы
            factors.append("Возможное влияние рыночных или экономических факторов")
        
        # Анализируем churn если есть данные
        if 'plan_churn_rate' in actual and 'plan_churn_rate' in planned:
            churn_change = actual['plan_churn_rate'] - planned['plan_churn_rate']
            if churn_change > 0.02:  # Увеличение churn на 2%
                factors.append("Рост оттока клиентов")
        
        return factors
    
    def _analyze_execution_quality(self, variances: List[Dict], 
                                  planned: Dict, actual: Dict) -> List[str]:
        """Анализ качества исполнения"""
        
        issues = []
        
        # Проверяем execution по разным категориям
        
        # Revenue execution
        revenue_variances = [v for v in variances if v['category'] == 'revenue']
        if revenue_variances:
            negative_revenue = [v for v in revenue_variances if v['variance_amount'] < 0]
            if len(negative_revenue) > len(revenue_variances) * 0.5:
                issues.append("Слабые результаты в revenue generation")
        
        # Cost control
        cost_variances = [v for v in variances if v['category'] == 'costs']
        if cost_variances:
            positive_costs = [v for v in cost_variances if v['variance_amount'] > 0]
            if len(positive_costs) > len(cost_variances) * 0.7:
                issues.append("Проблемы с контролем расходов")
        
        # CAC efficiency
        cac_metrics = [v for v in variances if 'cac' in v['metric'].lower()]
        if cac_metrics:
            cac_variance = cac_metrics[0]
            if cac_variance['variance_amount'] > 0 and cac_variance['variance_percent'] > 20:
                issues.append("Снижение эффективности customer acquisition")
        
        return issues
    
    def _generate_recommendations(self, root_cause_analysis: List[Dict],
                                 company_stage: str) -> Dict[str, List[str]]:
        """Генерация рекомендаций на основе анализа root causes"""
        
        recommendations = {
            "immediate": [],
            "short_term": [],
            "long_term": []
        }
        
        # Анализируем root causes
        for analysis in root_cause_analysis:
            causes = analysis.get('primary_causes', [])
            external_factors = analysis.get('external_factors', [])
            execution_issues = analysis.get('execution_issues', [])
            
            # Генерация рекомендаций на основе causes
            for cause in causes:
                if "цена" in cause.lower() or "arpu" in cause.lower():
                    recommendations["immediate"].append(
                        "Проанализировать pricing strategy и value proposition"
                    )
                elif "acquisition" in cause.lower() or "cac" in cause.lower():
                    recommendations["short_term"].append(
                        "Пересмотреть маркетинговые каналы и оптимизировать CAC"
                    )
                elif "расходы" in cause.lower() or "рост расходов" in cause.lower():
                    recommendations["immediate"].append(
                        "Провести review расходов и сократить non-essential costs"
                    )
            
            # Рекомендации на основе external factors
            for factor in external_factors:
                if "сезонность" in factor.lower():
                    recommendations["long_term"].append(
                        "Скорректировать план с учетом сезонности"
                    )
                elif "рыноч" in factor.lower():
                    recommendations["short_term"].append(
                        "Провести анализ market conditions и адаптировать strategy"
                    )
            
            # Рекомендации на основе execution issues
            for issue in execution_issues:
                if "результаты" in issue.lower() or "revenue" in issue.lower():
                    recommendations["immediate"].append(
                        "Усилить sales и marketing execution"
                    )
                elif "расход" in issue.lower() or "контроль" in issue.lower():
                    recommendations["immediate"].append(
                        "Внедрить stricter budget controls и approval processes"
                    )
        
        # Убираем дубликаты
        for key in recommendations:
            recommendations[key] = list(set(recommendations[key]))
        
        # Добавляем stage-specific рекомендации
        stage_recommendations = self._get_stage_specific_recommendations(company_stage)
        recommendations["long_term"].extend(stage_recommendations)
        
        return recommendations
    
    def _get_stage_specific_recommendations(self, stage: str) -> List[str]:
        """Получение stage-specific рекомендаций"""
        
        recommendations = {
            "pre_seed": [
                "Фокусироваться на product-market fit, а не на масштабировании",
                "Собирать больше customer feedback для корректировки плана",
                "Быть готовым к частым корректировкам плана"
            ],
            "seed": [
                "Оптимизировать unit economics перед масштабированием",
                "Построить repeatable sales process",
                "Начать готовиться к Series A fundraising"
            ],
            "series_a": [
                "Масштабировать проверенные модели роста",
                "Инвестировать в team building и процессы",
                "Фокусироваться на sustainable growth"
            ],
            "series_b": [
                "Оптимизировать operational efficiency",
                "Диверсифицировать revenue streams",
                "Готовиться к profitability или следующему раунду"
            ]
        }
        
        return recommendations.get(stage, [])
    
    def _analyze_trends(self, aligned_data: List[Dict]) -> Dict[str, Any]:
        """Анализ трендов отклонений"""
        
        if len(aligned_data) < 3:
            return {"insufficient_data": True}
        
        # Подготавливаем данные для трендового анализа
        monthly_variances = []
        
        for data in aligned_data:
            if not data['has_actual']:
                continue
            
            planned = data['planned']
            actual = data['actual']
            
            # Рассчитываем aggregate variance
            key_metrics = ['plan_total_revenue', 'plan_total_costs', 
                          'plan_burn_rate', 'plan_new_customers']
            
            total_variance = 0
            metric_count = 0
            
            for metric in key_metrics:
                if metric in planned and metric in actual:
                    planned_val = planned[metric]
                    actual_val = actual[metric]
                    
                    if planned_val != 0:
                        variance = abs(actual_val - planned_val) / abs(planned_val)
                        total_variance += variance
                        metric_count += 1
            
            if metric_count > 0:
                avg_variance = total_variance / metric_count
                monthly_variances.append({
                    'month': data['month_name'],
                    'month_number': data['planned'].get('month_number'),
                    'avg_variance_percent': avg_variance * 100
                })
        
        # Анализ тренда
        if len(monthly_variances) >= 3:
            variances = [v['avg_variance_percent'] for v in monthly_variances]
            
            # Проверяем улучшается ли accuracy со временем
            x = range(len(variances))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, variances)
            
            trend = "improving" if slope < -1 else "worsening" if slope > 1 else "stable"
            trend_strength = abs(slope) * 10
            
            # Анализ volatility
            volatility = np.std(variances)
            
            return {
                "trend_direction": trend,
                "trend_strength": trend_strength,
                "volatility": volatility,
                "avg_variance": np.mean(variances),
                "recent_trend": self._analyze_recent_trend(variances),
                "monthly_data": monthly_variances
            }
        
        return {"insufficient_data": True}
    
    def _analyze_recent_trend(self, variances: List[float]) -> str:
        """Анализ recent trend (последние 3 месяца)"""
        
        if len(variances) < 3:
            return "insufficient_data"
        
        recent = variances[-3:]
        
        # Проверяем тренд
        if recent[0] > recent[1] > recent[2]:
            return "improving"
        elif recent[0] < recent[1] < recent[2]:
            return "worsening"
        else:
            # Проверяем среднее
            avg_recent = np.mean(recent)
            avg_previous = np.mean(variances[:-3]) if len(variances) > 3 else avg_recent
            
            if avg_recent < avg_previous * 0.8:
                return "improving"
            elif avg_recent > avg_previous * 1.2:
                return "worsening"
            else:
                return "stable"
    
    def _create_variance_dashboard(self, aligned_data: List[Dict],
                                  variance_analysis: List[Dict],
                                  significant_variances: List[Dict]) -> Dict[str, Any]:
        """Создание dashboard для анализа отклонений"""
        
        dashboard = {
            "charts": {},
            "summary_metrics": {},
            "alerts": []
        }
        
        # 1. Variance Trend Chart
        if len(aligned_data) >= 2:
            fig_variance_trend = self._create_variance_trend_chart(aligned_data)
            dashboard["charts"]["variance_trend"] = fig_variance_trend
        
        # 2. Variance by Category Chart
        fig_variance_by_category = self._create_variance_by_category_chart(variance_analysis)
        dashboard["charts"]["variance_by_category"] = fig_variance_by_category
        
        # 3. Significant Variances Chart
        if significant_variances:
            fig_significant_variances = self._create_significant_variances_chart(significant_variances)
            dashboard["charts"]["significant_variances"] = fig_significant_variances
        
        # 4. Summary Metrics
        dashboard["summary_metrics"] = self._calculate_dashboard_metrics(
            aligned_data, variance_analysis, significant_variances
        )
        
        # 5. Alerts
        dashboard["alerts"] = self._generate_variance_alerts(significant_variances)
        
        return dashboard
    
    def _create_variance_trend_chart(self, aligned_data: List[Dict]) -> go.Figure:
        """Создание графика тренда отклонений"""
        
        months = []
        revenue_variances = []
        cost_variances = []
        
        for data in aligned_data:
            if not data['has_actual']:
                continue
            
            planned = data['planned']
            actual = data['actual']
            
            months.append(data['month_name'])
            
            # Revenue variance
            if 'plan_total_revenue' in planned and 'plan_total_revenue' in actual:
                planned_rev = planned['plan_total_revenue']
                actual_rev = actual['plan_total_revenue']
                if planned_rev != 0:
                    revenue_variances.append((actual_rev - planned_rev) / planned_rev * 100)
                else:
                    revenue_variances.append(0)
            
            # Cost variance
            if 'plan_total_costs' in planned and 'plan_total_costs' in actual:
                planned_cost = planned['plan_total_costs']
                actual_cost = actual['plan_total_costs']
                if planned_cost != 0:
                    cost_variances.append((actual_cost - planned_cost) / planned_cost * 100)
                else:
                    cost_variances.append(0)
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=months,
            y=revenue_variances,
            mode='lines+markers',
            name='Revenue Variance %',
            line=dict(color='green', width=3)
        ))
        
        fig.add_trace(go.Scatter(
            x=months,
            y=cost_variances,
            mode='lines+markers',
            name='Cost Variance %',
            line=dict(color='red', width=3)
        ))
        
        fig.add_hline(y=0, line_dash="dash", line_color="gray",
                     annotation_text="Target", annotation_position="bottom right")
        
        fig.update_layout(
            title='Trend of Variances Over Time',
            xaxis_title='Month',
            yaxis_title='Variance %',
            height=400
        )
        
        return fig
    
    def _create_variance_by_category_chart(self, variance_analysis: List[Dict]) -> go.Figure:
        """Создание графика отклонений по категориям"""
        
        # Группируем по категориям
        categories = {}
        
        for variance in variance_analysis:
            category = variance['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(abs(variance['variance_percent']))
        
        # Средние значения по категориям
        category_means = {
            cat: np.mean(vals) for cat, vals in categories.items()
        }
        
        fig = go.Figure(data=[go.Bar(
            x=list(category_means.keys()),
            y=list(category_means.values()),
            marker_color=['red', 'orange', 'yellow', 'green', 'blue'][:len(category_means)],
            text=[f"{v:.1f}%" for v in category_means.values()],
            textposition='auto'
        )])
        
        fig.update_layout(
            title='Average Variance by Category',
            xaxis_title='Category',
            yaxis_title='Average Variance %',
            height=400
        )
        
        return fig
    
    def _create_significant_variances_chart(self, significant_variances: List[Dict]) -> go.Figure:
        """Создание графика значимых отклонений"""
        
        # Группируем по значимости
        by_significance = {
            'critical': [],
            'high': [],
            'medium': []
        }
        
        for variance in significant_variances:
            sig = variance['significance']
            if sig in by_significance:
                by_significance[sig].append(variance)
        
        # Создаем stacked bar chart
        months = sorted(set(v['month'] for v in significant_variances))
        
        critical_counts = [len([v for v in by_significance['critical'] if v['month'] == month]) 
                          for month in months]
        high_counts = [len([v for v in by_significance['high'] if v['month'] == month]) 
                      for month in months]
        medium_counts = [len([v for v in by_significance['medium'] if v['month'] == month]) 
                        for month in months]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=months,
            y=medium_counts,
            name='Medium',
            marker_color='yellow'
        ))
        
        fig.add_trace(go.Bar(
            x=months,
            y=high_counts,
            name='High',
            marker_color='orange'
        ))
        
        fig.add_trace(go.Bar(
            x=months,
            y=critical_counts,
            name='Critical',
            marker_color='red'
        ))
        
        fig.update_layout(
            title='Significant Variances by Month',
            xaxis_title='Month',
            yaxis_title='Number of Variances',
            barmode='stack',
            height=400
        )
        
        return fig
    
    def _calculate_dashboard_metrics(self, aligned_data: List[Dict],
                                    variance_analysis: List[Dict],
                                    significant_variances: List[Dict]) -> Dict[str, Any]:
        """Расчет метрик для dashboard"""
        
        metrics = {}
        
        # Количество months с actual данными
        months_with_data = len([d for d in aligned_data if d['has_actual']])
        metrics["months_analyzed"] = months_with_data
        
        # Общее количество отклонений
        metrics["total_variances"] = len(variance_analysis)
        
        # Количество значимых отклонений
        metrics["significant_variances"] = len(significant_variances)
        
        # Распределение по значимости
        if significant_variances:
            critical = len([v for v in significant_variances if v['significance'] == 'critical'])
            high = len([v for v in significant_variances if v['significance'] == 'high'])
            medium = len([v for v in significant_variances if v['significance'] == 'medium'])
            
            metrics["critical_variances"] = critical
            metrics["high_variances"] = high
            metrics["medium_variances"] = medium
        
        # Среднее отклонение
        if variance_analysis:
            avg_variance = np.mean([abs(v['variance_percent']) for v in variance_analysis])
            metrics["avg_variance_percent"] = f"{avg_variance:.1f}%"
        
        # Наиболее проблемная категория
        if variance_analysis:
            by_category = {}
            for variance in variance_analysis:
                cat = variance['category']
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(abs(variance['variance_percent']))
            
            if by_category:
                worst_category = max(by_category.items(), key=lambda x: np.mean(x[1]))
                metrics["worst_performing_category"] = worst_category[0]
                metrics["worst_category_avg_variance"] = f"{np.mean(worst_category[1]):.1f}%"
        
        return metrics
    
    def _generate_variance_alerts(self, significant_variances: List[Dict]) -> List[Dict[str, Any]]:
        """Генерация alerts на основе значимых отклонений"""
        
        alerts = []
        
        # Критические отклонения
        critical_variances = [v for v in significant_variances if v['significance'] == 'critical']
        
        for variance in critical_variances:
            alerts.append({
                "type": "critical",
                "title": f"Критическое отклонение: {variance['metric']}",
                "message": f"Отклонение {variance['variance_percent']:.1f}% в {variance['month']}",
                "metric": variance['metric'],
                "month": variance['month'],
                "action_required": True
            })
        
        # Групповые alerts
        # Если много отклонений в revenue
        revenue_variances = [v for v in significant_variances 
                           if 'revenue' in v['metric'].lower() or 'mrr' in v['metric'].lower()]
        
        if len(revenue_variances) >= 3:
            negative_revenue = [v for v in revenue_variances if v['variance_amount'] < 0]
            if len(negative_revenue) >= 2:
                alerts.append({
                    "type": "high",
                    "title": "Повторяющиеся отклонения в revenue",
                    "message": f"{len(negative_revenue)} из {len(revenue_variances)} месяцев ниже плана",
                    "metric": "revenue",
                    "action_required": True
                })
        
        # Если много отклонений в costs
        cost_variances = [v for v in significant_variances 
                         if 'cost' in v['metric'].lower() or 'budget' in v['metric'].lower()]
        
        if len(cost_variances) >= 3:
            positive_costs = [v for v in cost_variances if v['variance_amount'] > 0]
            if len(positive_costs) >= 2:
                alerts.append({
                    "type": "high",
                    "title": "Превышение бюджета по расходам",
                    "message": f"{len(positive_costs)} из {len(cost_variances)} месяцев выше плана",
                    "metric": "costs",
                    "action_required": True
                })
        
        return alerts
    
    def _create_variance_summary(self, variance_analysis: List[Dict]) -> Dict[str, Any]:
        """Создание summary отклонений"""
        
        if not variance_analysis:
            return {"no_data": True}
        
        # Группируем по метрикам
        by_metric = {}
        
        for variance in variance_analysis:
            metric = variance['metric']
            if metric not in by_metric:
                by_metric[metric] = []
            by_metric[metric].append(variance)
        
        # Создаем summary
        summary = {
            "metrics_analyzed": len(by_metric),
            "total_data_points": len(variance_analysis),
            "worst_performing_metrics": [],
            "best_performing_metrics": []
        }
        
        # Находим худшие и лучшие метрики
        metric_avg_variances = {}
        
        for metric, variances in by_metric.items():
            avg_variance = np.mean([abs(v['variance_percent']) for v in variances])
            metric_avg_variances[metric] = avg_variance
        
        # Топ-3 худших
        worst_metrics = sorted(metric_avg_variances.items(), key=lambda x: x[1], reverse=True)[:3]
        summary["worst_performing_metrics"] = [
            {"metric": metric, "avg_variance": f"{variance:.1f}%"} 
            for metric, variance in worst_metrics
        ]
        
        # Топ-3 лучших
        best_metrics = sorted(metric_avg_variances.items(), key=lambda x: x[1])[:3]
        summary["best_performing_metrics"] = [
            {"metric": metric, "avg_variance": f"{variance:.1f}%"} 
            for metric, variance in best_metrics
        ]
        
        # Общее среднее отклонение
        all_variances = [abs(v['variance_percent']) for v in variance_analysis]
        summary["overall_avg_variance"] = f"{np.mean(all_variances):.1f}%"
        summary["variance_volatility"] = f"{np.std(all_variances):.1f}%"
        
        return summary
    
    def _extract_key_insights(self, significant_variances: List[Dict],
                             trend_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Извлечение ключевых инсайтов из анализа"""
        
        insights = []
        
        # Insight 1: Наличие критических отклонений
        critical_variances = [v for v in significant_variances if v['significance'] == 'critical']
        
        if critical_variances:
            metrics = set(v['metric'] for v in critical_variances)
            insights.append({
                "type": "critical_issue",
                "title": "Критические отклонения обнаружены",
                "description": f"Критические отклонения в {len(critical_variances)} точках данных по метрикам: {', '.join(metrics)}",
                "severity": "critical",
                "recommendation": "Немедленно рассмотреть и принять корректирующие действия"
            })
        
        # Insight 2: Тренд accuracy
        if not trend_analysis.get("insufficient_data", False):
            trend = trend_analysis.get("trend_direction")
            
            if trend == "improving":
                insights.append({
                    "type": "positive_trend",
                    "title": "Точность планирования улучшается",
                    "description": "Отклонения уменьшаются со временем, что указывает на улучшение accuracy планирования",
                    "severity": "positive",
                    "recommendation": "Продолжать текущие практики планирования"
                })
            elif trend == "worsening":
                insights.append({
                    "type": "negative_trend",
                    "title": "Точность планирования ухудшается",
                    "description": "Отклонения увеличиваются со временем, что указывает на проблемы с accuracy планирования",
                    "severity": "medium",
                    "recommendation": "Пересмотреть assumptions и методы планирования"
                })
        
        # Insight 3: Распределение отклонений
        if significant_variances:
            by_category = {}
            for variance in significant_variances:
                cat = variance['category']
                if cat not in by_category:
                    by_category[cat] = 0
                by_category[cat] += 1
            
            if by_category:
                worst_category = max(by_category.items(), key=lambda x: x[1])
                insights.append({
                    "type": "category_focus",
                    "title": f"Наибольшие проблемы в категории: {worst_category[0]}",
                    "description": f"{worst_category[1]} значимых отклонений в этой категории",
                    "severity": "medium",
                    "recommendation": "Сфокусировать усилия на улучшении этой категории"
                })
        
        # Insight 4: Системные проблемы
        revenue_variances = [v for v in significant_variances 
                           if 'revenue' in v['metric'].lower() or 'mrr' in v['metric'].lower()]
        cost_variances = [v for v in significant_variances 
                         if 'cost' in v['metric'].lower() or 'budget' in v['metric'].lower()]
        
        if len(revenue_variances) >= 3 and len(cost_variances) >= 3:
            insights.append({
                "type": "systemic_issue",
                "title": "Системные проблемы в планировании",
                "description": "Множественные отклонения как в revenue, так и в costs, что указывает на системные проблемы",
                "severity": "high",
                "recommendation": "Провести comprehensive review всего planning process"
            })
        
        return insights

# Создаем глобальный экземпляр анализатора
variance_analyzer = VarianceAnalyzer()

# Экспортируем полезные функции
def analyze_plan_variance(company_id: int, plan_id: int, 
                         start_date: Optional[str] = None,
                         end_date: Optional[str] = None) -> Dict[str, Any]:
    """Публичная функция для анализа отклонений плана"""
    
    # Получаем плановые данные
    plan = db_manager.get_financial_plan(plan_id)
    monthly_plans = db_manager.get_monthly_plans(plan_id)
    
    if not plan or not monthly_plans:
        return {"error": "Plan not found"}
    
    # Получаем фактические данные
    actual_data = db_manager.get_actual_financials(
        company_id, 
        start_date or plan.created_at,
        end_date or datetime.now().isoformat()
    )
    
    # Конвертируем в dict
    planned_dicts = [p.to_dict() for p in monthly_plans]
    actual_dicts = [a.to_dict() for a in actual_data]
    
    # Получаем стадию компании
    company = db_manager.get_company(company_id)
    stage = company.stage if company else 'pre_seed'
    
    return variance_analyzer.analyze_variance(planned_dicts, actual_dicts, stage)

def get_variance_alerts(company_id: int, last_n_months: int = 3) -> List[Dict[str, Any]]:
    """Получение variance alerts за последние N месяцев"""
    
    # Получаем последние фактические данные
    end_date = datetime.now()
    start_date = end_date - timedelta(days=last_n_months*30)
    
    actual_data = db_manager.get_actual_financials(
        company_id, start_date.isoformat(), end_date.isoformat()
    )
    
    if not actual_data:
        return []
    
    # Находим соответствующие планы
    alerts = []
    
    for actual in actual_data:
        # Ищем соответствующий месячный план
        month_plan = db_manager.get_monthly_plan_by_period(
            company_id, actual.year, actual.month_number
        )
        
        if month_plan:
            # Анализируем variance
            variance_analysis = variance_analyzer.analyze_variance(
                [month_plan.to_dict()], [actual.to_dict()], "pre_seed"
            )
            
            # Извлекаем alerts
            if "dashboard" in variance_analysis:
                alerts.extend(variance_analysis["dashboard"].get("alerts", []))
    
    return alerts