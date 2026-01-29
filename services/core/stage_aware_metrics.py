"""
Метрики, зависящие от стадии стартапа (Pre-seed, Seed, Series A и т.д.)
На основе реальных исследований SaaS индустрии
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum
import json

class Stage(Enum):
    """Стадии развития стартапа"""
    PRE_SEED = "pre_seed"          # Идея -> Первые клиенты
    SEED = "seed"                  # Product-Market Fit
    SERIES_A = "series_a"          # Масштабирование
    SERIES_B = "series_b"          # Ускорение роста
    SERIES_C_PLUS = "series_c_plus" # Зрелость

class MetricCategory(Enum):
    """Категории метрик"""
    GROWTH = "growth"              # Метрики роста
    EFFICIENCY = "efficiency"      # Эффективность
    PROFITABILITY = "profitability" # Рентабельность
    RETENTION = "retention"        # Удержание
    ACQUISITION = "acquisition"    # Привлечение
    TEAM = "team"                  # Команда

@dataclass
class StageMetrics:
    """Целевые метрики для конкретной стадии"""
    stage: Stage
    metrics: Dict[str, Dict[str, Any]]
    
    def get_metric(self, metric_name: str) -> Optional[Dict[str, Any]]:
        """Получение метрики по имени"""
        return self.metrics.get(metric_name)
    
    def get_target_value(self, metric_name: str) -> Optional[float]:
        """Получение целевого значения метрики"""
        metric = self.get_metric(metric_name)
        return metric.get('target') if metric else None
    
    def get_benchmark_range(self, metric_name: str) -> Dict[str, float]:
        """Получение диапазона значений для метрики"""
        metric = self.get_metric(metric_name)
        if not metric:
            return {}
        
        return {
            'poor': metric.get('poor', 0),
            'average': metric.get('average', 0),
            'good': metric.get('good', 0),
            'excellent': metric.get('excellent', 0)
        }
    
    def assess_metric(self, metric_name: str, value: float) -> Dict[str, Any]:
        """Оценка метрики относительно целевых значений"""
        ranges = self.get_benchmark_range(metric_name)
        if not ranges:
            return {'status': 'unknown', 'score': 0}
        
        # Определяем статус на основе значения
        if value <= ranges['poor']:
            status = 'critical'
            score = 1
        elif value <= ranges['average']:
            status = 'warning'
            score = 2
        elif value <= ranges['good']:
            status = 'good'
            score = 3
        elif value <= ranges['excellent']:
            status = 'excellent'
            score = 4
        else:
            status = 'outstanding'
            score = 5
        
        return {
            'status': status,
            'score': score,
            'value': value,
            'target': ranges['good'],  # Используем 'good' как цель
            'deviation': ((value - ranges['good']) / ranges['good']) * 100 if ranges['good'] > 0 else 0,
            'ranges': ranges
        }

class StageAwareMetrics:
    """Класс для работы с метриками, зависящими от стадии"""
    
    def __init__(self):
        self.stage_metrics = self._load_metrics()
    
    def _load_metrics(self) -> Dict[Stage, StageMetrics]:
        """Загрузка метрик для всех стадий"""
        
        # Pre-Seed Stage Metrics (самые важные для нашего приложения)
        pre_seed_metrics = {
            # Рост
            'mrr_growth_monthly': {
                'category': MetricCategory.GROWTH,
                'description': 'Месячный рост MRR',
                'unit': 'percentage',
                'poor': 0.05,      # 5%
                'average': 0.10,   # 10%
                'good': 0.20,      # 20%
                'excellent': 0.30, # 30%
                'target': 0.20,
                'priority': 'critical',
                'source': 'Bessemer Cloud Index'
            },
            
            # Эффективность
            'cac_payback_months': {
                'category': MetricCategory.EFFICIENCY,
                'description': 'Время окупаемости CAC в месяцах',
                'unit': 'months',
                'poor': 24,        # 24 месяца
                'average': 18,     # 18 месяцев
                'good': 12,        # 12 месяцев
                'excellent': 9,    # 9 месяцев
                'target': 12,
                'priority': 'high',
                'source': 'OpenView SaaS Benchmarks'
            },
            
            'ltv_cac_ratio': {
                'category': MetricCategory.EFFICIENCY,
                'description': 'Соотношение LTV к CAC',
                'unit': 'ratio',
                'poor': 1.5,       # 1.5x
                'average': 2.5,    # 2.5x
                'good': 3.5,       # 3.5x
                'excellent': 5.0,  # 5.0x
                'target': 3.5,
                'priority': 'high',
                'source': 'SaaS Capital'
            },
            
            'burn_to_mrr_ratio': {
                'category': MetricCategory.EFFICIENCY,
                'description': 'Соотношение Burn Rate к MRR',
                'unit': 'ratio',
                'poor': 3.0,       # 3.0x
                'average': 2.0,    # 2.0x
                'good': 1.5,       # 1.5x
                'excellent': 1.0,  # 1.0x
                'target': 1.5,
                'priority': 'high',
                'source': 'OpenView SaaS Benchmarks'
            },
            
            # Рентабельность
            'gross_margin': {
                'category': MetricCategory.PROFITABILITY,
                'description': 'Валовая маржа',
                'unit': 'percentage',
                'poor': 0.60,      # 60%
                'average': 0.70,   # 70%
                'good': 0.80,      # 80%
                'excellent': 0.90, # 90%
                'target': 0.80,
                'priority': 'medium',
                'source': 'Pacific Crest Survey'
            },
            
            # Удержание
            'monthly_churn_rate': {
                'category': MetricCategory.RETENTION,
                'description': 'Месячный процент оттока',
                'unit': 'percentage',
                'poor': 0.10,      # 10%
                'average': 0.07,   # 7%
                'good': 0.05,      # 5%
                'excellent': 0.03, # 3%
                'target': 0.05,
                'priority': 'critical',
                'source': 'Bessemer Cloud Index'
            },
            
            'net_revenue_retention': {
                'category': MetricCategory.RETENTION,
                'description': 'Чистое удержание выручки',
                'unit': 'percentage',
                'poor': 0.90,      # 90%
                'average': 0.95,   # 95%
                'good': 1.05,      # 105%
                'excellent': 1.15, # 115%
                'target': 1.05,
                'priority': 'high',
                'source': 'Bessemer Cloud Index'
            },
            
            # Привлечение
            'cac': {
                'category': MetricCategory.ACQUISITION,
                'description': 'Стоимость привлечения клиента',
                'unit': 'currency',
                'poor': 50000,     # 50,000 руб.
                'average': 30000,  # 30,000 руб.
                'good': 20000,     # 20,000 руб.
                'excellent': 10000, # 10,000 руб.
                'target': 20000,
                'priority': 'high',
                'source': 'Custom Benchmark'
            },
            
            'website_conversion_rate': {
                'category': MetricCategory.ACQUISITION,
                'description': 'Конверсия сайта в лиды',
                'unit': 'percentage',
                'poor': 0.01,      # 1%
                'average': 0.02,   # 2%
                'good': 0.03,      # 3%
                'excellent': 0.05, # 5%
                'target': 0.03,
                'priority': 'medium',
                'source': 'MarketingSherpa'
            },
            
            # Команда
            'revenue_per_employee': {
                'category': MetricCategory.TEAM,
                'description': 'Выручка на сотрудника в год',
                'unit': 'currency',
                'poor': 500000,    # 500,000 руб.
                'average': 1000000, # 1,000,000 руб.
                'good': 2000000,   # 2,000,000 руб.
                'excellent': 3000000, # 3,000,000 руб.
                'target': 2000000,
                'priority': 'low',
                'source': 'OpenView SaaS Benchmarks'
            },
            
            # Дополнительные метрики для Pre-Seed
            'runway_months': {
                'category': MetricCategory.EFFICIENCY,
                'description': 'Оставшиеся месяцы до сгорания денег',
                'unit': 'months',
                'poor': 3,         # 3 месяца
                'average': 6,      # 6 месяцев
                'good': 12,        # 12 месяцев
                'excellent': 18,   # 18 месяцев
                'target': 12,
                'priority': 'critical',
                'source': 'VC Best Practices'
            },
            
            'product_market_fit_score': {
                'category': MetricCategory.GROWTH,
                'description': 'Оценка Product-Market Fit',
                'unit': 'score',
                'poor': 20,        # 20/100
                'average': 40,     # 40/100
                'good': 60,        # 60/100
                'excellent': 80,   # 80/100
                'target': 60,
                'priority': 'critical',
                'source': 'Sean Ellis Test'
            }
        }
        
        # Seed Stage Metrics (более агрессивные)
        seed_metrics = pre_seed_metrics.copy()
        # Обновляем метрики для Seed стадии
        seed_metrics.update({
            'mrr_growth_monthly': {
                **seed_metrics['mrr_growth_monthly'],
                'poor': 0.10,
                'average': 0.15,
                'good': 0.25,
                'excellent': 0.40,
                'target': 0.25
            },
            'cac_payback_months': {
                **seed_metrics['cac_payback_months'],
                'poor': 18,
                'average': 12,
                'good': 9,
                'excellent': 6,
                'target': 9
            },
            'runway_months': {
                **seed_metrics['runway_months'],
                'poor': 6,
                'average': 9,
                'good': 12,
                'excellent': 18,
                'target': 12
            }
        })
        
        # Series A Metrics
        series_a_metrics = seed_metrics.copy()
        series_a_metrics.update({
            'mrr_growth_monthly': {
                **series_a_metrics['mrr_growth_monthly'],
                'poor': 0.08,
                'average': 0.12,
                'good': 0.18,
                'excellent': 0.25,
                'target': 0.18
            },
            'ltv_cac_ratio': {
                **series_a_metrics['ltv_cac_ratio'],
                'poor': 2.0,
                'average': 3.0,
                'good': 4.0,
                'excellent': 5.0,
                'target': 4.0
            }
        })
        
        return {
            Stage.PRE_SEED: StageMetrics(stage=Stage.PRE_SEED, metrics=pre_seed_metrics),
            Stage.SEED: StageMetrics(stage=Stage.SEED, metrics=seed_metrics),
            Stage.SERIES_A: StageMetrics(stage=Stage.SERIES_A, metrics=series_a_metrics),
            Stage.SERIES_B: StageMetrics(stage=Stage.SERIES_B, metrics=series_a_metrics),  # Для простоты
            Stage.SERIES_C_PLUS: StageMetrics(stage=Stage.SERIES_C_PLUS, metrics=series_a_metrics)
        }
    
    def get_stage_metrics(self, stage_str: str) -> Optional[StageMetrics]:
        """Получение метрик для стадии по строке"""
        try:
            stage = Stage(stage_str)
            return self.stage_metrics.get(stage)
        except ValueError:
            # Если стадия не найдена, возвращаем Pre-Seed как дефолт
            return self.stage_metrics.get(Stage.PRE_SEED)
    
    def get_stage_from_revenue(self, annual_revenue: float) -> Stage:
        """Определение стадии на основе годовой выручки (в рублях)"""
        if annual_revenue < 5000000:      # < 5 млн руб.
            return Stage.PRE_SEED
        elif annual_revenue < 25000000:   # < 25 млн руб.
            return Stage.SEED
        elif annual_revenue < 100000000:  # < 100 млн руб.
            return Stage.SERIES_A
        elif annual_revenue < 500000000:  # < 500 млн руб.
            return Stage.SERIES_B
        else:
            return Stage.SERIES_C_PLUS
    
    def get_key_metrics_for_stage(self, stage_str: str) -> List[Dict[str, Any]]:
        """Получение ключевых метрик для стадии"""
        stage_metrics = self.get_stage_metrics(stage_str)
        if not stage_metrics:
            return []
        
        key_metrics = []
        for name, metric in stage_metrics.metrics.items():
            if metric.get('priority') in ['critical', 'high']:
                key_metrics.append({
                    'name': name,
                    'description': metric['description'],
                    'category': metric['category'].value,
                    'target': metric['target'],
                    'unit': metric['unit'],
                    'priority': metric['priority'],
                    'source': metric['source']
                })
        
        return key_metrics
    
    def assess_company_metrics(self, stage_str: str, company_metrics: Dict[str, float]) -> Dict[str, Any]:
        """Оценка метрик компании относительно целевых для стадии"""
        stage_metrics = self.get_stage_metrics(stage_str)
        if not stage_metrics:
            return {'error': 'Стадия не найдена'}
        
        assessment = {
            'stage': stage_str,
            'overall_score': 0,
            'metrics': {},
            'categories': {},
            'recommendations': []
        }
        
        total_score = 0
        metric_count = 0
        
        # Оцениваем каждую метрику
        for metric_name, value in company_metrics.items():
            metric_assessment = stage_metrics.assess_metric(metric_name, value)
            if metric_assessment['status'] != 'unknown':
                assessment['metrics'][metric_name] = metric_assessment
                total_score += metric_assessment['score']
                metric_count += 1
                
                # Добавляем в категории
                metric_info = stage_metrics.get_metric(metric_name)
                if metric_info:
                    category = metric_info['category'].value
                    if category not in assessment['categories']:
                        assessment['categories'][category] = {
                            'score': 0,
                            'count': 0,
                            'metrics': []
                        }
                    assessment['categories'][category]['score'] += metric_assessment['score']
                    assessment['categories'][category]['count'] += 1
                    assessment['categories'][category]['metrics'].append(metric_name)
        
        # Рассчитываем общий score
        if metric_count > 0:
            assessment['overall_score'] = round((total_score / (metric_count * 5)) * 100, 1)
        
        # Рассчитываем средние score по категориям
        for category, data in assessment['categories'].items():
            if data['count'] > 0:
                data['average_score'] = round((data['score'] / (data['count'] * 5)) * 100, 1)
            else:
                data['average_score'] = 0
        
        # Генерируем рекомендации
        assessment['recommendations'] = self._generate_recommendations(assessment)
        
        return assessment
    
    def _generate_recommendations(self, assessment: Dict[str, Any]) -> List[Dict[str, str]]:
        """Генерация рекомендаций на основе оценки"""
        recommendations = []
        
        # Анализируем плохие метрики
        for metric_name, metric_data in assessment['metrics'].items():
            if metric_data['status'] in ['critical', 'warning']:
                rec = self._get_recommendation_for_metric(metric_name, metric_data)
                if rec:
                    recommendations.append(rec)
        
        # Добавляем общие рекомендации по категориям
        for category, data in assessment['categories'].items():
            if data.get('average_score', 0) < 60:  # Ниже 60%
                rec = self._get_recommendation_for_category(category, data['average_score'])
                if rec:
                    recommendations.append(rec)
        
        # Ограничиваем количество рекомендаций
        return recommendations[:5]
    
    def _get_recommendation_for_metric(self, metric_name: str, metric_data: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """Получение рекомендации для конкретной метрики"""
        
        recommendation_map = {
            'mrr_growth_monthly': {
                'critical': {
                    'title': 'Критически низкий рост MRR',
                    'description': 'Необходимо срочно увеличить темпы роста выручки',
                    'actions': [
                        'Увеличить маркетинговый бюджет на 20-30%',
                        'Запустить реферальную программу',
                        'Оптимизировать воронку продаж',
                        'Рассмотреть изменение ценообразования'
                    ]
                },
                'warning': {
                    'title': 'Низкий рост MRR',
                    'description': 'Рост выручки ниже целевых показателей',
                    'actions': [
                        'Анализировать CAC по каналам',
                        'Улучшить конверсию на сайте',
                        'Запустить upsell кампанию для существующих клиентов'
                    ]
                }
            },
            'cac_payback_months': {
                'critical': {
                    'title': 'Долгий срок окупаемости CAC',
                    'description': 'CAC окупается слишком долго, что ограничивает рост',
                    'actions': [
                        'Фокусироваться на каналах с низким CAC',
                        'Улучшить onboarding для увеличения LTV',
                        'Оптимизировать процессы продаж',
                        'Рассмотреть увеличение цен'
                    ]
                }
            },
            'runway_months': {
                'critical': {
                    'title': 'Критически низкий Runway',
                    'description': 'Осталось менее 6 месяцев до сгорания денег',
                    'actions': [
                        'Сократить non-essential расходы на 20-30%',
                        'Ускорить монетизацию',
                        'Начать подготовку к следующему раунду',
                        'Рассмотреть bridge financing'
                    ]
                }
            },
            'monthly_churn_rate': {
                'critical': {
                    'title': 'Высокий процент оттока клиентов',
                    'description': 'Большое количество клиентов уходит каждый месяц',
                    'actions': [
                        'Провести exit интервью с уходящими клиентами',
                        'Улучшить customer success процессы',
                        'Добавить новые возможности продукта',
                        'Запустить программу лояльности'
                    ]
                }
            }
        }
        
        if metric_name in recommendation_map and metric_data['status'] in recommendation_map[metric_name]:
            rec_data = recommendation_map[metric_name][metric_data['status']]
            return {
                'metric': metric_name,
                'status': metric_data['status'],
                'priority': 'high' if metric_data['status'] == 'critical' else 'medium',
                **rec_data
            }
        
        return None
    
    def _get_recommendation_for_category(self, category: str, score: float) -> Optional[Dict[str, str]]:
        """Получение рекомендации для категории"""
        
        category_map = {
            'growth': {
                'title': 'Проблемы с ростом',
                'description': f'Метрики роста ниже целевых ({score}%)',
                'actions': [
                    'Пересмотреть стратегию роста',
                    'Увеличить инвестиции в маркетинг',
                    'Оптимизировать процессы продаж'
                ]
            },
            'efficiency': {
                'title': 'Низкая эффективность',
                'description': f'Метрики эффективности требуют улучшения ({score}%)',
                'actions': [
                    'Оптимизировать операционные процессы',
                    'Автоматизировать рутинные задачи',
                    'Улучшить unit economics'
                ]
            },
            'retention': {
                'title': 'Проблемы с удержанием',
                'description': f'Метрики удержания ниже ожидаемых ({score}%)',
                'actions': [
                    'Усилить customer success команду',
                    'Улучшить качество продукта',
                    'Внедрить программы лояльности'
                ]
            }
        }
        
        if category in category_map:
            return {
                'category': category,
                'priority': 'medium',
                **category_map[category]
            }
        
        return None
    
    def get_metric_calculation_guide(self, metric_name: str) -> Dict[str, Any]:
        """Получение руководства по расчету метрики"""
        
        calculation_guides = {
            'mrr_growth_monthly': {
                'formula': '(Текущий MRR - Предыдущий MRR) / Предыдущий MRR',
                'example': 'Если в январе MRR был 100,000 руб., а в феврале 120,000 руб., то рост = (120,000 - 100,000) / 100,000 = 0.2 (20%)',
                'data_needed': ['MRR за текущий месяц', 'MRR за предыдущий месяц'],
                'frequency': 'Ежемесячно',
                'common_mistakes': [
                    'Не учитывать churned revenue',
                    'Не включать expansion revenue',
                    'Использовать разные валюты'
                ]
            },
            'cac_payback_months': {
                'formula': 'CAC / (MRR на клиента)',
                'example': 'Если CAC = 20,000 руб., а средний MRR на клиента = 5,000 руб., то payback = 20,000 / 5,000 = 4 месяца',
                'data_needed': ['Общий CAC за период', 'Средний MRR на нового клиента'],
                'frequency': 'Ежемесячно или ежеквартально',
                'common_mistakes': [
                    'Не включать все расходы на привлечение',
                    'Использовать неправильный CAC period',
                    'Не учитывать churn при расчете'
                ]
            },
            'ltv_cac_ratio': {
                'formula': 'LTV / CAC',
                'example': 'Если LTV клиента = 60,000 руб., а CAC = 20,000 руб., то LTV/CAC = 60,000 / 20,000 = 3.0',
                'data_needed': ['Средний MRR на клиента', 'Средний churn rate', 'CAC'],
                'frequency': 'Ежеквартально',
                'common_mistakes': [
                    'Использовать неправильный churn rate',
                    'Не учитывать discount rate для LTV',
                    'Сравнивать LTV и CAC за разные периоды'
                ]
            }
        }
        
        return calculation_guides.get(metric_name, {
            'formula': 'Недоступно',
            'example': 'Нет примера',
            'data_needed': [],
            'frequency': 'Неизвестно',
            'common_mistakes': []
        })
    
    def get_benchmark_comparison(self, stage_str: str, metric_name: str, value: float) -> Dict[str, Any]:
        """Сравнение значения метрики с бенчмарками"""
        stage_metrics = self.get_stage_metrics(stage_str)
        if not stage_metrics:
            return {}
        
        metric = stage_metrics.get_metric(metric_name)
        if not metric:
            return {}
        
        ranges = stage_metrics.get_benchmark_range(metric_name)
        
        # Рассчитываем процентиль
        if value <= ranges['poor']:
            percentile = 25
        elif value <= ranges['average']:
            percentile = 50
        elif value <= ranges['good']:
            percentile = 75
        elif value <= ranges['excellent']:
            percentile = 90
        else:
            percentile = 95
        
        # Определяем позицию относительно конкурентов
        if percentile >= 90:
            position = 'Топ 10% компаний'
        elif percentile >= 75:
            position = 'Топ 25% компаний'
        elif percentile >= 50:
            position = 'Выше среднего'
        elif percentile >= 25:
            position = 'Ниже среднего'
        else:
            position = 'Низкие показатели'
        
        return {
            'value': value,
            'percentile': percentile,
            'position': position,
            'benchmarks': ranges,
            'gap_to_good': ranges['good'] - value if value < ranges['good'] else 0,
            'gap_percentage': ((ranges['good'] - value) / ranges['good'] * 100) if ranges['good'] > 0 and value < ranges['good'] else 0,
            'source': metric.get('source', 'Неизвестно')
        }

# Создаем глобальный экземпляр
stage_metrics = StageAwareMetrics()

# Алиас для обратной совместимости с gigachat_analyst.py
stage_aware_metrics = stage_metrics

# Экспортируем полезные функции
def get_stage_metrics(stage: str) -> Optional[StageMetrics]:
    """Публичная функция для получения метрик стадии"""
    return stage_metrics.get_stage_metrics(stage)

def assess_company(stage: str, metrics: Dict[str, float]) -> Dict[str, Any]:
    """Публичная функция для оценки компании"""
    return stage_metrics.assess_company_metrics(stage, metrics)

def get_key_metrics(stage: str) -> List[Dict[str, Any]]:
    """Публичная функция для получения ключевых метрик"""
    return stage_metrics.get_key_metrics_for_stage(stage)