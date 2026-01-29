"""
Генератор экспортов для SaaS метрик и отчетов
Экспорт в Excel, PDF, CSV и другие форматы
"""

from enum import Enum
import pandas as pd
import numpy as np
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Tuple, Union
import json
import csv
import io
from pathlib import Path
import plotly.graph_objects as go
import plotly.io as pio
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Для работы без GUI

class ExportFormat(Enum):
    """Форматы экспорта"""
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"
    PDF = "pdf"
    HTML = "html"
    MARKDOWN = "markdown"

class ExportGenerator:
    """
    Генератор экспортов для SaaS метрик и отчетов
    """
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Настройка кастомных стилей для PDF"""
        
        # Заголовки
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#2E86C1')
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomHeading1',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=12,
            textColor=colors.HexColor('#3498DB')
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomHeading2',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=8,
            textColor=colors.HexColor('#5DADE2')
        ))
        
        # Текст
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomSmall',
            parent=self.styles['Normal'],
            fontSize=8,
            spaceAfter=4,
            textColor=colors.grey
        ))
    
    def export_company_report(self, company_data: Dict[str, Any], 
                             report_data: Dict[str, Any],
                             export_format: ExportFormat,
                             filename: Optional[str] = None) -> Union[bytes, str, None]:
        """
        Экспорт отчета компании
        
        Args:
            company_data: Данные компании
            report_data: Данные отчета
            export_format: Формат экспорта
            filename: Имя файла (опционально)
        
        Returns:
            Данные экспорта или путь к файлу
        """
        
        if export_format == ExportFormat.EXCEL:
            return self._export_to_excel(company_data, report_data, filename)
        elif export_format == ExportFormat.CSV:
            return self._export_to_csv(company_data, report_data, filename)
        elif export_format == ExportFormat.JSON:
            return self._export_to_json(company_data, report_data, filename)
        elif export_format == ExportFormat.PDF:
            return self._export_to_pdf(company_data, report_data, filename)
        elif export_format == ExportFormat.HTML:
            return self._export_to_html(company_data, report_data, filename)
        elif export_format == ExportFormat.MARKDOWN:
            return self._export_to_markdown(company_data, report_data, filename)
        else:
            raise ValueError(f"Unsupported export format: {export_format}")
    
    def _export_to_excel(self, company_data: Dict[str, Any],
                        report_data: Dict[str, Any],
                        filename: Optional[str] = None) -> bytes:
        """Экспорт в Excel"""
        
        # Создаем Excel writer
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # 1. Company Summary Sheet
            summary_data = self._prepare_company_summary(company_data, report_data)
            summary_df = pd.DataFrame([summary_data])
            summary_df.to_excel(writer, sheet_name='Company Summary', index=False)
            
            # 2. Financial Metrics Sheet
            metrics_data = self._prepare_financial_metrics(report_data)
            metrics_df = pd.DataFrame([metrics_data])
            metrics_df.to_excel(writer, sheet_name='Financial Metrics', index=False)
            
            # 3. Monthly Data Sheet
            if 'monthly_data' in report_data:
                monthly_df = pd.DataFrame(report_data['monthly_data'])
                monthly_df.to_excel(writer, sheet_name='Monthly Data', index=False)
            
            # 4. Recommendations Sheet
            if 'recommendations' in report_data:
                recs_df = pd.DataFrame(report_data['recommendations'])
                recs_df.to_excel(writer, sheet_name='Recommendations', index=False)
            
            # 5. Benchmark Comparison Sheet
            if 'benchmark_comparison' in report_data:
                bench_df = self._prepare_benchmark_data(report_data['benchmark_comparison'])
                bench_df.to_excel(writer, sheet_name='Benchmark Comparison', index=False)
        
        # Получаем байты
        excel_data = output.getvalue()
        
        # Сохраняем в файл если указано имя
        if filename:
            with open(filename, 'wb') as f:
                f.write(excel_data)
        
        return excel_data
    
    def _prepare_company_summary(self, company_data: Dict[str, Any],
                                report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Подготовка summary компании"""
        
        summary = {
            'Company Name': company_data.get('company_name', 'N/A'),
            'Stage': company_data.get('stage', 'N/A'),
            'Current MRR': f"${company_data.get('current_mrr', 0):,.0f}",
            'Current Customers': f"{company_data.get('current_customers', 0):,.0f}",
            'Monthly Price': f"${company_data.get('monthly_price', 0):,.2f}",
            'Team Size': company_data.get('team_size', 0),
            'Cash Balance': f"${company_data.get('cash_balance', 0):,.0f}",
            'Analysis Date': report_data.get('analysis_date', datetime.now().isoformat()),
            'Report Type': report_data.get('report_type', 'Financial Analysis'),
            'Overall Status': report_data.get('overall_status', 'N/A')
        }
        
        # Добавляем key insights если есть
        if 'key_insights' in report_data and report_data['key_insights']:
            insights = report_data['key_insights']
            for i, insight in enumerate(insights[:3]):  # Первые 3 insights
                summary[f'Key Insight {i+1}'] = insight.get('title', '')
        
        return summary
    
    def _prepare_financial_metrics(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Подготовка финансовых метрик"""
        
        metrics = {}
        
        # Базовые метрики
        if 'current_metrics' in report_data:
            current = report_data['current_metrics']
            
            metrics['Current MRR'] = f"${current.get('mrr', 0):,.0f}"
            metrics['Monthly Growth Rate'] = f"{current.get('growth_rate', 0)*100:.1f}%"
            metrics['Churn Rate'] = f"{current.get('churn_rate', 0)*100:.1f}%"
            metrics['CAC'] = f"${current.get('cac', 0):,.0f}"
            metrics['LTV'] = f"${current.get('ltv', 0):,.0f}"
            metrics['LTV/CAC Ratio'] = f"{current.get('ltv_cac_ratio', 0):.1f}x"
            metrics['Burn Rate'] = f"${current.get('burn_rate', 0):,.0f}/month"
            metrics['Runway'] = f"{current.get('runway', 0):.1f} months"
            metrics['Gross Margin'] = f"{current.get('gross_margin', 0)*100:.1f}%"
        
        # Добавляем benchmark comparison если есть
        if 'benchmark_comparison' in report_data:
            bench = report_data['benchmark_comparison']
            metrics['Benchmark Score'] = f"{bench.get('overall_score', 0):.0f}/100"
            metrics['Performance Level'] = bench.get('overall_performance', 'N/A')
        
        return metrics
    
    def _prepare_benchmark_data(self, benchmark_data: Dict[str, Any]) -> pd.DataFrame:
        """Подготовка данных benchmark comparison"""
        
        rows = []
        
        if 'metrics_compared' in benchmark_data:
            for metric_data in benchmark_data['metrics_compared']:
                rows.append({
                    'Metric': metric_data.get('metric', ''),
                    'Company Value': metric_data.get('company_value', 0),
                    'Benchmark Good': metric_data.get('benchmark_good', 0),
                    'Benchmark Great': metric_data.get('benchmark_great', 0),
                    'Benchmark Excellent': metric_data.get('benchmark_excellent', 0),
                    'Performance Level': metric_data.get('performance_level', ''),
                    'Score': metric_data.get('score', 0),
                    'Gap %': f"{metric_data.get('gap_percent', 0):.1f}%"
                })
        
        return pd.DataFrame(rows)
    
    def _export_to_csv(self, company_data: Dict[str, Any],
                      report_data: Dict[str, Any],
                      filename: Optional[str] = None) -> str:
        """Экспорт в CSV"""
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 1. Company Summary
        writer.writerow(['COMPANY SUMMARY'])
        writer.writerow([])
        
        summary = self._prepare_company_summary(company_data, report_data)
        for key, value in summary.items():
            writer.writerow([key, value])
        
        writer.writerow([])
        
        # 2. Financial Metrics
        writer.writerow(['FINANCIAL METRICS'])
        writer.writerow([])
        
        metrics = self._prepare_financial_metrics(report_data)
        for key, value in metrics.items():
            writer.writerow([key, value])
        
        writer.writerow([])
        
        # 3. Monthly Data (если есть)
        if 'monthly_data' in report_data and report_data['monthly_data']:
            writer.writerow(['MONTHLY DATA'])
            writer.writerow([])
            
            monthly_data = report_data['monthly_data']
            if isinstance(monthly_data, list) and len(monthly_data) > 0:
                # Headers
                headers = list(monthly_data[0].keys())
                writer.writerow(headers)
                
                # Data
                for row in monthly_data:
                    writer.writerow([row.get(h, '') for h in headers])
                
                writer.writerow([])
        
        csv_data = output.getvalue()
        
        # Сохраняем в файл если указано имя
        if filename:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                f.write(csv_data)
        
        return csv_data
    
    def _export_to_json(self, company_data: Dict[str, Any],
                       report_data: Dict[str, Any],
                       filename: Optional[str] = None) -> str:
        """Экспорт в JSON"""
        
        export_data = {
            'export_date': datetime.now().isoformat(),
            'company': company_data,
            'report': report_data,
            'metadata': {
                'export_format': 'json',
                'version': '1.0',
                'generated_by': 'SaaS Unit Economics Tool'
            }
        }
        
        json_data = json.dumps(export_data, indent=2, default=str)
        
        # Сохраняем в файл если указано имя
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(json_data)
        
        return json_data
    
    def _export_to_pdf(self, company_data: Dict[str, Any],
                      report_data: Dict[str, Any],
                      filename: Optional[str] = None) -> bytes:
        """Экспорт в PDF"""
        
        # Создаем PDF документ
        buffer = io.BytesIO()
        
        if filename:
            doc = SimpleDocTemplate(filename, pagesize=A4)
        else:
            doc = SimpleDocTemplate(buffer, pagesize=A4)
        
        # Собираем элементы документа
        elements = []
        
        # 1. Заголовок
        elements.append(Paragraph("SaaS Financial Analysis Report", self.styles['CustomTitle']))
        elements.append(Spacer(1, 0.25*inch))
        
        # 2. Company Information
        elements.append(Paragraph("Company Information", self.styles['CustomHeading1']))
        elements.append(Spacer(1, 0.1*inch))
        
        company_info = [
            ['Company Name:', company_data.get('company_name', 'N/A')],
            ['Stage:', company_data.get('stage', 'N/A')],
            ['Current MRR:', f"${company_data.get('current_mrr', 0):,.0f}"],
            ['Current Customers:', f"{company_data.get('current_customers', 0):,.0f}"],
            ['Monthly Price:', f"${company_data.get('monthly_price', 0):,.2f}"],
            ['Team Size:', str(company_data.get('team_size', 0))],
            ['Cash Balance:', f"${company_data.get('cash_balance', 0):,.0f}"]
        ]
        
        company_table = Table(company_info, colWidths=[2*inch, 3*inch])
        company_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('FONTSIZE', (0, 0), (-1, -1), 9)
        ]))
        
        elements.append(company_table)
        elements.append(Spacer(1, 0.25*inch))
        
        # 3. Financial Metrics
        elements.append(Paragraph("Key Financial Metrics", self.styles['CustomHeading1']))
        elements.append(Spacer(1, 0.1*inch))
        
        if 'current_metrics' in report_data:
            current = report_data['current_metrics']
            
            metrics_data = [
                ['Metric', 'Value', 'Status'],
                ['Monthly Growth Rate', f"{current.get('growth_rate', 0)*100:.1f}%", self._get_metric_status(current.get('growth_rate', 0), 0.1)],
                ['Churn Rate', f"{current.get('churn_rate', 0)*100:.1f}%", self._get_metric_status(current.get('churn_rate', 0), 0.05, reverse=True)],
                ['CAC', f"${current.get('cac', 0):,.0f}", 'N/A'],
                ['LTV', f"${current.get('ltv', 0):,.0f}", 'N/A'],
                ['LTV/CAC Ratio', f"{current.get('ltv_cac_ratio', 0):.1f}x", self._get_metric_status(current.get('ltv_cac_ratio', 0), 3.0)],
                ['Burn Rate', f"${current.get('burn_rate', 0):,.0f}/month", 'N/A'],
                ['Runway', f"{current.get('runway', 0):.1f} months", self._get_runway_status(current.get('runway', 0))],
                ['Gross Margin', f"{current.get('gross_margin', 0)*100:.1f}%", self._get_metric_status(current.get('gross_margin', 0), 0.7)]
            ]
            
            metrics_table = Table(metrics_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
            metrics_table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E86C1')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('FONTSIZE', (0, 0), (-1, -1), 9)
            ]))
            
            elements.append(metrics_table)
        
        elements.append(Spacer(1, 0.25*inch))
        
        # 4. Key Insights
        if 'key_insights' in report_data and report_data['key_insights']:
            elements.append(Paragraph("Key Insights", self.styles['CustomHeading1']))
            elements.append(Spacer(1, 0.1*inch))
            
            for i, insight in enumerate(report_data['key_insights'][:5]):  # Первые 5 insights
                elements.append(Paragraph(f"{i+1}. {insight.get('title', '')}", self.styles['CustomHeading2']))
                elements.append(Paragraph(insight.get('description', ''), self.styles['CustomBody']))
                elements.append(Paragraph(f"Recommendation: {insight.get('recommendation', '')}", self.styles['CustomSmall']))
                elements.append(Spacer(1, 0.05*inch))
        
        # 5. Recommendations
        if 'recommendations' in report_data and report_data['recommendations']:
            elements.append(Paragraph("Recommendations", self.styles['CustomHeading1']))
            elements.append(Spacer(1, 0.1*inch))
            
            recs = report_data['recommendations']
            if isinstance(recs, dict):
                for category, items in recs.items():
                    if isinstance(items, list):
                        elements.append(Paragraph(category.replace('_', ' ').title(), self.styles['CustomHeading2']))
                        for item in items[:3]:  # Первые 3 рекомендации в каждой категории
                            elements.append(Paragraph(f"• {item}", self.styles['CustomBody']))
                        elements.append(Spacer(1, 0.05*inch))
        
        # 6. Footer
        elements.append(Spacer(1, 0.5*inch))
        elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", self.styles['CustomSmall']))
        elements.append(Paragraph("SaaS Unit Economics Tool - Financial Analysis Report", self.styles['CustomSmall']))
        
        # Собираем документ
        doc.build(elements)
        
        # Получаем байты если сохраняли в buffer
        if not filename:
            pdf_data = buffer.getvalue()
            buffer.close()
            return pdf_data
        
        return None
    
    def _get_metric_status(self, value: float, target: float, reverse: bool = False) -> str:
        """Получение статуса метрики"""
        
        if reverse:
            # Для метрик где меньше лучше (например churn)
            if value <= target * 0.7:
                return "Excellent"
            elif value <= target:
                return "Good"
            elif value <= target * 1.3:
                return "Fair"
            else:
                return "Needs Improvement"
        else:
            # Для метрик где больше лучше
            if value >= target * 1.3:
                return "Excellent"
            elif value >= target:
                return "Good"
            elif value >= target * 0.7:
                return "Fair"
            else:
                return "Needs Improvement"
    
    def _get_runway_status(self, runway: float) -> str:
        """Получение статуса runway"""
        
        if runway >= 18:
            return "Excellent"
        elif runway >= 12:
            return "Good"
        elif runway >= 9:
            return "Fair"
        elif runway >= 6:
            return "Concerning"
        elif runway >= 3:
            return "Critical"
        else:
            return "Emergency"
    
    def _export_to_html(self, company_data: Dict[str, Any],
                       report_data: Dict[str, Any],
                       filename: Optional[str] = None) -> str:
        """Экспорт в HTML"""
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>SaaS Financial Analysis Report</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    text-align: center;
                    padding-bottom: 30px;
                    border-bottom: 2px solid #2E86C1;
                    margin-bottom: 30px;
                }}
                .company-info, .metrics-table {{
                    margin-bottom: 30px;
                }}
                .section-title {{
                    color: #2E86C1;
                    border-bottom: 1px solid #ddd;
                    padding-bottom: 10px;
                    margin-top: 40px;
                }}
                .metric-card {{
                    background: #f8f9fa;
                    border-left: 4px solid #3498DB;
                    padding: 15px;
                    margin-bottom: 15px;
                    border-radius: 4px;
                }}
                .metric-value {{
                    font-size: 1.5em;
                    font-weight: bold;
                    color: #2C3E50;
                }}
                .metric-label {{
                    color: #7F8C8D;
                    font-size: 0.9em;
                }}
                .insight-card {{
                    background: #fff;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    padding: 15px;
                    margin-bottom: 15px;
                }}
                .insight-title {{
                    color: #E74C3C;
                    font-weight: bold;
                    margin-bottom: 5px;
                }}
                .recommendation {{
                    background: #E8F8F5;
                    border-left: 4px solid #1ABC9C;
                    padding: 10px;
                    margin-bottom: 10px;
                    border-radius: 3px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 20px;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 12px;
                    text-align: left;
                }}
                th {{
                    background-color: #2E86C1;
                    color: white;
                }}
                tr:nth-child(even) {{
                    background-color: #f2f2f2;
                }}
                .status-excellent {{ color: #27AE60; font-weight: bold; }}
                .status-good {{ color: #3498DB; font-weight: bold; }}
                .status-fair {{ color: #F39C12; font-weight: bold; }}
                .status-poor {{ color: #E74C3C; font-weight: bold; }}
                .footer {{
                    margin-top: 50px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    text-align: center;
                    color: #7F8C8D;
                    font-size: 0.9em;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>SaaS Financial Analysis Report</h1>
                <p>Generated on {generated_date}</p>
            </div>
            
            <div class="company-info">
                <h2 class="section-title">Company Information</h2>
                <table>
                    {company_info_rows}
                </table>
            </div>
            
            <div class="metrics-table">
                <h2 class="section-title">Key Financial Metrics</h2>
                <table>
                    {metrics_rows}
                </table>
            </div>
            
            {insights_section}
            
            {recommendations_section}
            
            {benchmark_section}
            
            <div class="footer">
                <p>Generated by SaaS Unit Economics Tool</p>
                <p>Report ID: {report_id}</p>
            </div>
        </body>
        </html>
        """
        
        # Подготавливаем данные для шаблона
        company_info_rows = ""
        if company_data:
            company_info = [
                ('Company Name', company_data.get('company_name', 'N/A')),
                ('Stage', company_data.get('stage', 'N/A')),
                ('Current MRR', f"${company_data.get('current_mrr', 0):,.0f}"),
                ('Current Customers', f"{company_data.get('current_customers', 0):,.0f}"),
                ('Monthly Price', f"${company_data.get('monthly_price', 0):,.2f}"),
                ('Team Size', company_data.get('team_size', 0)),
                ('Cash Balance', f"${company_data.get('cash_balance', 0):,.0f}")
            ]
            
            for label, value in company_info:
                company_info_rows += f"<tr><td><strong>{label}</strong></td><td>{value}</td></tr>"
        
        # Financial Metrics
        metrics_rows = ""
        if 'current_metrics' in report_data:
            current = report_data['current_metrics']
            
            metrics = [
                ('Monthly Growth Rate', f"{current.get('growth_rate', 0)*100:.1f}%", self._get_metric_status(current.get('growth_rate', 0), 0.1)),
                ('Churn Rate', f"{current.get('churn_rate', 0)*100:.1f}%", self._get_metric_status(current.get('churn_rate', 0), 0.05, reverse=True)),
                ('CAC', f"${current.get('cac', 0):,.0f}", 'N/A'),
                ('LTV', f"${current.get('ltv', 0):,.0f}", 'N/A'),
                ('LTV/CAC Ratio', f"{current.get('ltv_cac_ratio', 0):.1f}x", self._get_metric_status(current.get('ltv_cac_ratio', 0), 3.0)),
                ('Burn Rate', f"${current.get('burn_rate', 0):,.0f}/month", 'N/A'),
                ('Runway', f"{current.get('runway', 0):.1f} months", self._get_runway_status(current.get('runway', 0))),
                ('Gross Margin', f"{current.get('gross_margin', 0)*100:.1f}%", self._get_metric_status(current.get('gross_margin', 0), 0.7))
            ]
            
            metrics_rows = "<tr><th>Metric</th><th>Value</th><th>Status</th></tr>"
            for label, value, status in metrics:
                status_class = ""
                if "Excellent" in status:
                    status_class = "status-excellent"
                elif "Good" in status:
                    status_class = "status-good"
                elif "Fair" in status:
                    status_class = "status-fair"
                elif "Needs Improvement" in status or "Concerning" in status or "Critical" in status or "Emergency" in status:
                    status_class = "status-poor"
                
                metrics_rows += f'<tr><td>{label}</td><td>{value}</td><td class="{status_class}">{status}</td></tr>'
        
        # Insights Section
        insights_section = ""
        if 'key_insights' in report_data and report_data['key_insights']:
            insights_html = ""
            for i, insight in enumerate(report_data['key_insights'][:5]):
                insights_html += f"""
                <div class="insight-card">
                    <div class="insight-title">{i+1}. {insight.get('title', '')}</div>
                    <p>{insight.get('description', '')}</p>
                    <p><strong>Recommendation:</strong> {insight.get('recommendation', '')}</p>
                </div>
                """
            
            insights_section = f"""
            <div class="insights-section">
                <h2 class="section-title">Key Insights</h2>
                {insights_html}
            </div>
            """
        
        # Recommendations Section
        recommendations_section = ""
        if 'recommendations' in report_data and report_data['recommendations']:
            recs_html = ""
            recs = report_data['recommendations']
            
            if isinstance(recs, dict):
                for category, items in recs.items():
                    if isinstance(items, list):
                        category_html = ""
                        for item in items[:3]:
                            category_html += f'<div class="recommendation">{item}</div>'
                        
                        recs_html += f"""
                        <h3>{category.replace('_', ' ').title()}</h3>
                        {category_html}
                        """
            
            recommendations_section = f"""
            <div class="recommendations-section">
                <h2 class="section-title">Recommendations</h2>
                {recs_html}
            </div>
            """
        
        # Benchmark Section
        benchmark_section = ""
        if 'benchmark_comparison' in report_data:
            bench = report_data['benchmark_comparison']
            
            if 'overall_score' in bench:
                score = bench['overall_score']
                performance = bench.get('overall_performance', 'N/A')
                
                benchmark_section = f"""
                <div class="benchmark-section">
                    <h2 class="section-title">Benchmark Comparison</h2>
                    <div class="metric-card">
                        <div class="metric-label">Overall Benchmark Score</div>
                        <div class="metric-value">{score}/100</div>
                        <div>Performance: {performance}</div>
                    </div>
                </div>
                """
        
        # Заполняем шаблон
        html_content = html_template.format(
            generated_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            company_info_rows=company_info_rows,
            metrics_rows=metrics_rows,
            insights_section=insights_section,
            recommendations_section=recommendations_section,
            benchmark_section=benchmark_section,
            report_id=report_data.get('report_id', 'N/A')
        )
        
        # Сохраняем в файл если указано имя
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
        
        return html_content
    
    def _export_to_markdown(self, company_data: Dict[str, Any],
                           report_data: Dict[str, Any],
                           filename: Optional[str] = None) -> str:
        """Экспорт в Markdown"""
        
        md_content = f"""
# SaaS Financial Analysis Report

**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Company Information

"""
        
        # Company Information
        if company_data:
            md_content += f"""
| Field | Value |
|-------|-------|
| Company Name | {company_data.get('company_name', 'N/A')} |
| Stage | {company_data.get('stage', 'N/A')} |
| Current MRR | ${company_data.get('current_mrr', 0):,.0f} |
| Current Customers | {company_data.get('current_customers', 0):,.0f} |
| Monthly Price | ${company_data.get('monthly_price', 0):,.2f} |
| Team Size | {company_data.get('team_size', 0)} |
| Cash Balance | ${company_data.get('cash_balance', 0):,.0f} |

"""
        
        # Financial Metrics
        if 'current_metrics' in report_data:
            current = report_data['current_metrics']
            
            md_content += """
## Key Financial Metrics

| Metric | Value | Status |
|--------|-------|--------|
"""
            
            metrics = [
                ('Monthly Growth Rate', f"{current.get('growth_rate', 0)*100:.1f}%", self._get_metric_status(current.get('growth_rate', 0), 0.1)),
                ('Churn Rate', f"{current.get('churn_rate', 0)*100:.1f}%", self._get_metric_status(current.get('churn_rate', 0), 0.05, reverse=True)),
                ('CAC', f"${current.get('cac', 0):,.0f}", 'N/A'),
                ('LTV', f"${current.get('ltv', 0):,.0f}", 'N/A'),
                ('LTV/CAC Ratio', f"{current.get('ltv_cac_ratio', 0):.1f}x", self._get_metric_status(current.get('ltv_cac_ratio', 0), 3.0)),
                ('Burn Rate', f"${current.get('burn_rate', 0):,.0f}/month", 'N/A'),
                ('Runway', f"{current.get('runway', 0):.1f} months", self._get_runway_status(current.get('runway', 0))),
                ('Gross Margin', f"{current.get('gross_margin', 0)*100:.1f}%", self._get_metric_status(current.get('gross_margin', 0), 0.7))
            ]
            
            for label, value, status in metrics:
                md_content += f"| {label} | {value} | {status} |\n"
            
            md_content += "\n"
        
        # Key Insights
        if 'key_insights' in report_data and report_data['key_insights']:
            md_content += "## Key Insights\n\n"
            
            for i, insight in enumerate(report_data['key_insights'][:5]):
                md_content += f"""
### {i+1}. {insight.get('title', '')}

{insight.get('description', '')}

**Recommendation:** {insight.get('recommendation', '')}

"""
        
        # Recommendations
        if 'recommendations' in report_data and report_data['recommendations']:
            md_content += "## Recommendations\n\n"
            
            recs = report_data['recommendations']
            if isinstance(recs, dict):
                for category, items in recs.items():
                    if isinstance(items, list):
                        md_content += f"### {category.replace('_', ' ').title()}\n\n"
                        for item in items[:3]:
                            md_content += f"- {item}\n"
                        md_content += "\n"
        
        # Benchmark Comparison
        if 'benchmark_comparison' in report_data:
            bench = report_data['benchmark_comparison']
            
            if 'overall_score' in bench:
                md_content += f"""
## Benchmark Comparison

**Overall Score:** {bench['overall_score']}/100

**Performance Level:** {bench.get('overall_performance', 'N/A')}

"""
        
        # Footer
        md_content += f"""
---

*Generated by SaaS Unit Economics Tool*  
*Report ID: {report_data.get('report_id', 'N/A')}*
"""
        
        # Сохраняем в файл если указано имя
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(md_content)
        
        return md_content
    
    def export_financial_plan(self, plan_data: Dict[str, Any],
                             export_format: ExportFormat,
                             filename: Optional[str] = None) -> Union[bytes, str, None]:
        """
        Экспорт финансового плана
        
        Args:
            plan_data: Данные финансового плана
            export_format: Формат экспорта
            filename: Имя файла (опционально)
        
        Returns:
            Данные экспорта или путь к файлу
        """
        
        if export_format == ExportFormat.EXCEL:
            return self._export_plan_to_excel(plan_data, filename)
        elif export_format == ExportFormat.PDF:
            return self._export_plan_to_pdf(plan_data, filename)
        else:
            # Для других форматов используем общий метод
            return self.export_company_report(
                {'company_name': plan_data.get('plan_name', 'Financial Plan')},
                plan_data,
                export_format,
                filename
            )
    
    def _export_plan_to_excel(self, plan_data: Dict[str, Any],
                             filename: Optional[str] = None) -> bytes:
        """Экспорт плана в Excel"""
        
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # 1. Plan Summary
            summary_data = {
                'Plan Name': plan_data.get('plan_name', 'N/A'),
                'Plan Year': plan_data.get('plan_year', 'N/A'),
                'Company ID': plan_data.get('company_id', 'N/A'),
                'Created Date': plan_data.get('created_at', datetime.now().isoformat()),
                'Description': plan_data.get('description', '')
            }
            
            summary_df = pd.DataFrame([summary_data])
            summary_df.to_excel(writer, sheet_name='Plan Summary', index=False)
            
            # 2. Monthly Plans
            if 'monthly_plans' in plan_data and plan_data['monthly_plans']:
                monthly_data = []
                
                for plan in plan_data['monthly_plans']:
                    if isinstance(plan, dict):
                        monthly_data.append({
                            'Month': plan.get('month_name', plan.get('month_number', '')),
                            'MRR': plan.get('plan_mrr', 0),
                            'New Customers': plan.get('plan_new_customers', 0),
                            'Total Revenue': plan.get('plan_total_revenue', 0),
                            'Total Costs': plan.get('plan_total_costs', 0),
                            'Burn Rate': plan.get('plan_burn_rate', 0),
                            'Runway': plan.get('plan_runway', 0),
                            'LTV/CAC Ratio': plan.get('plan_ltv_cac_ratio', 0)
                        })
                
                if monthly_data:
                    monthly_df = pd.DataFrame(monthly_data)
                    monthly_df.to_excel(writer, sheet_name='Monthly Plans', index=False)
            
            # 3. Assumptions
            if 'assumptions' in plan_data and plan_data['assumptions']:
                assumptions = plan_data['assumptions']
                
                if isinstance(assumptions, dict):
                    assumptions_list = []
                    
                    for category, values in assumptions.items():
                        if isinstance(values, dict):
                            for key, value in values.items():
                                assumptions_list.append({
                                    'Category': category,
                                    'Parameter': key,
                                    'Value': value
                                })
                        else:
                            assumptions_list.append({
                                'Category': 'General',
                                'Parameter': category,
                                'Value': values
                            })
                    
                    if assumptions_list:
                        assumptions_df = pd.DataFrame(assumptions_list)
                        assumptions_df.to_excel(writer, sheet_name='Assumptions', index=False)
            
            # 4. Summary Metrics
            if 'summary_metrics' in plan_data and plan_data['summary_metrics']:
                summary_metrics = plan_data['summary_metrics']
                
                if isinstance(summary_metrics, dict):
                    metrics_list = []
                    
                    for key, value in summary_metrics.items():
                        metrics_list.append({
                            'Metric': key.replace('_', ' ').title(),
                            'Value': value
                        })
                    
                    if metrics_list:
                        metrics_df = pd.DataFrame(metrics_list)
                        metrics_df.to_excel(writer, sheet_name='Summary Metrics', index=False)
        
        excel_data = output.getvalue()
        
        # Сохраняем в файл если указано имя
        if filename:
            with open(filename, 'wb') as f:
                f.write(excel_data)
        
        return excel_data
    
    def _export_plan_to_pdf(self, plan_data: Dict[str, Any],
                           filename: Optional[str] = None) -> bytes:
        """Экспорт плана в PDF"""
        
        buffer = io.BytesIO()
        
        if filename:
            doc = SimpleDocTemplate(filename, pagesize=A4)
        else:
            doc = SimpleDocTemplate(buffer, pagesize=A4)
        
        elements = []
        
        # Заголовок
        elements.append(Paragraph("Financial Plan Report", self.styles['CustomTitle']))
        elements.append(Spacer(1, 0.25*inch))
        
        # Plan Information
        elements.append(Paragraph("Plan Information", self.styles['CustomHeading1']))
        elements.append(Spacer(1, 0.1*inch))
        
        plan_info = [
            ['Plan Name:', plan_data.get('plan_name', 'N/A')],
            ['Plan Year:', str(plan_data.get('plan_year', 'N/A'))],
            ['Created:', plan_data.get('created_at', datetime.now().isoformat())],
            ['Description:', plan_data.get('description', '')]
        ]
        
        plan_table = Table(plan_info, colWidths=[2*inch, 4*inch])
        plan_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('FONTSIZE', (0, 0), (-1, -1), 9)
        ]))
        
        elements.append(plan_table)
        elements.append(Spacer(1, 0.25*inch))
        
        # Monthly Plans Summary
        if 'monthly_plans' in plan_data and plan_data['monthly_plans']:
            elements.append(Paragraph("Monthly Plans Summary", self.styles['CustomHeading1']))
            elements.append(Spacer(1, 0.1*inch))
            
            monthly_data = plan_data['monthly_plans']
            if len(monthly_data) > 0:
                # Создаем таблицу с key metrics
                table_data = [['Month', 'MRR', 'Revenue', 'Costs', 'Profit', 'Runway']]
                
                for plan in monthly_data[:12]:  # Первые 12 месяцев
                    if isinstance(plan, dict):
                        mrr = plan.get('plan_mrr', 0)
                        revenue = plan.get('plan_total_revenue', 0)
                        costs = plan.get('plan_total_costs', 0)
                        profit = revenue - costs
                        runway = plan.get('plan_runway', 0)
                        
                        table_data.append([
                            plan.get('month_name', plan.get('month_number', '')),
                            f"${mrr:,.0f}",
                            f"${revenue:,.0f}",
                            f"${costs:,.0f}",
                            f"${profit:,.0f}",
                            f"{runway:.1f} months"
                        ])
                
                if len(table_data) > 1:
                    monthly_table = Table(table_data, colWidths=[0.8*inch, 1*inch, 1*inch, 1*inch, 1*inch, 1*inch])
                    monthly_table.setStyle(TableStyle([
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E86C1')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('PADDING', (0, 0), (-1, -1), 4),
                        ('FONTSIZE', (0, 0), (-1, -1), 8)
                    ]))
                    
                    elements.append(monthly_table)
            
            elements.append(Spacer(1, 0.25*inch))
        
        # Summary Metrics
        if 'summary_metrics' in plan_data and plan_data['summary_metrics']:
            elements.append(Paragraph("Plan Summary Metrics", self.styles['CustomHeading1']))
            elements.append(Spacer(1, 0.1*inch))
            
            summary_metrics = plan_data['summary_metrics']
            
            if isinstance(summary_metrics, dict):
                metrics_data = []
                
                key_metrics = [
                    ('total_12month_revenue', 'Total 12-Month Revenue'),
                    ('total_12month_costs', 'Total 12-Month Costs'),
                    ('total_12month_profit', 'Total 12-Month Profit'),
                    ('ending_cash_balance', 'Ending Cash Balance'),
                    ('min_runway_months', 'Minimum Runway'),
                    ('breakeven_month', 'Breakeven Month')
                ]
                
                for key, label in key_metrics:
                    if key in summary_metrics:
                        value = summary_metrics[key]
                        
                        if 'revenue' in key or 'costs' in key or 'profit' in key or 'cash' in key:
                            formatted_value = f"${value:,.0f}"
                        elif key == 'breakeven_month':
                            formatted_value = f"Month {value}" if value else 'N/A'
                        else:
                            formatted_value = f"{value:,.1f}"
                        
                        metrics_data.append([label, formatted_value])
                
                if metrics_data:
                    metrics_table = Table(metrics_data, colWidths=[2.5*inch, 1.5*inch])
                    metrics_table.setStyle(TableStyle([
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                        ('PADDING', (0, 0), (-1, -1), 6),
                        ('FONTSIZE', (0, 0), (-1, -1), 9)
                    ]))
                    
                    elements.append(metrics_table)
        
        # Footer
        elements.append(Spacer(1, 0.5*inch))
        elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", self.styles['CustomSmall']))
        elements.append(Paragraph("SaaS Unit Economics Tool - Financial Plan Report", self.styles['CustomSmall']))
        
        # Собираем документ
        doc.build(elements)
        
        # Получаем байты если сохраняли в buffer
        if not filename:
            pdf_data = buffer.getvalue()
            buffer.close()
            return pdf_data
        
        return None
    
    def export_dataframe(self, df: pd.DataFrame,
                        export_format: ExportFormat,
                        filename: Optional[str] = None) -> Union[bytes, str, None]:
        """
        Экспорт DataFrame в различные форматы
        
        Args:
            df: DataFrame для экспорта
            export_format: Формат экспорта
            filename: Имя файла (опционально)
        
        Returns:
            Данные экспорта или путь к файлу
        """
        
        if export_format == ExportFormat.EXCEL:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Data')
            excel_data = output.getvalue()
            
            if filename:
                with open(filename, 'wb') as f:
                    f.write(excel_data)
            return excel_data
        
        elif export_format == ExportFormat.CSV:
            csv_data = df.to_csv(index=False)
            
            if filename:
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    f.write(csv_data)
            return csv_data
        
        elif export_format == ExportFormat.JSON:
            json_data = df.to_json(orient='records', indent=2)
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(json_data)
            return json_data
        
        elif export_format == ExportFormat.HTML:
            html_data = df.to_html(index=False, classes='table table-striped')
            
            # Добавляем базовый HTML wrapper
            full_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    table {{ border-collapse: collapse; width: 100%; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #4CAF50; color: white; }}
                    tr:nth-child(even) {{ background-color: #f2f2f2; }}
                </style>
            </head>
            <body>
                <h2>Data Export</h2>
                <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                {html_data}
            </body>
            </html>
            """
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(full_html)
            return full_html
        
        else:
            raise ValueError(f"Unsupported export format for DataFrame: {export_format}")

# Создаем глобальный экземпляр генератора экспортов
export_generator = ExportGenerator()

# Экспортируем полезные функции
def export_report(company_data: Dict[str, Any], 
                 report_data: Dict[str, Any],
                 format_str: str,
                 filename: Optional[str] = None) -> Union[bytes, str, None]:
    """Публичная функция для экспорта отчета"""
    try:
        export_format = ExportFormat(format_str.lower())
    except ValueError:
        raise ValueError(f"Unsupported export format: {format_str}. Supported formats: {[f.value for f in ExportFormat]}")
    
    return export_generator.export_company_report(company_data, report_data, export_format, filename)

def export_financial_plan(plan_data: Dict[str, Any],
                         format_str: str,
                         filename: Optional[str] = None) -> Union[bytes, str, None]:
    """Публичная функция для экспорта финансового плана"""
    try:
        export_format = ExportFormat(format_str.lower())
    except ValueError:
        raise ValueError(f"Unsupported export format: {format_str}. Supported formats: {[f.value for f in ExportFormat]}")
    
    return export_generator.export_financial_plan(plan_data, export_format, filename)

def export_dataframe_to_file(df: pd.DataFrame,
                            format_str: str,
                            filename: str) -> None:
    """Публичная функция для экспорта DataFrame в файл"""
    try:
        export_format = ExportFormat(format_str.lower())
    except ValueError:
        raise ValueError(f"Unsupported export format: {format_str}. Supported formats: {[f.value for f in ExportFormat]}")
    
    export_generator.export_dataframe(df, export_format, filename)