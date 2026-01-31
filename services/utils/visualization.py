"""
Визуализация данных для SaaS метрик
Создание графиков и dashboard с использованием Plotly и Matplotlib
"""

import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Для работы без GUI
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
import json
import io
import base64

from services.utils.math_utils import safe_divide

class VisualizationEngine:
    """
    Движок визуализации для SaaS метрик
    Создание графиков, dashboard и визуальных отчетов
    """
    
    def __init__(self):
        # Настройка цветовых схем
        self.color_schemes = {
            'sequential': px.colors.sequential.Blues,
            'diverging': px.colors.diverging.RdYlBu,
            'qualitative': px.colors.qualitative.Set3,
            'saas': ['#2E86C1', '#3498DB', '#5DADE2', '#85C1E9', '#AED6F1', '#D6EAF8']
        }
        
        # Настройка стилей Plotly
        self.setup_plotly_theme()
        
        # Настройка стилей Matplotlib
        self.setup_matplotlib_style()
    
    def setup_plotly_theme(self):
        """Настройка темы Plotly"""
        
        pio.templates["saas_theme"] = go.layout.Template(
            layout=go.Layout(
                font=dict(family="Arial, sans-serif", size=12),
                title=dict(font=dict(size=20, color='#2C3E50')),
                plot_bgcolor='white',
                paper_bgcolor='white',
                xaxis=dict(
                    gridcolor='#ecf0f1',
                    linecolor='#bdc3c7',
                    zerolinecolor='#bdc3c7'
                ),
                yaxis=dict(
                    gridcolor='#ecf0f1',
                    linecolor='#bdc3c7',
                    zerolinecolor='#bdc3c7'
                ),
                colorway=self.color_schemes['saas']
            )
        )
        
        pio.templates.default = "plotly_white+saas_theme"
    
    def setup_matplotlib_style(self):
        """Настройка стилей Matplotlib"""
        
        plt.style.use('seaborn-v0_8-whitegrid')
        sns.set_palette(self.color_schemes['saas'])
        
        # Кастомные настройки
        matplotlib.rcParams.update({
            'font.size': 10,
            'axes.titlesize': 14,
            'axes.labelsize': 12,
            'xtick.labelsize': 10,
            'ytick.labelsize': 10,
            'legend.fontsize': 10,
            'figure.titlesize': 16,
            'figure.figsize': (10, 6),
            'savefig.dpi': 100,
            'savefig.bbox': 'tight',
            'savefig.pad_inches': 0.1
        })
    
    def create_mrr_growth_chart(self, monthly_data: List[Dict[str, Any]], 
                               title: str = "MRR Growth Over Time") -> go.Figure:
        """
        Создание графика роста MRR
        
        Args:
            monthly_data: Месячные данные
            title: Заголовок графика
        
        Returns:
            Plotly Figure
        """
        
        if not monthly_data:
            return self._create_empty_chart("No data available")
        
        # Подготовка данных
        df = pd.DataFrame(monthly_data)
        
        # Проверка необходимых колонок
        if 'month_name' not in df.columns or 'plan_mrr' not in df.columns:
            return self._create_empty_chart("Missing required columns")
        
        fig = go.Figure()
        
        # Линия MRR
        fig.add_trace(go.Scatter(
            x=df['month_name'],
            y=df['plan_mrr'],
            mode='lines+markers',
            name='MRR',
            line=dict(color='#2E86C1', width=3),
            marker=dict(size=8)
        ))
        
        # Заполнение под линией
        fig.add_trace(go.Scatter(
            x=df['month_name'],
            y=df['plan_mrr'],
            mode='none',
            name='MRR Area',
            fill='tozeroy',
            fillcolor='rgba(46, 134, 193, 0.2)',
            showlegend=False
        ))
        
        # Добавление аннотаций для значительных изменений
        if len(df) > 1:
            for i in range(1, len(df)):
                prev_mrr = df.iloc[i-1]['plan_mrr']
                curr_mrr = df.iloc[i]['plan_mrr']
                
                if prev_mrr > 0:
                    growth = safe_divide(curr_mrr - prev_mrr, prev_mrr)
                    
                    if abs(growth) > 0.2:  # Изменение более 20%
                        fig.add_annotation(
                            x=df.iloc[i]['month_name'],
                            y=curr_mrr,
                            text=f"{growth:+.1%}",
                            showarrow=True,
                            arrowhead=2,
                            arrowsize=1,
                            arrowwidth=2,
                            arrowcolor='#E74C3C' if growth < 0 else '#27AE60',
                            font=dict(color='#E74C3C' if growth < 0 else '#27AE60', size=10)
                        )
        
        # Настройка layout
        fig.update_layout(
            title=dict(text=title, x=0.5, xanchor='center'),
            xaxis_title="Month",
            yaxis_title="MRR ($)",
            hovermode='x unified',
            height=500,
            showlegend=True
        )
        
        # Добавление линии тренда если достаточно данных
        if len(df) >= 3:
            try:
                x_numeric = list(range(len(df)))
                y_values = df['plan_mrr'].values
                
                # Linear regression
                coeffs = np.polyfit(x_numeric, y_values, 1)
                trend_line = np.polyval(coeffs, x_numeric)
                
                fig.add_trace(go.Scatter(
                    x=df['month_name'],
                    y=trend_line,
                    mode='lines',
                    name='Trend Line',
                    line=dict(color='#E74C3C', width=2, dash='dash'),
                    opacity=0.7
                ))
            except:
                pass
        
        return fig
    
    def create_burn_rate_chart(self, monthly_data: List[Dict[str, Any]],
                              title: str = "Burn Rate Analysis") -> go.Figure:
        """
        Создание графика burn rate
        
        Args:
            monthly_data: Месячные данные
            title: Заголовок графика
        
        Returns:
            Plotly Figure
        """
        
        if not monthly_data:
            return self._create_empty_chart("No data available")
        
        df = pd.DataFrame(monthly_data)
        
        # Проверка необходимых колонок
        required_cols = ['month_name', 'plan_total_revenue', 'plan_total_costs', 'plan_burn_rate']
        if not all(col in df.columns for col in required_cols):
            return self._create_empty_chart("Missing required columns")
        
        fig = go.Figure()
        
        # Revenue Bar
        fig.add_trace(go.Bar(
            x=df['month_name'],
            y=df['plan_total_revenue'],
            name='Revenue',
            marker_color='#27AE60',
            opacity=0.7
        ))
        
        # Costs Bar
        fig.add_trace(go.Bar(
            x=df['month_name'],
            y=df['plan_total_costs'],
            name='Costs',
            marker_color='#E74C3C',
            opacity=0.7
        ))
        
        # Burn Rate Line
        fig.add_trace(go.Scatter(
            x=df['month_name'],
            y=df['plan_burn_rate'],
            mode='lines+markers',
            name='Burn Rate',
            line=dict(color='#2C3E50', width=3),
            yaxis='y2'
        ))
        
        # Zero Line
        fig.add_hline(y=0, line_dash="dash", line_color="gray", 
                     annotation_text="Break-even", annotation_position="bottom right")
        
        # Настройка layout
        fig.update_layout(
            title=dict(text=title, x=0.5, xanchor='center'),
            xaxis_title="Month",
            yaxis_title="Amount ($)",
            yaxis2=dict(
                title="Burn Rate ($)",
                overlaying='y',
                side='right',
                showgrid=False
            ),
            barmode='group',
            hovermode='x unified',
            height=500,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
    
    def create_runway_chart(self, monthly_data: List[Dict[str, Any]],
                           cash_balance: float = 0,
                           title: str = "Runway Projection") -> go.Figure:
        """
        Создание графика runway
        
        Args:
            monthly_data: Месячные данные
            cash_balance: Начальный cash balance
            title: Заголовок графика
        
        Returns:
            Plotly Figure
        """
        
        if not monthly_data:
            return self._create_empty_chart("No data available")
        
        df = pd.DataFrame(monthly_data)
        
        # Проверка необходимых колонок
        if 'month_name' not in df.columns or 'plan_burn_rate' not in df.columns:
            return self._create_empty_chart("Missing required columns")
        
        # Расчет cumulative cash
        cumulative_cash = cash_balance
        cash_data = []
        
        for _, row in df.iterrows():
            burn_rate = row['plan_burn_rate']
            cumulative_cash -= burn_rate
            cash_data.append(cumulative_cash)
        
        df['cumulative_cash'] = cash_data
        
        fig = go.Figure()
        
        # Cumulative Cash Area
        fig.add_trace(go.Scatter(
            x=df['month_name'],
            y=df['cumulative_cash'],
            mode='lines',
            name='Cash Balance',
            line=dict(color='#3498DB', width=3),
            fill='tozeroy',
            fillcolor='rgba(52, 152, 219, 0.3)'
        ))
        
        # Zero Line
        fig.add_hline(y=0, line_dash="dash", line_color="#E74C3C", 
                     annotation_text="Cash Out", annotation_position="bottom right")
        
        # Нахождение месяца когда заканчиваются деньги
        cash_out_month = None
        for i, cash in enumerate(df['cumulative_cash']):
            if cash <= 0:
                cash_out_month = df.iloc[i]['month_name']
                break
        
        if cash_out_month:
            fig.add_vline(x=cash_out_month, line_dash="dot", line_color="#E74C3C",
                         annotation_text=f"Cash Out: {cash_out_month}", 
                         annotation_position="top")
        
        # Добавление аннотаций для критических уровней
        warning_level = cash_balance * 0.25
        critical_level = cash_balance * 0.1
        
        if warning_level > 0:
            fig.add_hline(y=warning_level, line_dash="dot", line_color="#F39C12",
                         annotation_text="Warning Level", annotation_position="left")
        
        if critical_level > 0:
            fig.add_hline(y=critical_level, line_dash="dot", line_color="#E74C3C",
                         annotation_text="Critical Level", annotation_position="left")
        
        # Настройка layout
        fig.update_layout(
            title=dict(text=title, x=0.5, xanchor='center'),
            xaxis_title="Month",
            yaxis_title="Cash Balance ($)",
            hovermode='x unified',
            height=500,
            showlegend=True
        )
        
        return fig
    
    def create_ltv_cac_chart(self, metrics_data: Dict[str, Any],
                            title: str = "LTV/CAC Analysis") -> go.Figure:
        """
        Создание графика LTV/CAC analysis
        
        Args:
            metrics_data: Данные метрик
            title: Заголовок графика
        
        Returns:
            Plotly Figure
        """
        
        if not metrics_data:
            return self._create_empty_chart("No data available")
        
        # Подготовка данных
        ltv = metrics_data.get('ltv', 0)
        cac = metrics_data.get('cac', 0)
        ltv_cac_ratio = metrics_data.get('ltv_cac_ratio', 0)
        
        if ltv == 0 or cac == 0:
            return self._create_empty_chart("Insufficient data for LTV/CAC analysis")
        
        fig = go.Figure()
        
        # Bar chart для LTV и CAC
        fig.add_trace(go.Bar(
            x=['LTV', 'CAC'],
            y=[ltv, cac],
            name='Value',
            marker_color=['#27AE60', '#E74C3C'],
            text=[f"${ltv:,.0f}", f"${cac:,.0f}"],
            textposition='auto'
        ))
        
        # Добавление LTV/CAC ratio как аннотация
        fig.add_annotation(
            x=0.5,
            y=max(ltv, cac) * 1.1,
            text=f"LTV/CAC Ratio: {ltv_cac_ratio:.1f}x",
            showarrow=False,
            font=dict(size=14, color='#2C3E50')
        )
        
        # Добавление benchmark линий
        benchmarks = {
            'Poor (<1x)': 1.0,
            'Minimum (3x)': 3.0,
            'Good (5x)': 5.0,
            'Excellent (8x)': 8.0
        }
        
        for label, value in benchmarks.items():
            benchmark_ltv = value * cac
            
            # Добавляем только если benchmark LTV в пределах графика
            if benchmark_ltv <= ltv * 1.5:
                fig.add_hline(y=benchmark_ltv, line_dash="dot", 
                             line_color=self._get_benchmark_color(value),
                             annotation_text=label, 
                             annotation_position="right",
                             annotation_font_size=10)
        
        # Настройка layout
        fig.update_layout(
            title=dict(text=title, x=0.5, xanchor='center'),
            yaxis_title="Value ($)",
            showlegend=False,
            height=500
        )
        
        return fig
    
    def _get_benchmark_color(self, ratio: float) -> str:
        """Получение цвета для benchmark линии"""
        
        if ratio >= 8:
            return '#27AE60'  # Green
        elif ratio >= 5:
            return '#2ECC71'  # Light Green
        elif ratio >= 3:
            return '#F39C12'  # Orange
        else:
            return '#E74C3C'  # Red
    
    def create_customer_metrics_chart(self, monthly_data: List[Dict[str, Any]],
                                     title: str = "Customer Metrics") -> go.Figure:
        """
        Создание графика customer metrics
        
        Args:
            monthly_data: Месячные данные
            title: Заголовок графика
        
        Returns:
            Plotly Figure
        """
        
        if not monthly_data:
            return self._create_empty_chart("No data available")
        
        df = pd.DataFrame(monthly_data)
        
        # Проверка необходимых колонок
        required_cols = ['month_name', 'plan_new_customers', 'plan_churn_rate']
        if not all(col in df.columns for col in required_cols):
            return self._create_empty_chart("Missing required columns")
        
        fig = go.Figure()
        
        # New Customers Bar
        fig.add_trace(go.Bar(
            x=df['month_name'],
            y=df['plan_new_customers'],
            name='New Customers',
            marker_color='#27AE60',
            opacity=0.7
        ))
        
        # Churn Rate Line
        fig.add_trace(go.Scatter(
            x=df['month_name'],
            y=df['plan_churn_rate'] * 100,  # Convert to percentage
            mode='lines+markers',
            name='Churn Rate (%)',
            line=dict(color='#E74C3C', width=3),
            yaxis='y2'
        ))
        
        # Net New Customers (если есть данные)
        if 'plan_net_new_customers' in df.columns:
            fig.add_trace(go.Bar(
                x=df['month_name'],
                y=df['plan_net_new_customers'],
                name='Net New Customers',
                marker_color='#3498DB',
                opacity=0.7
            ))
        
        # Настройка layout
        fig.update_layout(
            title=dict(text=title, x=0.5, xanchor='center'),
            xaxis_title="Month",
            yaxis_title="Number of Customers",
            yaxis2=dict(
                title="Churn Rate (%)",
                overlaying='y',
                side='right',
                showgrid=False,
                range=[0, max(df['plan_churn_rate'] * 100) * 1.2]
            ),
            barmode='group',
            hovermode='x unified',
            height=500,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
    
    def create_financial_health_dashboard(self, company_data: Dict[str, Any],
                                         metrics_data: Dict[str, Any],
                                         monthly_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Создание dashboard финансового здоровья
        
        Args:
            company_data: Данные компании
            metrics_data: Данные метрик
            monthly_data: Месячные данные
        
        Returns:
            Dict с графиками dashboard
        """
        
        dashboard = {
            'metrics_cards': self._create_metrics_cards(company_data, metrics_data),
            'charts': {},
            'alerts': []
        }
        
        # Создание графиков
        if monthly_data:
            dashboard['charts']['mrr_growth'] = self.create_mrr_growth_chart(monthly_data)
            dashboard['charts']['burn_rate'] = self.create_burn_rate_chart(monthly_data)
            dashboard['charts']['runway'] = self.create_runway_chart(
                monthly_data, company_data.get('cash_balance', 0)
            )
            dashboard['charts']['customer_metrics'] = self.create_customer_metrics_chart(monthly_data)
        
        # Создание LTV/CAC графика если есть данные
        if metrics_data and 'ltv' in metrics_data and 'cac' in metrics_data:
            dashboard['charts']['ltv_cac'] = self.create_ltv_cac_chart(metrics_data)
        
        # Генерация alerts
        dashboard['alerts'] = self._generate_financial_alerts(company_data, metrics_data)
        
        return dashboard
    
    def _create_metrics_cards(self, company_data: Dict[str, Any],
                             metrics_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Создание cards с ключевыми метриками"""
        
        cards = []
        
        # 1. MRR Card
        mrr = company_data.get('current_mrr', 0)
        growth_rate = metrics_data.get('growth_rate', 0) * 100
        
        cards.append({
            'title': 'Monthly Recurring Revenue',
            'value': f"${mrr:,.0f}",
            'subtitle': f"Growth: {growth_rate:+.1f}%",
            'color': 'green' if growth_rate > 0 else 'red',
            'icon': '💰'
        })
        
        # 2. Runway Card
        runway = metrics_data.get('runway', 0)
        runway_status = self._get_runway_status(runway)
        
        cards.append({
            'title': 'Runway',
            'value': f"{runway:.1f} months",
            'subtitle': runway_status['description'],
            'color': runway_status['color'],
            'icon': '⏱️'
        })
        
        # 3. LTV/CAC Card
        ltv_cac_ratio = metrics_data.get('ltv_cac_ratio', 0)
        ltv_cac_status = self._get_ltv_cac_status(ltv_cac_ratio)
        
        cards.append({
            'title': 'LTV/CAC Ratio',
            'value': f"{ltv_cac_ratio:.1f}x",
            'subtitle': ltv_cac_status['description'],
            'color': ltv_cac_status['color'],
            'icon': '⚖️'
        })
        
        # 4. Burn Rate Card
        burn_rate = metrics_data.get('burn_rate', 0)
        cash_balance = company_data.get('cash_balance', 0)
        
        if cash_balance > 0:
            burn_months = cash_balance / burn_rate if burn_rate > 0 else float('inf')
            burn_status = 'Good' if burn_months >= 12 else 'Warning' if burn_months >= 6 else 'Critical'
        else:
            burn_status = 'No Cash'
        
        cards.append({
            'title': 'Monthly Burn Rate',
            'value': f"${burn_rate:,.0f}",
            'subtitle': f"Status: {burn_status}",
            'color': 'green' if burn_status == 'Good' else 'orange' if burn_status == 'Warning' else 'red',
            'icon': '🔥'
        })
        
        return cards
    
    def _get_runway_status(self, runway: float) -> Dict[str, Any]:
        """Получение статуса runway"""
        
        if runway >= 18:
            return {'color': 'green', 'description': 'Excellent (>18 months)'}
        elif runway >= 12:
            return {'color': 'blue', 'description': 'Good (12-18 months)'}
        elif runway >= 9:
            return {'color': 'orange', 'description': 'Warning (9-12 months)'}
        elif runway >= 6:
            return {'color': 'red', 'description': 'Concerning (6-9 months)'}
        else:
            return {'color': 'darkred', 'description': 'Critical (<6 months)'}
    
    def _get_ltv_cac_status(self, ratio: float) -> Dict[str, Any]:
        """Получение статуса LTV/CAC ratio"""
        
        if ratio >= 8:
            return {'color': 'green', 'description': 'Excellent (>8x)'}
        elif ratio >= 5:
            return {'color': 'blue', 'description': 'Good (5-8x)'}
        elif ratio >= 3:
            return {'color': 'orange', 'description': 'Minimum (3-5x)'}
        else:
            return {'color': 'red', 'description': 'Poor (<3x)'}
    
    def _generate_financial_alerts(self, company_data: Dict[str, Any],
                                  metrics_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Генерация финансовых alerts"""
        
        alerts = []
        
        # Check runway
        runway = metrics_data.get('runway', 0)
        if runway < 6:
            alerts.append({
                'level': 'critical',
                'title': 'Critical Runway',
                'message': f'Runway is only {runway:.1f} months. Immediate action required.',
                'action': 'Reduce burn rate or start fundraising immediately.'
            })
        elif runway < 12:
            alerts.append({
                'level': 'warning',
                'title': 'Low Runway',
                'message': f'Runway is {runway:.1f} months. Plan fundraising soon.',
                'action': 'Start fundraising preparation.'
            })
        
        # Check LTV/CAC
        ltv_cac_ratio = metrics_data.get('ltv_cac_ratio', 0)
        if ltv_cac_ratio < 3:
            alerts.append({
                'level': 'warning',
                'title': 'Low LTV/CAC Ratio',
                'message': f'LTV/CAC ratio is {ltv_cac_ratio:.1f}x (below 3x benchmark).',
                'action': 'Improve retention or reduce CAC.'
            })
        
        # Check growth rate
        growth_rate = metrics_data.get('growth_rate', 0) * 100
        if growth_rate < 5:
            alerts.append({
                'level': 'warning',
                'title': 'Slow Growth',
                'message': f'Growth rate is only {growth_rate:.1f}%/month.',
                'action': 'Focus on accelerating growth initiatives.'
            })
        
        # Check churn rate
        churn_rate = metrics_data.get('churn_rate', 0) * 100
        if churn_rate > 10:
            alerts.append({
                'level': 'critical',
                'title': 'High Churn Rate',
                'message': f'Churn rate is {churn_rate:.1f}% (above 10% benchmark).',
                'action': 'Investigate churn reasons and improve retention.'
            })
        
        return alerts
    
    def create_benchmark_comparison_chart(self, comparison_data: Dict[str, Any],
                                         title: str = "Benchmark Comparison") -> go.Figure:
        """
        Создание графика сравнения с benchmarks
        
        Args:
            comparison_data: Данные сравнения
            title: Заголовок графика
        
        Returns:
            Plotly Figure
        """
        
        if not comparison_data or 'metrics_compared' not in comparison_data:
            return self._create_empty_chart("No benchmark comparison data")
        
        metrics = comparison_data['metrics_compared']
        
        if not metrics:
            return self._create_empty_chart("No metrics to compare")
        
        # Подготовка данных для radar chart
        categories = []
        company_values = []
        benchmark_good = []
        benchmark_great = []
        
        for metric in metrics:
            metric_name = metric.get('metric', '').replace('plan_', '').replace('_', ' ').title()
            categories.append(metric_name)
            
            company_value = metric.get('company_value', 0)
            benchmark_good_val = metric.get('benchmark_good', 0)
            benchmark_great_val = metric.get('benchmark_great', 0)
            
            # Нормализация значений для radar chart
            max_val = max(company_value, benchmark_good_val, benchmark_great_val)
            
            if max_val > 0:
                company_values.append(company_value / max_val * 100)
                benchmark_good.append(benchmark_good_val / max_val * 100)
                benchmark_great.append(benchmark_great_val / max_val * 100)
            else:
                company_values.append(0)
                benchmark_good.append(0)
                benchmark_great.append(0)
        
        # Закрываем круг для radar chart
        categories = categories + [categories[0]]
        company_values = company_values + [company_values[0]]
        benchmark_good = benchmark_good + [benchmark_good[0]]
        benchmark_great = benchmark_great + [benchmark_great[0]]
        
        fig = go.Figure()
        
        # Company Performance
        fig.add_trace(go.Scatterpolar(
            r=company_values,
            theta=categories,
            name='Company',
            fill='toself',
            fillcolor='rgba(46, 134, 193, 0.3)',
            line=dict(color='#2E86C1', width=3)
        ))
        
        # Benchmark Good
        fig.add_trace(go.Scatterpolar(
            r=benchmark_good,
            theta=categories,
            name='Benchmark (Good)',
            line=dict(color='#27AE60', width=2, dash='dash')
        ))
        
        # Benchmark Great
        fig.add_trace(go.Scatterpolar(
            r=benchmark_great,
            theta=categories,
            name='Benchmark (Great)',
            line=dict(color='#2ECC71', width=2, dash='dot')
        ))
        
        # Настройка layout
        fig.update_layout(
            title=dict(text=title, x=0.5, xanchor='center'),
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            showlegend=True,
            height=600
        )
        
        return fig
    
    def create_scenario_comparison_chart(self, scenarios_data: Dict[str, Any],
                                        title: str = "Scenario Comparison") -> go.Figure:
        """
        Создание графика сравнения сценариев
        
        Args:
            scenarios_data: Данные сценариев
            title: Заголовок графика
        
        Returns:
            Plotly Figure
        """
        
        if not scenarios_data or 'comparison' not in scenarios_data:
            return self._create_empty_chart("No scenario comparison data")
        
        comparison = scenarios_data['comparison']
        
        if 'metrics_comparison' not in comparison:
            return self._create_empty_chart("No metrics to compare")
        
        metrics_comparison = comparison['metrics_comparison']
        
        # Подготовка данных
        scenarios = []
        metrics_data = {}
        
        for scenario_name, scenario_data in scenarios_data.get('results', {}).items():
            if 'error' in scenario_data:
                continue
                
            scenarios.append(scenario_name)
            
            if 'scenario' in scenario_data and 'scenario_outcomes' in scenario_data['scenario']:
                outcomes = scenario_data['scenario']['scenario_outcomes']
                
                for metric, value in outcomes.items():
                    if metric not in metrics_data:
                        metrics_data[metric] = []
                    metrics_data[metric].append(value)
        
        if not scenarios or not metrics_data:
            return self._create_empty_chart("No valid scenario data")
        
        # Выбираем ключевые метрики для сравнения
        key_metrics = ['ending_mrr', 'ending_cash', 'ending_runway', 'total_profit']
        available_metrics = [m for m in key_metrics if m in metrics_data]
        
        if not available_metrics:
            return self._create_empty_chart("No key metrics available")
        
        # Создаем grouped bar chart
        fig = go.Figure()
        
        colors = ['#2E86C1', '#3498DB', '#5DADE2', '#85C1E9', '#AED6F1']
        
        for i, metric in enumerate(available_metrics):
            metric_name = metric.replace('ending_', '').replace('_', ' ').title()
            
            fig.add_trace(go.Bar(
                name=metric_name,
                x=scenarios,
                y=metrics_data[metric],
                marker_color=colors[i % len(colors)]
            ))
        
        # Настройка layout
        fig.update_layout(
            title=dict(text=title, x=0.5, xanchor='center'),
            xaxis_title="Scenario",
            yaxis_title="Value",
            barmode='group',
            hovermode='x unified',
            height=500,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
    
    def create_empty_chart(self, message: str = "No data available") -> go.Figure:
        """Создание пустого графика с сообщением"""
        return self._create_empty_chart(message)
    
    def _create_empty_chart(self, message: str) -> go.Figure:
        """Внутренний метод создания пустого графика"""
        
        fig = go.Figure()
        
        fig.add_annotation(
            x=0.5,
            y=0.5,
            text=message,
            showarrow=False,
            font=dict(size=16, color="gray"),
            xref="paper",
            yref="paper"
        )
        
        fig.update_layout(
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='white',
            height=400
        )
        
        return fig
    
    def fig_to_html(self, fig: go.Figure) -> str:
        """
        Конвертация Plotly Figure в HTML
        
        Args:
            fig: Plotly Figure
        
        Returns:
            HTML строка
        """
        
        return pio.to_html(fig, full_html=False, include_plotlyjs='cdn')
    
    def fig_to_image(self, fig: go.Figure, format: str = 'png', 
                    width: int = 800, height: int = 600) -> bytes:
        """
        Конвертация Plotly Figure в image
        
        Args:
            fig: Plotly Figure
            format: Формат изображения (png, jpeg, svg, pdf)
            width: Ширина изображения
            height: Высота изображения
        
        Returns:
            Байты изображения
        """
        
        return pio.to_image(fig, format=format, width=width, height=height)
    
    def create_matplotlib_chart(self, data: pd.DataFrame, 
                               chart_type: str = 'line',
                               **kwargs) -> plt.Figure:
        """
        Создание графика с использованием Matplotlib
        
        Args:
            data: DataFrame с данными
            chart_type: Тип графика (line, bar, scatter, histogram)
            **kwargs: Дополнительные параметры
        
        Returns:
            Matplotlib Figure
        """
        
        fig, ax = plt.subplots(figsize=kwargs.get('figsize', (10, 6)))
        
        if chart_type == 'line':
            if 'x' in kwargs and 'y' in kwargs:
                ax.plot(data[kwargs['x']], data[kwargs['y']], 
                       marker='o', linewidth=2, markersize=6)
            else:
                # Plot всех числовых колонок
                numeric_cols = data.select_dtypes(include=[np.number]).columns
                for col in numeric_cols[:5]:  # Ограничиваем 5 колонками
                    ax.plot(data.index, data[col], label=col)
                
                if len(numeric_cols) > 0:
                    ax.legend()
        
        elif chart_type == 'bar':
            if 'x' in kwargs and 'y' in kwargs:
                ax.bar(data[kwargs['x']], data[kwargs['y']])
            else:
                # Bar chart для первой числовой колонки
                numeric_cols = data.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) > 0:
                    ax.bar(data.index, data[numeric_cols[0]])
        
        elif chart_type == 'scatter':
            if 'x' in kwargs and 'y' in kwargs:
                ax.scatter(data[kwargs['x']], data[kwargs['y']])
        
        elif chart_type == 'histogram':
            if 'column' in kwargs:
                ax.hist(data[kwargs['column']].dropna(), bins=20)
        
        # Настройки графика
        if 'title' in kwargs:
            ax.set_title(kwargs['title'], fontsize=14, pad=20)
        
        if 'xlabel' in kwargs:
            ax.set_xlabel(kwargs['xlabel'], fontsize=12)
        
        if 'ylabel' in kwargs:
            ax.set_ylabel(kwargs['ylabel'], fontsize=12)
        
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        
        return fig
    
    def matplotlib_fig_to_base64(self, fig: plt.Figure, format: str = 'png') -> str:
        """
        Конвертация Matplotlib Figure в base64 строку
        
        Args:
            fig: Matplotlib Figure
            format: Формат изображения
        
        Returns:
            Base64 строка
        """
        
        buf = io.BytesIO()
        fig.savefig(buf, format=format, dpi=100, bbox_inches='tight')
        buf.seek(0)
        
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()
        
        return f"data:image/{format};base64,{img_str}"
    
    def create_metrics_table(self, metrics_data: Dict[str, Any],
                            title: str = "Financial Metrics") -> go.Figure:
        """
        Создание таблицы с метриками
        
        Args:
            metrics_data: Данные метрик
            title: Заголовок таблицы
        
        Returns:
            Plotly Figure с таблицей
        """
        
        if not metrics_data:
            return self._create_empty_chart("No metrics data")
        
        # Подготовка данных для таблицы
        headers = ['Metric', 'Value', 'Status']
        rows = []
        
        # Key metrics
        key_metrics = [
            ('MRR', metrics_data.get('mrr', 0), f"${metrics_data.get('mrr', 0):,.0f}", ''),
            ('Monthly Growth', metrics_data.get('growth_rate', 0), f"{metrics_data.get('growth_rate', 0)*100:.1f}%", 
             self._get_growth_status(metrics_data.get('growth_rate', 0))),
            ('Churn Rate', metrics_data.get('churn_rate', 0), f"{metrics_data.get('churn_rate', 0)*100:.1f}%",
             self._get_churn_status(metrics_data.get('churn_rate', 0))),
            ('CAC', metrics_data.get('cac', 0), f"${metrics_data.get('cac', 0):,.0f}", ''),
            ('LTV', metrics_data.get('ltv', 0), f"${metrics_data.get('ltv', 0):,.0f}", ''),
            ('LTV/CAC Ratio', metrics_data.get('ltv_cac_ratio', 0), f"{metrics_data.get('ltv_cac_ratio', 0):.1f}x",
             self._get_ltv_cac_status_text(metrics_data.get('ltv_cac_ratio', 0))),
            ('Burn Rate', metrics_data.get('burn_rate', 0), f"${metrics_data.get('burn_rate', 0):,.0f}/month", ''),
            ('Runway', metrics_data.get('runway', 0), f"{metrics_data.get('runway', 0):.1f} months",
             self._get_runway_status_text(metrics_data.get('runway', 0))),
            ('Gross Margin', metrics_data.get('gross_margin', 0), f"{metrics_data.get('gross_margin', 0)*100:.1f}%",
             self._get_margin_status(metrics_data.get('gross_margin', 0)))
        ]
        
        for metric_name, value, formatted_value, status in key_metrics:
            rows.append([metric_name, formatted_value, status])
        
        # Создание таблицы
        fig = go.Figure(data=[go.Table(
            header=dict(
                values=headers,
                fill_color='#2E86C1',
                align='left',
                font=dict(color='white', size=12)
            ),
            cells=dict(
                values=list(zip(*rows)),
                fill_color=['white', 'white', 
                           [self._get_status_color(status) for status in rows[-1]]],
                align='left',
                font=dict(color='black', size=11)
            )
        )])
        
        fig.update_layout(
            title=dict(text=title, x=0.5, xanchor='center'),
            height=400
        )
        
        return fig
    
    def _get_growth_status(self, growth_rate: float) -> str:
        """Получение статуса growth rate"""
        
        if growth_rate >= 0.15:
            return 'Excellent'
        elif growth_rate >= 0.10:
            return 'Good'
        elif growth_rate >= 0.05:
            return 'Fair'
        else:
            return 'Needs Improvement'
    
    def _get_churn_status(self, churn_rate: float) -> str:
        """Получение статуса churn rate"""
        
        if churn_rate <= 0.02:
            return 'Excellent'
        elif churn_rate <= 0.05:
            return 'Good'
        elif churn_rate <= 0.08:
            return 'Fair'
        else:
            return 'Needs Improvement'
    
    def _get_ltv_cac_status_text(self, ratio: float) -> str:
        """Получение текста статуса LTV/CAC"""
        
        if ratio >= 8:
            return 'Excellent'
        elif ratio >= 5:
            return 'Good'
        elif ratio >= 3:
            return 'Minimum'
        else:
            return 'Poor'
    
    def _get_runway_status_text(self, runway: float) -> str:
        """Получение текста статуса runway"""
        
        if runway >= 18:
            return 'Excellent'
        elif runway >= 12:
            return 'Good'
        elif runway >= 9:
            return 'Warning'
        elif runway >= 6:
            return 'Concerning'
        else:
            return 'Critical'
    
    def _get_margin_status(self, margin: float) -> str:
        """Получение статуса gross margin"""
        
        if margin >= 0.8:
            return 'Excellent'
        elif margin >= 0.7:
            return 'Good'
        elif margin >= 0.6:
            return 'Fair'
        else:
            return 'Needs Improvement'
    
    def _get_status_color(self, status: str) -> str:
        """Получение цвета для статуса"""
        
        color_map = {
            'Excellent': '#27AE60',
            'Good': '#2ECC71',
            'Fair': '#F39C12',
            'Minimum': '#F39C12',
            'Warning': '#F39C12',
            'Needs Improvement': '#E74C3C',
            'Poor': '#E74C3C',
            'Concerning': '#E74C3C',
            'Critical': '#C0392B'
        }
        
        return color_map.get(status, '#ECF0F1')

# Создаем глобальный экземпляр движка визуализации
visualization_engine = VisualizationEngine()

# Экспортируем полезные функции
def create_financial_dashboard(company_data: Dict[str, Any],
                              metrics_data: Dict[str, Any],
                              monthly_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Публичная функция для создания финансового dashboard"""
    return visualization_engine.create_financial_health_dashboard(
        company_data, metrics_data, monthly_data
    )

def create_mrr_growth_visualization(monthly_data: List[Dict[str, Any]]) -> str:
    """Публичная функция для создания визуализации роста MRR"""
    fig = visualization_engine.create_mrr_growth_chart(monthly_data)
    return visualization_engine.fig_to_html(fig)

def export_chart_as_image(fig: go.Figure, format: str = 'png') -> bytes:
    """Публичная функция для экспорта графика как изображения"""
    return visualization_engine.fig_to_image(fig, format)
