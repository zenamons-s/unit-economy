"""
Когортный анализ для SaaS метрик
Анализ retention, LTV, churn по когортам клиентов
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import plotly.graph_objects as go
import plotly.express as px
from dataclasses import dataclass
from scipy import stats
from services.utils.math_utils import safe_divide

@dataclass
class Cohort:
    """Когорта клиентов"""
    id: str
    period: str  # '2024-01', '2024-Q1', etc.
    start_date: datetime
    end_date: datetime
    customer_count: int
    total_mrr: float
    
    # Retention metrics
    retention_curve: Optional[List[float]] = None
    churn_curve: Optional[List[float]] = None
    
    # Financial metrics
    cohort_ltv: Optional[float] = None
    cohort_cac: Optional[float] = None
    payback_period: Optional[int] = None

class RealisticCohortAnalyzer:
    """
    Реалистичный анализатор когорт для SaaS
    С учетом реалий B2B SaaS и российского рынка
    """
    
    def __init__(self):
        self.month_names = {
            1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель',
            5: 'Май', 6: 'Июнь', 7: 'Июль', 8: 'Август',
            9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'
        }
    
    def analyze_cohorts(self, transaction_data: pd.DataFrame, 
                       period_type: str = 'monthly') -> Dict[str, Any]:
        """
        Основной анализ когорт
        
        Args:
            transaction_data: DataFrame с транзакциями
                Должен содержать колонки:
                - customer_id: ID клиента
                - date: дата транзакции
                - amount: сумма транзакции
                - mrr: месячная выручка
            period_type: тип периода ('monthly', 'quarterly')
        
        Returns:
            Dict с результатами анализа
        """
        
        # Подготовка данных
        df = self._prepare_data(transaction_data)
        
        # Создание когорт
        cohorts = self._create_cohorts(df, period_type)
        
        # Расчет retention
        retention_matrix = self._calculate_retention_matrix(df, cohorts, period_type)
        
        # Расчет LTV
        ltv_analysis = self._calculate_ltv_analysis(df, cohorts)
        
        # Прогноз удержания
        forecast = self._forecast_retention(retention_matrix)
        
        # Визуализации
        visualizations = self._create_visualizations(retention_matrix, ltv_analysis, forecast)
        
        # Инсайты
        insights = self._generate_insights(cohorts, retention_matrix, ltv_analysis)
        
        return {
            'cohorts': cohorts,
            'retention_matrix': retention_matrix,
            'ltv_analysis': ltv_analysis,
            'forecast': forecast,
            'visualizations': visualizations,
            'insights': insights,
            'summary_metrics': self._calculate_summary_metrics(cohorts, retention_matrix, ltv_analysis)
        }
    
    def _prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Подготовка данных для анализа"""
        
        # Копируем данные
        df = df.copy()
        
        # Преобразуем дату
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        
        # Создаем месяц и квартал
        df['month'] = df['date'].dt.to_period('M')
        df['quarter'] = df['date'].dt.to_period('Q')
        
        # Для MRR: если нет колонки mrr, используем amount
        if 'mrr' not in df.columns and 'amount' in df.columns:
            df['mrr'] = df['amount']
        
        # Группируем по клиенту и месяцу для уникальных записей
        df = df.groupby(['customer_id', 'month']).agg({
            'mrr': 'sum',
            'date': 'min'
        }).reset_index()
        
        return df
    
    def _create_cohorts(self, df: pd.DataFrame, period_type: str) -> List[Cohort]:
        """Создание когорт из данных"""
        
        cohorts = []
        
        if period_type == 'monthly':
            period_col = 'month'
        else:  # quarterly
            period_col = 'quarter'
        
        # Находим первый период для каждого клиента
        first_purchases = df.groupby('customer_id').agg({
            period_col: 'min',
            'date': 'min'
        }).reset_index()
        
        # Группируем по периоду для создания когорт
        cohort_data = first_purchases.groupby(period_col).agg({
            'customer_id': 'count',
            'date': 'min'
        }).reset_index()
        
        # Считаем общий MRR по когорте
        for _, row in cohort_data.iterrows():
            period = row[period_col]
            cohort_start = row['date'].to_timestamp()
            
            # Находим клиентов в этой когорте
            cohort_customers = first_purchases[first_purchases[period_col] == period]['customer_id'].tolist()
            
            # Считаем начальный MRR для когорты
            cohort_mrr = df[
                (df['customer_id'].isin(cohort_customers)) & 
                (df[period_col] == period)
            ]['mrr'].sum()
            
            # Создаем объект когорты
            cohort = Cohort(
                id=str(period),
                period=str(period),
                start_date=cohort_start,
                end_date=cohort_start + pd.offsets.MonthEnd(0),
                customer_count=row['customer_id'],
                total_mrr=cohort_mrr
            )
            
            cohorts.append(cohort)
        
        # Сортируем когорты по дате
        cohorts.sort(key=lambda x: x.start_date)
        
        return cohorts
    
    def _calculate_retention_matrix(self, df: pd.DataFrame, 
                                   cohorts: List[Cohort], 
                                   period_type: str) -> pd.DataFrame:
        """Расчет матрицы удержания"""
        
        if period_type == 'monthly':
            periods = sorted(df['month'].unique())
            period_col = 'month'
        else:
            periods = sorted(df['quarter'].unique())
            period_col = 'quarter'
        
        # Создаем матрицу удержания
        retention_matrix = pd.DataFrame(index=[c.period for c in cohorts], 
                                       columns=[f'Month {i}' for i in range(len(periods))])
        
        for cohort in cohorts:
            # Находим клиентов в когорте
            cohort_period = cohort.period
            cohort_customers = df[df[period_col] == pd.Period(cohort_period)]['customer_id'].unique()
            
            # Для каждого периода считаем retention
            for i, period in enumerate(periods):
                if pd.Period(cohort_period) <= period:
                    # Клиенты, которые активны в этом периоде
                    active_in_period = df[
                        (df['customer_id'].isin(cohort_customers)) & 
                        (df[period_col] == period)
                    ]['customer_id'].unique()
                    
                    # Рассчитываем retention rate
                    if len(cohort_customers) > 0:
                        retention_rate = safe_divide(len(active_in_period), len(cohort_customers))
                        retention_matrix.loc[cohort_period, f'Month {i}'] = retention_rate
                    else:
                        retention_matrix.loc[cohort_period, f'Month {i}'] = 0
        
        # Заполняем NaN нулями
        retention_matrix = retention_matrix.fillna(0)
        
        return retention_matrix
    
    def _calculate_ltv_analysis(self, df: pd.DataFrame, 
                               cohorts: List[Cohort]) -> Dict[str, Any]:
        """Расчет LTV (Lifetime Value) анализа"""
        
        ltv_results = {
            'cohort_ltv': {},
            'average_ltv': 0,
            'ltv_by_cohort': [],
            'ltv_distribution': {}
        }
        
        total_ltv = 0
        cohort_count = 0
        
        for cohort in cohorts:
            # Находим клиентов когорты
            cohort_period = pd.Period(cohort.period)
            cohort_customers = df[df['month'] == cohort_period]['customer_id'].unique()
            
            # Считаем общую выручку от этой когорты
            cohort_revenue = df[df['customer_id'].isin(cohort_customers)]['mrr'].sum()
            
            # Рассчитываем LTV на клиента
            if len(cohort_customers) > 0:
                cohort_ltv = safe_divide(cohort_revenue, len(cohort_customers))
            else:
                cohort_ltv = 0
            
            # Сохраняем результаты
            ltv_results['cohort_ltv'][cohort.period] = cohort_ltv
            ltv_results['ltv_by_cohort'].append({
                'cohort': cohort.period,
                'customer_count': len(cohort_customers),
                'total_revenue': cohort_revenue,
                'ltv_per_customer': cohort_ltv
            })
            
            total_ltv += cohort_ltv
            cohort_count += 1
        
        # Рассчитываем средний LTV
        if cohort_count > 0:
            ltv_results['average_ltv'] = safe_divide(total_ltv, cohort_count)
        
        # Распределение LTV
        ltv_values = list(ltv_results['cohort_ltv'].values())
        if ltv_values:
            ltv_results['ltv_distribution'] = {
                'mean': np.mean(ltv_values),
                'median': np.median(ltv_values),
                'std': np.std(ltv_values),
                'min': np.min(ltv_values),
                'max': np.max(ltv_values)
            }
        
        return ltv_results
    
    def _forecast_retention(self, retention_matrix: pd.DataFrame) -> Dict[str, Any]:
        """Прогноз удержания на будущие периоды"""
        
        # Берем последние когорты для прогноза
        recent_cohorts = retention_matrix.tail(min(6, len(retention_matrix)))
        
        # Рассчитываем среднюю кривую удержания
        avg_retention_curve = recent_cohorts.mean(axis=0)
        
        # Фитируем кривую удержания (используем экспоненциальный decay)
        x = np.arange(len(avg_retention_curve))
        y = avg_retention_curve.values
        
        # Убираем нулевые значения
        mask = y > 0
        if mask.sum() > 2:
            x_fit = x[mask]
            y_fit = y[mask]
            
            # Экспоненциальная регрессия: y = a * exp(-b * x)
            try:
                # Логарифмируем для линейной регрессии
                log_y = np.log(y_fit)
                slope, intercept, r_value, p_value, std_err = stats.linregress(x_fit, log_y)
                
                a = np.exp(intercept)
                b = -slope
                
                # Прогноз на следующие 12 месяцев
                forecast_months = 12
                x_forecast = np.arange(len(avg_retention_curve) + forecast_months)
                y_forecast = a * np.exp(-b * x_forecast)
                
                # Ограничиваем прогноз между 0 и 1
                y_forecast = np.clip(y_forecast, 0, 1)
                
                forecast = {
                    'months': x_forecast.tolist(),
                    'retention_forecast': y_forecast.tolist(),
                    'params': {'a': float(a), 'b': float(b)},
                    'r_squared': float(r_value ** 2),
                    'churn_rate': float(b)  # Monthly churn rate
                }
                
            except:
                # Если регрессия не удалась, используем простую экстраполяцию
                forecast = {
                    'months': x_forecast.tolist(),
                    'retention_forecast': list(y) + [y[-1]] * forecast_months,
                    'params': None,
                    'r_squared': 0,
                    'churn_rate': 0.1  # Default
                }
        else:
            # Недостаточно данных для прогноза
            forecast = {
                'months': list(range(24)),
                'retention_forecast': [0.5] * 24,
                'params': None,
                'r_squared': 0,
                'churn_rate': 0.1
            }
        
        return forecast
    
    def _create_visualizations(self, retention_matrix: pd.DataFrame,
                              ltv_analysis: Dict[str, Any],
                              forecast: Dict[str, Any]) -> Dict[str, Any]:
        """Создание визуализаций для когортного анализа"""
        
        visualizations = {}
        
        # 1. Heatmap удержания
        fig_heatmap = go.Figure(data=go.Heatmap(
            z=retention_matrix.values,
            x=retention_matrix.columns,
            y=retention_matrix.index,
            colorscale='RdYlGn',
            zmin=0,
            zmax=1,
            colorbar=dict(title="Retention Rate")
        ))
        
        fig_heatmap.update_layout(
            title="Cohort Retention Heatmap",
            xaxis_title="Months Since Acquisition",
            yaxis_title="Cohort",
            height=500
        )
        
        visualizations['retention_heatmap'] = fig_heatmap
        
        # 2. Кривые удержания
        fig_retention = go.Figure()
        
        # Добавляем каждую когорту
        for cohort in retention_matrix.index:
            fig_retention.add_trace(go.Scatter(
                x=retention_matrix.columns,
                y=retention_matrix.loc[cohort],
                mode='lines+markers',
                name=cohort,
                opacity=0.7
            ))
        
        # Добавляем прогноз
        if forecast['retention_forecast']:
            fig_retention.add_trace(go.Scatter(
                x=[f'Month {i}' for i in forecast['months']],
                y=forecast['retention_forecast'],
                mode='lines',
                name='Forecast',
                line=dict(dash='dash', color='black', width=3)
            ))
        
        fig_retention.update_layout(
            title="Cohort Retention Curves",
            xaxis_title="Months Since Acquisition",
            yaxis_title="Retention Rate",
            yaxis=dict(tickformat=".0%"),
            height=500
        )
        
        visualizations['retention_curves'] = fig_retention
        
        # 3. LTV по когортам
        ltv_by_cohort = pd.DataFrame(ltv_analysis['ltv_by_cohort'])
        if not ltv_by_cohort.empty:
            fig_ltv = px.bar(
                ltv_by_cohort,
                x='cohort',
                y='ltv_per_customer',
                title="LTV by Cohort",
                labels={'ltv_per_customer': 'LTV per Customer', 'cohort': 'Cohort'}
            )
            
            fig_ltv.update_layout(
                yaxis_title="LTV (руб.)",
                height=400
            )
            
            visualizations['ltv_by_cohort'] = fig_ltv
        
        # 4. Распределение LTV
        if ltv_analysis['ltv_distribution']:
            ltv_dist = ltv_analysis['ltv_distribution']
            
            # Создаем box plot для распределения LTV
            ltv_values = list(ltv_analysis['cohort_ltv'].values())
            
            fig_dist = go.Figure()
            
            fig_dist.add_trace(go.Box(
                y=ltv_values,
                name="LTV Distribution",
                boxpoints='all',
                jitter=0.3,
                pointpos=-1.8
            ))
            
            fig_dist.update_layout(
                title="LTV Distribution Across Cohorts",
                yaxis_title="LTV (руб.)",
                height=400
            )
            
            visualizations['ltv_distribution'] = fig_dist
        
        return visualizations
    
    def _generate_insights(self, cohorts: List[Cohort],
                          retention_matrix: pd.DataFrame,
                          ltv_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Генерация инсайтов из анализа когорт"""
        
        insights = []
        
        # 1. Анализ трендов удержания
        if len(cohorts) >= 3:
            # Сравниваем первые и последние когорты
            early_cohorts = retention_matrix.head(3).mean(axis=1)
            late_cohorts = retention_matrix.tail(3).mean(axis=1)
            
            early_avg = early_cohorts.mean()
            late_avg = late_cohorts.mean()
            
            if late_avg > early_avg * 1.1:
                insights.append({
                    'type': 'positive',
                    'title': 'Улучшение удержания клиентов',
                    'description': f'Последние когорты показывают на {((late_avg/early_avg)-1)*100:.1f}% лучшее удержание',
                    'impact': 'Увеличение LTV и снижение CAC payback',
                    'action': 'Продолжать текущие практики onboarding и customer success'
                })
            elif late_avg < early_avg * 0.9:
                insights.append({
                    'type': 'warning',
                    'title': 'Ухудшение удержания клиентов',
                    'description': f'Последние когорты показывают на {((1-late_avg/early_avg))*100:.1f}% худшее удержание',
                    'impact': 'Снижение LTV и увеличение CAC payback',
                    'action': 'Исследовать причины ухудшения удержания'
                })
        
        # 2. Анализ LTV трендов
        ltv_by_cohort = ltv_analysis.get('ltv_by_cohort', [])
        if len(ltv_by_cohort) >= 3:
            ltv_values = [c['ltv_per_customer'] for c in ltv_by_cohort]
            
            # Проверяем рост LTV
            if ltv_values[-1] > ltv_values[0] * 1.2:
                insights.append({
                    'type': 'positive',
                    'title': 'Рост LTV',
                    'description': f'LTV вырос на {((ltv_values[-1]/ltv_values[0])-1)*100:.1f}% с первых когорт',
                    'impact': 'Улучшение unit economics и рентабельности',
                    'action': 'Продолжать стратегии увеличения ценности клиента'
                })
        
        # 3. Анализ стабильности удержания
        retention_std = retention_matrix.std(axis=0).mean()
        if retention_std < 0.1:
            insights.append({
                'type': 'positive',
                'title': 'Стабильное удержание',
                'description': 'Когорты показывают стабильные паттерны удержания',
                'impact': 'Прогнозируемый cash flow и надежная бизнес-модель',
                'action': 'Использовать стабильные метрики для планирования'
            })
        elif retention_std > 0.2:
            insights.append({
                'type': 'warning',
                'title': 'Нестабильное удержание',
                'description': 'Большие различия в удержании между когортами',
                'impact': 'Сложности с прогнозированием и планированием',
                'action': 'Исследовать причины нестабильности удержания'
            })
        
        # 4. Расчет ожидаемого lifetime
        if 'churn_rate' in ltv_analysis.get('forecast', {}):
            churn_rate = ltv_analysis['forecast']['churn_rate']
            if churn_rate > 0:
                expected_lifetime = safe_divide(1, churn_rate)
                
                if expected_lifetime < 6:
                    insights.append({
                        'type': 'critical',
                        'title': 'Короткий жизненный цикл клиентов',
                        'description': f'Ожидаемый lifetime: {expected_lifetime:.1f} месяцев',
                        'impact': 'Высокий churn, низкий LTV, сложности с масштабированием',
                        'action': 'Срочно улучшать удержание клиентов'
                    })
                elif expected_lifetime > 24:
                    insights.append({
                        'type': 'positive',
                        'title': 'Долгосрочные клиенты',
                        'description': f'Ожидаемый lifetime: {expected_lifetime:.1f} месяцев',
                        'impact': 'Высокий LTV, стабильный cash flow',
                        'action': 'Фокусироваться на expansion revenue от существующих клиентов'
                    })
        
        return insights
    
    def _calculate_summary_metrics(self, cohorts: List[Cohort],
                                  retention_matrix: pd.DataFrame,
                                  ltv_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Расчет сводных метрик"""
        
        summary = {}
        
        # Общие метрики
        total_customers = sum(c.customer_count for c in cohorts)
        total_mrr = sum(c.total_mrr for c in cohorts)
        
        summary['total_cohorts'] = len(cohorts)
        summary['total_customers'] = total_customers
        summary['total_mrr'] = total_mrr
        summary['avg_customers_per_cohort'] = total_customers / len(cohorts) if cohorts else 0
        
        # Retention metrics
        if not retention_matrix.empty:
            # Среднее удержание в первый месяц
            first_month_retention = retention_matrix.iloc[:, 0].mean() if len(retention_matrix.columns) > 0 else 0
            
            # Удержание через 3, 6, 12 месяцев
            month_3_col = min(2, len(retention_matrix.columns) - 1)
            month_6_col = min(5, len(retention_matrix.columns) - 1)
            month_12_col = min(11, len(retention_matrix.columns) - 1)
            
            retention_3m = retention_matrix.iloc[:, month_3_col].mean() if month_3_col >= 0 else 0
            retention_6m = retention_matrix.iloc[:, month_6_col].mean() if month_6_col >= 0 else 0
            retention_12m = retention_matrix.iloc[:, month_12_col].mean() if month_12_col >= 0 else 0
            
            summary['retention_metrics'] = {
                'first_month': first_month_retention,
                'month_3': retention_3m,
                'month_6': retention_6m,
                'month_12': retention_12m
            }
            
            # Расчет churn rate
            if first_month_retention > 0:
                monthly_churn = 1 - retention_3m ** (1/3) if retention_3m > 0 else 0.1
                summary['estimated_monthly_churn'] = monthly_churn
                summary['estimated_customer_lifetime'] = 1 / monthly_churn if monthly_churn > 0 else 0
        
        # LTV metrics
        if ltv_analysis:
            summary['ltv_metrics'] = {
                'average_ltv': ltv_analysis.get('average_ltv', 0),
                'ltv_distribution': ltv_analysis.get('ltv_distribution', {})
            }
        
        # Качество данных
        data_quality = {
            'cohorts_with_data': len([c for c in cohorts if c.customer_count > 0]),
            'total_periods_analyzed': len(retention_matrix.columns) if not retention_matrix.empty else 0,
            'data_completeness': 'good' if len(cohorts) >= 3 else 'limited'
        }
        
        summary['data_quality'] = data_quality
        
        return summary
    
    def calculate_ltv(self, avg_mrr: float, churn_rate: float, 
                     discount_rate: float = 0.1, periods: int = 60) -> Dict[str, Any]:
        """
        Расчет Lifetime Value (LTV) клиента
        
        Args:
            avg_mrr: Средний MRR на клиента
            churn_rate: Месячный процент оттока
            discount_rate: Ставка дисконтирования (для расчета present value)
            periods: Количество периодов для расчета
        
        Returns:
            Dict с расчетами LTV
        """
        
        # Простой LTV (без дисконтирования)
        if churn_rate > 0:
            simple_ltv = safe_divide(avg_mrr, churn_rate)
        else:
            simple_ltv = avg_mrr * periods
        
        # LTV с дисконтированием
        discounted_ltv = 0
        for t in range(1, periods + 1):
            survival_probability = (1 - churn_rate) ** t
            discounted_value = (avg_mrr * survival_probability) / ((1 + discount_rate/12) ** t)
            discounted_ltv += discounted_value
        
        # Расчет payback period (сколько месяцев нужно для окупаемости CAC)
        # Предполагаем, что CAC известен
        
        return {
            'simple_ltv': simple_ltv,
            'discounted_ltv': discounted_ltv,
            'customer_lifetime_months': safe_divide(1, churn_rate, periods) if churn_rate > 0 else periods,
            'formula_used': 'LTV = MRR / Churn Rate',
            'assumptions': {
                'avg_mrr': avg_mrr,
                'churn_rate': churn_rate,
                'discount_rate': discount_rate,
                'periods': periods
            }
        }
    
    def simulate_cohort_ltv(self, initial_customers: int, avg_mrr: float,
                           churn_rate: float, growth_rate: float = 0.0,
                           periods: int = 36) -> pd.DataFrame:
        """
        Симуляция LTV для когорты клиентов
        
        Args:
            initial_customers: Начальное количество клиентов
            avg_mrr: Средний MRR на клиента
            churn_rate: Месячный процент оттока
            growth_rate: Месячный рост MRR на клиента (expansion)
            periods: Количество периодов для симуляции
        
        Returns:
            DataFrame с симуляцией
        """
        
        # Создаем DataFrame для симуляции
        simulation_data = []
        
        remaining_customers = initial_customers
        cumulative_revenue = 0
        
        for month in range(periods):
            # Количество клиентов в этом месяце
            customers_this_month = remaining_customers
            
            # Выручка в этом месяце
            monthly_revenue = customers_this_month * avg_mrr * ((1 + growth_rate) ** month)
            
            # Накопленная выручка
            cumulative_revenue += monthly_revenue
            
            # Сохраняем данные
            simulation_data.append({
                'month': month,
                'customers': customers_this_month,
                'monthly_revenue': monthly_revenue,
                'cumulative_revenue': cumulative_revenue,
                'avg_revenue_per_customer': monthly_revenue / customers_this_month if customers_this_month > 0 else 0
            })
            
            # Обновляем количество клиентов на следующий месяц
            remaining_customers = remaining_customers * (1 - churn_rate)
        
        simulation_df = pd.DataFrame(simulation_data)
        
        # Добавляем расчеты LTV
        simulation_df['ltv_to_date'] = simulation_df['cumulative_revenue'].apply(
            lambda value: safe_divide(value, initial_customers)
        )
        
        return simulation_df
    
    def analyze_seasonal_patterns(self, transaction_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Анализ сезонных паттернов в привлечении и удержании клиентов
        
        Args:
            transaction_data: DataFrame с транзакциями
        
        Returns:
            Dict с анализом сезонности
        """
        
        df = self._prepare_data(transaction_data)
        
        # Добавляем сезонные признаки
        df['year'] = df['date'].dt.year
        df['month_num'] = df['date'].dt.month
        df['quarter_num'] = df['date'].dt.quarter
        df['month_name'] = df['date'].dt.month.apply(lambda x: self.month_names.get(x, ''))
        
        # Анализ привлечения по месяцам
        acquisition_by_month = df.groupby(['year', 'month_num', 'month_name']).agg({
            'customer_id': 'nunique',
            'mrr': 'sum'
        }).reset_index()
        
        # Анализ удержания по месяцам
        # Находим первый месяц для каждого клиента
        first_purchases = df.groupby('customer_id').agg({
            'month_num': 'min',
            'year': 'min'
        }).reset_index()
        
        # Объединяем с исходными данными для анализа retention
        df_with_cohort = df.merge(first_purchases, on='customer_id', 
                                  suffixes=('', '_first'))
        
        # Анализ retention по когортам по месяцам
        retention_by_cohort_month = []
        
        for (cohort_year, cohort_month), cohort_df in df_with_cohort.groupby(['year_first', 'month_num_first']):
            cohort_size = cohort_df['customer_id'].nunique()
            
            # Анализируем retention в последующие месяцы
            for months_after in range(1, 13):
                target_year = cohort_year + ((cohort_month + months_after - 1) // 12)
                target_month = ((cohort_month + months_after - 1) % 12) + 1
                
                active_in_period = df_with_cohort[
                    (df_with_cohort['customer_id'].isin(cohort_df['customer_id'])) &
                    (df_with_cohort['year'] == target_year) &
                    (df_with_cohort['month_num'] == target_month)
                ]['customer_id'].nunique()
                
                retention_rate = active_in_period / cohort_size if cohort_size > 0 else 0
                
                retention_by_cohort_month.append({
                    'cohort_year': cohort_year,
                    'cohort_month': cohort_month,
                    'cohort_month_name': self.month_names.get(cohort_month, ''),
                    'months_after': months_after,
                    'cohort_size': cohort_size,
                    'retained_customers': active_in_period,
                    'retention_rate': retention_rate
                })
        
        retention_df = pd.DataFrame(retention_by_cohort_month)
        
        # Анализ сезонности в retention
        seasonal_patterns = {}
        if not retention_df.empty:
            # Среднее удержание по месяцам когорты
            retention_by_cohort_month_avg = retention_df.groupby('cohort_month').agg({
                'retention_rate': 'mean'
            }).reset_index()
            
            seasonal_patterns['retention_by_acquisition_month'] = retention_by_cohort_month_avg.to_dict('records')
        
        # Визуализация сезонности
        visualizations = {}
        
        # График привлечения по месяцам
        if not acquisition_by_month.empty:
            fig_acquisition = px.line(
                acquisition_by_month,
                x='month_name',
                y='customer_id',
                color='year',
                title="Customer Acquisition by Month",
                labels={'customer_id': 'New Customers', 'month_name': 'Month'}
            )
            
            fig_acquisition.update_layout(height=400)
            visualizations['acquisition_by_month'] = fig_acquisition
        
        return {
            'acquisition_patterns': acquisition_by_month.to_dict('records'),
            'retention_patterns': seasonal_patterns,
            'seasonal_insights': self._generate_seasonal_insights(acquisition_by_month, retention_df),
            'visualizations': visualizations
        }
    
    def _generate_seasonal_insights(self, acquisition_data: pd.DataFrame,
                                   retention_data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Генерация инсайтов о сезонности"""
        
        insights = []
        
        # Анализ сезонности в привлечении
        if not acquisition_data.empty:
            # Находим лучший и худший месяцы для привлечения
            avg_by_month = acquisition_data.groupby('month_name').agg({
                'customer_id': 'mean'
            }).reset_index()
            
            best_month = avg_by_month.loc[avg_by_month['customer_id'].idxmax()]
            worst_month = avg_by_month.loc[avg_by_month['customer_id'].idxmin()]
            
            if best_month['customer_id'] > worst_month['customer_id'] * 1.5:
                insights.append({
                    'type': 'info',
                    'title': 'Сильная сезонность в привлечении',
                    'description': f'{best_month["month_name"]} лучше для привлечения, чем {worst_month["month_name"]}',
                    'recommendation': 'Увеличить маркетинговый бюджет в пиковые месяцы'
                })
        
        # Анализ сезонности в удержании
        if not retention_data.empty and 'retention_rate' in retention_data.columns:
            # Проверяем, есть ли различия в retention по месяцам когорты
            retention_by_cohort_month = retention_data.groupby('cohort_month_name').agg({
                'retention_rate': 'mean'
            }).reset_index()
            
            if len(retention_by_cohort_month) > 1:
                retention_std = retention_by_cohort_month['retention_rate'].std()
                if retention_std > 0.1:
                    insights.append({
                        'type': 'warning',
                        'title': 'Сезонность в удержании',
                        'description': 'Удержание клиентов зависит от месяца привлечения',
                        'recommendation': 'Адаптировать onboarding под сезонные когорты'
                    })
        
        return insights
    
    def calculate_cac_ltv_ratio(self, cac: float, ltv: float, 
                               include_details: bool = True) -> Dict[str, Any]:
        """
        Расчет соотношения CAC:LTV
        
        Args:
            cac: Customer Acquisition Cost
            ltv: Lifetime Value
            include_details: Включать детальный анализ
        
        Returns:
            Dict с анализом соотношения
        """
        
        ratio = ltv / cac if cac > 0 else 0
        
        # Оценка соотношения
        if ratio >= 3.0:
            rating = "Excellent"
            color = "green"
            assessment = "Здоровое соотношение, бизнес масштабируем"
        elif ratio >= 2.0:
            rating = "Good"
            color = "blue"
            assessment = "Хорошее соотношение, можно масштабировать"
        elif ratio >= 1.5:
            rating = "Fair"
            color = "yellow"
            assessment = "Соотношение на границе, требуется оптимизация"
        elif ratio >= 1.0:
            rating = "Concerning"
            color = "orange"
            assessment = "Рискованное соотношение, требуется срочная оптимизация"
        else:
            rating = "Critical"
            color = "red"
            assessment = "Критическое соотношение, бизнес нежизнеспособен"
        
        result = {
            'cac': cac,
            'ltv': ltv,
            'ratio': ratio,
            'rating': rating,
            'color': color,
            'assessment': assessment,
            'benchmark': {
                'saas_standard': 3.0,
                'minimum_viable': 1.5,
                'excellent': 5.0
            }
        }
        
        if include_details:
            # Детальный анализ
            payback_period = cac / (ltv / 12) if ltv > 0 else 0  # В месяцах
            
            result['details'] = {
                'payback_period_months': payback_period,
                'months_to_breakeven': payback_period,
                'gross_margin_required': cac / ltv if ltv > 0 else 1,
                'scalability_score': min(100, ratio * 20)  # 0-100 score
            }
            
            # Рекомендации
            recommendations = []
            if ratio < 1.5:
                recommendations.extend([
                    "Снизить CAC через оптимизацию маркетинговых каналов",
                    "Увеличить LTV через улучшение удержания и upsell",
                    "Пересмотреть pricing strategy",
                    "Фокусироваться на organic growth каналах"
                ])
            elif ratio < 3.0:
                recommendations.extend([
                    "Постепенно увеличивать маркетинговые инвестиции",
                    "Экспериментировать с новыми каналами привлечения",
                    "Улучшать unit economics через операционную эффективность"
                ])
            else:
                recommendations.extend([
                    "Агрессивно масштабировать маркетинговые инвестиции",
                    "Экспериментировать с новыми рынками",
                    "Рассмотреть возможность снижения цен для ускорения роста"
                ])
            
            result['recommendations'] = recommendations
        
        return result

# Создаем глобальный экземпляр анализатора
cohort_analyzer = RealisticCohortAnalyzer()

# Экспортируем полезные функции
def analyze_cohorts_data(transaction_data: pd.DataFrame, 
                        period_type: str = 'monthly') -> Dict[str, Any]:
    """Публичная функция для анализа когорт"""
    return cohort_analyzer.analyze_cohorts(transaction_data, period_type)

def calculate_customer_ltv(avg_mrr: float, churn_rate: float, 
                          discount_rate: float = 0.1, 
                          periods: int = 60) -> Dict[str, Any]:
    """Публичная функция для расчета LTV"""
    return cohort_analyzer.calculate_ltv(avg_mrr, churn_rate, discount_rate, periods)

def analyze_seasonality(transaction_data: pd.DataFrame) -> Dict[str, Any]:
    """Публичная функция для анализа сезонности"""
    return cohort_analyzer.analyze_seasonal_patterns(transaction_data)
