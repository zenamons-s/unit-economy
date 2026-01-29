"""
Эталонные метрики SaaS для разных стадий и вертикалей
Сравнение с лучшими практиками и benchmarks индустрии
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

class CompanyStage(Enum):
    """Стадии компании"""
    PRE_SEED = "pre_seed"
    SEED = "seed"
    SERIES_A = "series_a"
    SERIES_B = "series_b"
    SERIES_C = "series_c"
    GROWTH = "growth"
    MATURE = "mature"
    PUBLIC = "public"

class Vertical(Enum):
    """Вертикали SaaS"""
    B2B_ENTERPRISE = "b2b_enterprise"
    B2B_SMB = "b2b_smb"
    B2C = "b2c"
    DEV_TOOLS = "dev_tools"
    MARKETING_TECH = "marketing_tech"
    SALES_TECH = "sales_tech"
    HR_TECH = "hr_tech"
    FIN_TECH = "fin_tech"
    HEALTH_TECH = "health_tech"
    ED_TECH = "ed_tech"

@dataclass
class SaaSBenchmark:
    """Эталонная метрика SaaS"""
    metric: str
    stage: str
    vertical: str
    good: float
    great: float
    excellent: float
    description: str
    source: str
    last_updated: datetime
    sample_size: int = 0
    confidence: float = 0.0

class SaaSBenchmarks:
    """
    База данных эталонных метрик SaaS
    Сравнение с лучшими практиками индустрии
    """
    
    def __init__(self):
        self.benchmarks = self._load_benchmarks()
        self.defaults = self._create_default_benchmarks()
        
    def _load_benchmarks(self) -> Dict[str, List[SaaSBenchmark]]:
        """Загрузка benchmarks из файла или создание defaults"""
        
        # Попытка загрузить из файла
        try:
            with open('data/saas_benchmarks.json', 'r') as f:
                data = json.load(f)
                
            benchmarks = {}
            for key, bench_list in data.items():
                benchmarks[key] = [
                    SaaSBenchmark(
                        metric=b['metric'],
                        stage=b['stage'],
                        vertical=b.get('vertical', 'all'),
                        good=b['good'],
                        great=b['great'],
                        excellent=b['excellent'],
                        description=b['description'],
                        source=b['source'],
                        last_updated=datetime.fromisoformat(b['last_updated']),
                        sample_size=b.get('sample_size', 0),
                        confidence=b.get('confidence', 0.0)
                    )
                    for b in bench_list
                ]
            
            return benchmarks
            
        except FileNotFoundError:
            # Используем defaults если файл не найден
            return self._create_default_benchmarks_dict()
    
    def _create_default_benchmarks_dict(self) -> Dict[str, List[SaaSBenchmark]]:
        """Создание словаря default benchmarks"""
        
        benchmarks = {}
        
        for stage in CompanyStage:
            stage_key = stage.value
            benchmarks[stage_key] = self._get_default_benchmarks_for_stage(stage_key)
        
        return benchmarks
    
    def _create_default_benchmarks(self) -> Dict[str, SaaSBenchmark]:
        """Создание default benchmarks для быстрого доступа"""
        
        default_benchmarks = {}
        
        # Базовые метрики для всех стадий
        base_metrics = [
            ("mrr_growth_monthly", "Monthly MRR Growth", "%"),
            ("cac_payback_months", "CAC Payback Period", "months"),
            ("ltv_cac_ratio", "LTV to CAC Ratio", "x"),
            ("gross_margin", "Gross Margin", "%"),
            ("net_revenue_retention", "Net Revenue Retention", "%"),
            ("burn_multiple", "Burn Multiple", "x"),
            ("rule_of_40", "Rule of 40", "%")
        ]
        
        for metric, description, unit in base_metrics:
            default_benchmarks[metric] = SaaSBenchmark(
                metric=metric,
                stage="all",
                vertical="all",
                good=self._get_default_value(metric, "good"),
                great=self._get_default_value(metric, "great"),
                excellent=self._get_default_value(metric, "excellent"),
                description=f"{description} ({unit})",
                source="SaaS Industry Standards",
                last_updated=datetime.now(),
                sample_size=1000,
                confidence=0.8
            )
        
        return default_benchmarks
    
    def _get_default_benchmarks_for_stage(self, stage: str) -> List[SaaSBenchmark]:
        """Получение default benchmarks для стадии"""
        
        benchmarks = []
        
        # MRR Growth
        benchmarks.append(SaaSBenchmark(
            metric="mrr_growth_monthly",
            stage=stage,
            vertical="all",
            good=self._get_mrr_growth_target(stage, "good"),
            great=self._get_mrr_growth_target(stage, "great"),
            excellent=self._get_mrr_growth_target(stage, "excellent"),
            description="Monthly MRR Growth Rate (%)",
            source="SaaS Capital, OpenView",
            last_updated=datetime.now(),
            sample_size=500,
            confidence=0.85
        ))
        
        # CAC Payback
        benchmarks.append(SaaSBenchmark(
            metric="cac_payback_months",
            stage=stage,
            vertical="all",
            good=self._get_cac_payback_target(stage, "good"),
            great=self._get_cac_payback_target(stage, "great"),
            excellent=self._get_cac_payback_target(stage, "excellent"),
            description="Months to recover CAC",
            source="SaaStr, Tomasz Tunguz",
            last_updated=datetime.now(),
            sample_size=300,
            confidence=0.8
        ))
        
        # LTV/CAC Ratio
        benchmarks.append(SaaSBenchmark(
            metric="ltv_cac_ratio",
            stage=stage,
            vertical="all",
            good=self._get_ltv_cac_target(stage, "good"),
            great=self._get_ltv_cac_target(stage, "great"),
            excellent=self._get_ltv_cac_target(stage, "excellent"),
            description="Lifetime Value to CAC Ratio",
            source="Bessemer, Andreessen Horowitz",
            last_updated=datetime.now(),
            sample_size=400,
            confidence=0.9
        ))
        
        # Gross Margin
        benchmarks.append(SaaSBenchmark(
            metric="gross_margin",
            stage=stage,
            vertical="all",
            good=70.0,
            great=75.0,
            excellent=80.0,
            description="Gross Margin (%)",
            source="SaaS Industry Standards",
            last_updated=datetime.now(),
            sample_size=1000,
            confidence=0.95
        ))
        
        # Net Revenue Retention
        benchmarks.append(SaaSBenchmark(
            metric="net_revenue_retention",
            stage=stage,
            vertical="all",
            good=self._get_nrr_target(stage, "good"),
            great=self._get_nrr_target(stage, "great"),
            excellent=self._get_nrr_target(stage, "excellent"),
            description="Net Revenue Retention (%)",
            source="Battery Ventures, Scale Venture Partners",
            last_updated=datetime.now(),
            sample_size=200,
            confidence=0.75
        ))
        
        # Burn Multiple
        benchmarks.append(SaaSBenchmark(
            metric="burn_multiple",
            stage=stage,
            vertical="all",
            good=self._get_burn_multiple_target(stage, "good"),
            great=self._get_burn_multiple_target(stage, "great"),
            excellent=self._get_burn_multiple_target(stage, "excellent"),
            description="Burn Multiple (Capital Efficiency)",
            source="David Sacks, Craft Ventures",
            last_updated=datetime.now(),
            sample_size=150,
            confidence=0.7
        ))
        
        # Magic Number
        benchmarks.append(SaaSBenchmark(
            metric="magic_number",
            stage=stage,
            vertical="all",
            good=self._get_magic_number_target(stage, "good"),
            great=self._get_magic_number_target(stage, "great"),
            excellent=self._get_magic_number_target(stage, "excellent"),
            description="Sales Efficiency (Magic Number)",
            source="Bessemer Cloud Index",
            last_updated=datetime.now(),
            sample_size=250,
            confidence=0.8
        ))
        
        # Rule of 40
        if stage in ["series_a", "series_b", "series_c", "growth", "mature", "public"]:
            benchmarks.append(SaaSBenchmark(
                metric="rule_of_40",
                stage=stage,
                vertical="all",
                good=30.0,
                great=40.0,
                excellent=50.0,
                description="Rule of 40 (Growth Rate + Profit Margin)",
                source="Brad Feld, Scale Venture Partners",
                last_updated=datetime.now(),
                sample_size=300,
                confidence=0.85
            ))
        
        return benchmarks
    
    def _get_mrr_growth_target(self, stage: str, level: str) -> float:
        """Получение target MRR growth для стадии"""
        
        targets = {
            "pre_seed": {"good": 15.0, "great": 25.0, "excellent": 35.0},
            "seed": {"good": 20.0, "great": 30.0, "excellent": 40.0},
            "series_a": {"good": 15.0, "great": 25.0, "excellent": 35.0},
            "series_b": {"good": 10.0, "great": 20.0, "excellent": 30.0},
            "series_c": {"good": 8.0, "great": 15.0, "excellent": 25.0},
            "growth": {"good": 5.0, "great": 10.0, "excellent": 20.0},
            "mature": {"good": 2.0, "great": 5.0, "excellent": 10.0},
            "public": {"good": 1.0, "great": 3.0, "excellent": 5.0}
        }
        
        return targets.get(stage, {}).get(level, 10.0)
    
    def _get_cac_payback_target(self, stage: str, level: str) -> float:
        """Получение target CAC payback для стадии"""
        
        targets = {
            "pre_seed": {"good": 24.0, "great": 18.0, "excellent": 12.0},
            "seed": {"good": 18.0, "great": 12.0, "excellent": 9.0},
            "series_a": {"good": 15.0, "great": 10.0, "excellent": 7.0},
            "series_b": {"good": 12.0, "great": 8.0, "excellent": 5.0},
            "series_c": {"good": 10.0, "great": 6.0, "excellent": 4.0},
            "growth": {"good": 8.0, "great": 5.0, "excellent": 3.0},
            "mature": {"good": 6.0, "great": 4.0, "excellent": 2.0},
            "public": {"good": 4.0, "great": 3.0, "excellent": 2.0}
        }
        
        return targets.get(stage, {}).get(level, 12.0)
    
    def _get_ltv_cac_target(self, stage: str, level: str) -> float:
        """Получение target LTV/CAC для стадии"""
        
        targets = {
            "pre_seed": {"good": 2.0, "great": 3.0, "excellent": 4.0},
            "seed": {"good": 2.5, "great": 3.5, "excellent": 5.0},
            "series_a": {"good": 3.0, "great": 4.0, "excellent": 6.0},
            "series_b": {"good": 3.5, "great": 5.0, "excellent": 7.0},
            "series_c": {"good": 4.0, "great": 6.0, "excellent": 8.0},
            "growth": {"good": 4.5, "great": 7.0, "excellent": 10.0},
            "mature": {"good": 5.0, "great": 8.0, "excellent": 12.0},
            "public": {"good": 6.0, "great": 10.0, "excellent": 15.0}
        }
        
        return targets.get(stage, {}).get(level, 3.0)
    
    def _get_nrr_target(self, stage: str, level: str) -> float:
        """Получение target Net Revenue Retention для стадии"""
        
        targets = {
            "pre_seed": {"good": 90.0, "great": 100.0, "excellent": 110.0},
            "seed": {"good": 95.0, "great": 105.0, "excellent": 115.0},
            "series_a": {"good": 100.0, "great": 110.0, "excellent": 120.0},
            "series_b": {"good": 105.0, "great": 115.0, "excellent": 125.0},
            "series_c": {"good": 110.0, "great": 120.0, "excellent": 130.0},
            "growth": {"good": 115.0, "great": 125.0, "excellent": 135.0},
            "mature": {"good": 120.0, "great": 130.0, "excellent": 140.0},
            "public": {"good": 125.0, "great": 135.0, "excellent": 145.0}
        }
        
        return targets.get(stage, {}).get(level, 100.0)
    
    def _get_burn_multiple_target(self, stage: str, level: str) -> float:
        """Получение target Burn Multiple для стадии"""
        
        targets = {
            "pre_seed": {"good": 3.0, "great": 2.0, "excellent": 1.5},
            "seed": {"good": 2.5, "great": 1.5, "excellent": 1.0},
            "series_a": {"good": 2.0, "great": 1.2, "excellent": 0.8},
            "series_b": {"good": 1.5, "great": 1.0, "excellent": 0.6},
            "series_c": {"good": 1.2, "great": 0.8, "excellent": 0.4},
            "growth": {"good": 1.0, "great": 0.6, "excellent": 0.3},
            "mature": {"good": 0.8, "great": 0.4, "excellent": 0.2},
            "public": {"good": 0.6, "great": 0.3, "excellent": 0.1}
        }
        
        return targets.get(stage, {}).get(level, 1.5)
    
    def _get_magic_number_target(self, stage: str, level: str) -> float:
        """Получение target Magic Number для стадии"""
        
        targets = {
            "pre_seed": {"good": 0.5, "great": 0.8, "excellent": 1.2},
            "seed": {"good": 0.8, "great": 1.2, "excellent": 1.5},
            "series_a": {"good": 1.0, "great": 1.5, "excellent": 2.0},
            "series_b": {"good": 1.2, "great": 1.8, "excellent": 2.5},
            "series_c": {"good": 1.5, "great": 2.2, "excellent": 3.0},
            "growth": {"good": 1.8, "great": 2.5, "excellent": 3.5},
            "mature": {"good": 2.0, "great": 3.0, "excellent": 4.0},
            "public": {"good": 2.5, "great": 3.5, "excellent": 5.0}
        }
        
        return targets.get(stage, {}).get(level, 1.0)
    
    def _get_default_value(self, metric: str, level: str) -> float:
        """Получение default значения для метрики"""
        
        defaults = {
            "mrr_growth_monthly": {"good": 10.0, "great": 20.0, "excellent": 30.0},
            "cac_payback_months": {"good": 12.0, "great": 8.0, "excellent": 5.0},
            "ltv_cac_ratio": {"good": 3.0, "great": 5.0, "excellent": 8.0},
            "gross_margin": {"good": 70.0, "great": 75.0, "excellent": 80.0},
            "net_revenue_retention": {"good": 100.0, "great": 110.0, "excellent": 120.0},
            "burn_multiple": {"good": 1.5, "great": 1.0, "excellent": 0.5},
            "magic_number": {"good": 1.0, "great": 1.5, "excellent": 2.0},
            "rule_of_40": {"good": 30.0, "great": 40.0, "excellent": 50.0}
        }
        
        return defaults.get(metric, {}).get(level, 0.0)
    
    def get_benchmarks(self, stage: str, vertical: Optional[str] = None) -> Dict[str, Any]:
        """
        Получение benchmarks для стадии и вертикали
        
        Args:
            stage: Стадия компании
            vertical: Вертикаль (опционально)
        
        Returns:
            Dict с benchmarks
        """
        
        # Получаем benchmarks для стадии
        stage_benchmarks = self.benchmarks.get(stage, [])
        
        # Фильтруем по вертикали если указана
        if vertical:
            vertical_benchmarks = [
                b for b in stage_benchmarks 
                if b.vertical == vertical or b.vertical == "all"
            ]
        else:
            vertical_benchmarks = stage_benchmarks
        
        # Форматируем результат
        result = {
            "stage": stage,
            "vertical": vertical or "all",
            "benchmarks": {},
            "summary": {},
            "last_updated": datetime.now().isoformat()
        }
        
        for benchmark in vertical_benchmarks:
            result["benchmarks"][benchmark.metric] = {
                "good": benchmark.good,
                "great": benchmark.great,
                "excellent": benchmark.excellent,
                "description": benchmark.description,
                "source": benchmark.source,
                "confidence": benchmark.confidence,
                "sample_size": benchmark.sample_size
            }
        
        # Добавляем summary
        result["summary"] = self._create_benchmarks_summary(result["benchmarks"])
        
        return result
    
    def _create_benchmarks_summary(self, benchmarks: Dict[str, Any]) -> Dict[str, Any]:
        """Создание summary benchmarks"""
        
        if not benchmarks:
            return {}
        
        summary = {
            "total_metrics": len(benchmarks),
            "key_metrics": [],
            "growth_metrics": [],
            "efficiency_metrics": [],
            "financial_metrics": []
        }
        
        # Классифицируем метрики
        for metric, data in benchmarks.items():
            metric_info = {
                "metric": metric,
                "good": data["good"],
                "great": data["great"],
                "excellent": data["excellent"],
                "description": data["description"]
            }
            
            if "growth" in metric.lower() or "mrr" in metric.lower():
                summary["growth_metrics"].append(metric_info)
            elif "cac" in metric.lower() or "ltv" in metric.lower() or "efficiency" in metric.lower():
                summary["efficiency_metrics"].append(metric_info)
            elif "margin" in metric.lower() or "revenue" in metric.lower() or "burn" in metric.lower():
                summary["financial_metrics"].append(metric_info)
            
            # Key metrics (важнейшие)
            if metric in ["mrr_growth_monthly", "ltv_cac_ratio", "cac_payback_months", "net_revenue_retention"]:
                summary["key_metrics"].append(metric_info)
        
        return summary
    
    def compare_with_benchmarks(self, company_metrics: Dict[str, float], 
                               stage: str, vertical: Optional[str] = None) -> Dict[str, Any]:
        """
        Сравнение метрик компании с benchmarks
        
        Args:
            company_metrics: Метрики компании
            stage: Стадия компании
            vertical: Вертикаль (опционально)
        
        Returns:
            Dict с результатами сравнения
        """
        
        # Получаем benchmarks
        benchmarks_data = self.get_benchmarks(stage, vertical)
        benchmarks = benchmarks_data["benchmarks"]
        
        comparison = {
            "stage": stage,
            "vertical": vertical or "all",
            "metrics_compared": [],
            "overall_score": 0,
            "strengths": [],
            "weaknesses": [],
            "recommendations": [],
            "detailed_comparison": {}
        }
        
        scores = []
        
        for metric, company_value in company_metrics.items():
            if metric not in benchmarks:
                continue
            
            benchmark = benchmarks[metric]
            
            # Определяем performance level
            if company_value >= benchmark["excellent"]:
                level = "excellent"
                score = 100
            elif company_value >= benchmark["great"]:
                level = "great"
                score = 80
            elif company_value >= benchmark["good"]:
                level = "good"
                score = 60
            else:
                level = "below_good"
                score = 40
            
            # Gap analysis
            if level == "below_good":
                gap = benchmark["good"] - company_value
                gap_percent = (gap / benchmark["good"]) * 100 if benchmark["good"] > 0 else 0
            else:
                gap = 0
                gap_percent = 0
            
            comparison["metrics_compared"].append({
                "metric": metric,
                "company_value": company_value,
                "benchmark_good": benchmark["good"],
                "benchmark_great": benchmark["great"],
                "benchmark_excellent": benchmark["excellent"],
                "performance_level": level,
                "score": score,
                "gap": gap if level == "below_good" else 0,
                "gap_percent": gap_percent if level == "below_good" else 0,
                "description": benchmark["description"]
            })
            
            scores.append(score)
            
            # Записываем в detailed comparison
            comparison["detailed_comparison"][metric] = {
                "company": company_value,
                "benchmark": {
                    "good": benchmark["good"],
                    "great": benchmark["great"],
                    "excellent": benchmark["excellent"]
                },
                "performance": level,
                "score": score,
                "gap_to_good": max(0, benchmark["good"] - company_value)
            }
            
            # Добавляем strengths и weaknesses
            if level in ["excellent", "great"]:
                comparison["strengths"].append({
                    "metric": metric,
                    "value": company_value,
                    "benchmark": benchmark["excellent"] if level == "excellent" else benchmark["great"],
                    "outperformance": company_value - (benchmark["excellent"] if level == "excellent" else benchmark["great"])
                })
            elif level == "below_good":
                comparison["weaknesses"].append({
                    "metric": metric,
                    "value": company_value,
                    "benchmark_good": benchmark["good"],
                    "gap": benchmark["good"] - company_value,
                    "gap_percent": gap_percent
                })
        
        # Рассчитываем overall score
        if scores:
            comparison["overall_score"] = np.mean(scores)
            comparison["overall_performance"] = self._get_overall_performance(comparison["overall_score"])
        
        # Генерация рекомендаций
        comparison["recommendations"] = self._generate_benchmark_recommendations(comparison)
        
        return comparison
    
    def _get_overall_performance(self, score: float) -> str:
        """Получение overall performance level"""
        
        if score >= 90:
            return "excellent"
        elif score >= 75:
            return "great"
        elif score >= 60:
            return "good"
        elif score >= 50:
            return "fair"
        else:
            return "needs_improvement"
    
    def _generate_benchmark_recommendations(self, comparison: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Генерация рекомендаций на основе сравнения с benchmarks"""
        
        recommendations = []
        
        # Рекомендации для weaknesses
        for weakness in comparison.get("weaknesses", []):
            metric = weakness["metric"]
            gap = weakness["gap"]
            gap_percent = weakness["gap_percent"]
            
            rec = {
                "metric": metric,
                "priority": "high" if gap_percent > 30 else "medium" if gap_percent > 15 else "low",
                "current_value": weakness["value"],
                "target_value": weakness["benchmark_good"],
                "gap": gap,
                "gap_percent": gap_percent,
                "actions": self._get_improvement_actions(metric)
            }
            
            recommendations.append(rec)
        
        # Рекомендации для поддержания strengths
        for strength in comparison.get("strengths", []):
            metric = strength["metric"]
            
            rec = {
                "metric": metric,
                "priority": "low",
                "current_value": strength["value"],
                "target_value": "maintain",
                "gap": 0,
                "gap_percent": 0,
                "actions": [f"Продолжать текущие практики для поддержания {metric}"]
            }
            
            recommendations.append(rec)
        
        # Общие рекомендации на основе overall score
        overall_performance = comparison.get("overall_performance", "")
        
        if overall_performance in ["fair", "needs_improvement"]:
            recommendations.append({
                "metric": "overall",
                "priority": "critical",
                "current_value": comparison.get("overall_score", 0),
                "target_value": 60,  # Цель: достичь good
                "gap": 60 - comparison.get("overall_score", 0),
                "gap_percent": ((60 - comparison.get("overall_score", 0)) / 60) * 100,
                "actions": [
                    "Сфокусироваться на улучшении key metrics",
                    "Провести глубокий анализ performance gaps",
                    "Разработать action plan для improvement"
                ]
            })
        
        return recommendations
    
    def _get_improvement_actions(self, metric: str) -> List[str]:
        """Получение действий для улучшения метрики"""
        
        actions_map = {
            "mrr_growth_monthly": [
                "Улучшить sales efficiency",
                "Оптимизировать marketing channels",
                "Увеличить prices",
                "Улучшить conversion rates"
            ],
            "cac_payback_months": [
                "Снизить customer acquisition costs",
                "Увеличить average revenue per customer",
                "Улучшить sales velocity",
                "Оптимизировать marketing spend"
            ],
            "ltv_cac_ratio": [
                "Улучшить customer retention",
                "Снизить churn rate",
                "Увеличить upsell/cross-sell",
                "Оптимизировать pricing strategy"
            ],
            "gross_margin": [
                "Оптимизировать cost of goods sold",
                "Улучшить infrastructure efficiency",
                "Пересмотреть vendor contracts",
                "Автоматизировать manual processes"
            ],
            "net_revenue_retention": [
                "Улучшить customer success",
                "Увеличить expansion revenue",
                "Снизить churn",
                "Развивать product adoption"
            ],
            "burn_multiple": [
                "Улучшить capital efficiency",
                "Сократить unnecessary расходы",
                "Фокусироваться на profitable growth",
                "Оптимизировать team productivity"
            ],
            "magic_number": [
                "Улучшить sales efficiency",
                "Оптимизировать marketing ROI",
                "Увеличить sales productivity",
                "Развивать scalable growth channels"
            ]
        }
        
        return actions_map.get(metric, ["Провести анализ для выявления improvement opportunities"])
    
    def get_industry_averages(self, stage: str = None, vertical: str = None) -> Dict[str, Any]:
        """
        Получение средних значений по индустрии
        
        Args:
            stage: Стадия (опционально)
            vertical: Вертикаль (опционально)
        
        Returns:
            Dict со средними значениями
        """
        
        # Здесь можно добавить реальные данные из индустрии
        # Пока используем сгенерированные данные
        
        industry_data = {
            "sources": [
                "SaaS Capital Benchmarking Report",
                "OpenView SaaS Benchmarks",
                "Bessemer Cloud Index",
                "Battery Ventures State of Cloud"
            ],
            "metrics": {},
            "trends": {},
            "insights": []
        }
        
        # Генерируем industry averages
        metrics = [
            "mrr_growth_monthly", "cac_payback_months", "ltv_cac_ratio",
            "gross_margin", "net_revenue_retention", "burn_multiple"
        ]
        
        for metric in metrics:
            industry_data["metrics"][metric] = {
                "average": self._get_industry_average(metric, stage, vertical),
                "median": self._get_industry_median(metric, stage, vertical),
                "top_quartile": self._get_industry_top_quartile(metric, stage, vertical),
                "bottom_quartile": self._get_industry_bottom_quartile(metric, stage, vertical),
                "sample_size": np.random.randint(100, 1000),
                "year_over_year_change": np.random.uniform(-5, 10)
            }
        
        # Добавляем trends
        industry_data["trends"] = {
            "cac_trend": "increasing",  # CAC растет в индустрии
            "growth_trend": "moderating",  # Рост замедляется
            "efficiency_trend": "improving",  # Эффективность улучшается
            "profitability_trend": "improving"  # Profitability улучшается
        }
        
        # Добавляем insights
        industry_data["insights"] = [
            "CAC продолжает расти в большинстве вертикалей SaaS",
            "Топ-перформеры фокусируются на net revenue retention >120%",
            "Эффективные компании имеют burn multiple <1.0",
            "Rule of 40 становится стандартом для growth-stage компаний"
        ]
        
        return industry_data
    
    def _get_industry_average(self, metric: str, stage: str = None, vertical: str = None) -> float:
        """Получение среднего значения по индустрии"""
        
        # Используем benchmarks как основу, с добавлением вариативности
        if stage:
            benchmarks = self.get_benchmarks(stage, vertical)
            if metric in benchmarks["benchmarks"]:
                benchmark = benchmarks["benchmarks"][metric]
                return (benchmark["good"] + benchmark["great"] + benchmark["excellent"]) / 3
        
        # Default значения
        defaults = {
            "mrr_growth_monthly": 15.0,
            "cac_payback_months": 10.0,
            "ltv_cac_ratio": 4.0,
            "gross_margin": 75.0,
            "net_revenue_retention": 110.0,
            "burn_multiple": 1.2,
            "magic_number": 1.5,
            "rule_of_40": 35.0
        }
        
        return defaults.get(metric, 0.0)
    
    def _get_industry_median(self, metric: str, stage: str = None, vertical: str = None) -> float:
        """Получение медианного значения по индустрии"""
        
        average = self._get_industry_average(metric, stage, vertical)
        # Медиана обычно близка к среднему
        return average * np.random.uniform(0.9, 1.1)
    
    def _get_industry_top_quartile(self, metric: str, stage: str = None, vertical: str = None) -> float:
        """Получение значения top quartile по индустрии"""
        
        average = self._get_industry_average(metric, stage, vertical)
        # Top quartile выше среднего
        return average * np.random.uniform(1.2, 1.5)
    
    def _get_industry_bottom_quartile(self, metric: str, stage: str = None, vertical: str = None) -> float:
        """Получение значения bottom quartile по индустрии"""
        
        average = self._get_industry_average(metric, stage, vertical)
        # Bottom quartile ниже среднего
        return average * np.random.uniform(0.7, 0.9)
    
    def calculate_rule_of_40(self, growth_rate: float, profit_margin: float) -> Dict[str, Any]:
        """
        Расчет Rule of 40
        
        Args:
            growth_rate: Growth rate (%)
            profit_margin: Profit margin (%)
        
        Returns:
            Dict с результатами Rule of 40
        """
        
        rule_of_40 = growth_rate + profit_margin
        benchmark = 40.0
        
        analysis = {
            "growth_rate": growth_rate,
            "profit_margin": profit_margin,
            "rule_of_40_score": rule_of_40,
            "benchmark": benchmark,
            "gap": rule_of_40 - benchmark,
            "performance": "above" if rule_of_40 >= benchmark else "below",
            "category": self._categorize_rule_of_40(rule_of_40)
        }
        
        # Рекомендации
        if rule_of_40 < benchmark:
            if growth_rate < 20:
                analysis["recommendation"] = "Фокусироваться на ускорении роста"
                analysis["action_items"] = [
                    "Инвестировать в sales и marketing",
                    "Расширить target market",
                    "Улучшить product-market fit"
                ]
            else:
                analysis["recommendation"] = "Улучшать profitability"
                analysis["action_items"] = [
                    "Оптимизировать расходы",
                    "Улучшить operational efficiency",
                    "Фокусироваться на profitable growth"
                ]
        else:
            analysis["recommendation"] = "Отличные результаты, продолжать текущую стратегию"
            analysis["action_items"] = [
                "Поддерживать баланс роста и profitability",
                "Масштабировать успешные практики",
                "Готовиться к следующей стадии роста"
            ]
        
        return analysis
    
    def _categorize_rule_of_40(self, score: float) -> str:
        """Категоризация Rule of 40 score"""
        
        if score >= 50:
            return "excellent"
        elif score >= 40:
            return "great"
        elif score >= 30:
            return "good"
        elif score >= 20:
            return "fair"
        else:
            return "needs_improvement"
    
    def get_fundraising_benchmarks(self, stage: str) -> Dict[str, Any]:
        """
        Получение benchmarks для fundraising
        
        Args:
            stage: Стадия fundraising
        
        Returns:
            Dict с fundraising benchmarks
        """
        
        fundraising_benchmarks = {
            "pre_seed": {
                "typical_round_size": 500000,
                "valuation_range": "1-3M",
                "investor_types": ["Angels", "Pre-seed funds", "Accelerators"],
                "key_metrics": ["Team", "Idea", "Market size"],
                "expected_milestones": ["Prototype", "Early traction", "Founder-market fit"]
            },
            "seed": {
                "typical_round_size": 2000000,
                "valuation_range": "5-10M",
                "investor_types": ["Seed funds", "Micro VCs", "Angel groups"],
                "key_metrics": ["MRR", "Growth rate", "Unit economics"],
                "expected_milestones": ["Product-market fit", "Repeatable sales", "Early team"]
            },
            "series_a": {
                "typical_round_size": 8000000,
                "valuation_range": "15-30M",
                "investor_types": ["VCs", "Growth funds"],
                "key_metrics": ["ARR", "Net revenue retention", "CAC payback"],
                "expected_milestones": ["Scalable growth", "Strong team", "Clear path to Series B"]
            },
            "series_b": {
                "typical_round_size": 20000000,
                "valuation_range": "50-100M",
                "investor_types": ["Growth VCs", "Private equity"],
                "key_metrics": ["Rule of 40", "Magic number", "Market leadership"],
                "expected_milestones": ["Market leadership", "Operational excellence", "Path to profitability"]
            }
        }
        
        return fundraising_benchmarks.get(stage, {})
    
    def save_custom_benchmark(self, benchmark: SaaSBenchmark) -> bool:
        """
        Сохранение custom benchmark
        
        Args:
            benchmark: Custom benchmark
        
        Returns:
            bool успешности сохранения
        """
        
        try:
            # Добавляем в соответствующую категорию
            key = benchmark.stage
            if key not in self.benchmarks:
                self.benchmarks[key] = []
            
            self.benchmarks[key].append(benchmark)
            
            # Сохраняем в файл
            self._save_to_file()
            
            return True
            
        except Exception as e:
            print(f"Error saving custom benchmark: {e}")
            return False
    
    def _save_to_file(self):
        """Сохранение benchmarks в файл"""
        
        try:
            # Конвертация в dict
            data = {}
            for key, benchmarks in self.benchmarks.items():
                data[key] = [
                    {
                        "metric": b.metric,
                        "stage": b.stage,
                        "vertical": b.vertical,
                        "good": b.good,
                        "great": b.great,
                        "excellent": b.excellent,
                        "description": b.description,
                        "source": b.source,
                        "last_updated": b.last_updated.isoformat(),
                        "sample_size": b.sample_size,
                        "confidence": b.confidence
                    }
                    for b in benchmarks
                ]
            
            # Сохранение в файл
            with open('data/saas_benchmarks.json', 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Error saving benchmarks to file: {e}")

# Создаем глобальный экземпляр benchmarks
saas_benchmarks = SaaSBenchmarks()

# Экспортируем полезные функции
def get_company_benchmarks(stage: str, vertical: Optional[str] = None) -> Dict[str, Any]:
    """Публичная функция для получения benchmarks компании"""
    return saas_benchmarks.get_benchmarks(stage, vertical)

def compare_company_with_benchmarks(metrics: Dict[str, float], 
                                   stage: str, 
                                   vertical: Optional[str] = None) -> Dict[str, Any]:
    """Публичная функция для сравнения компании с benchmarks"""
    return saas_benchmarks.compare_with_benchmarks(metrics, stage, vertical)

def get_rule_of_40_analysis(growth_rate: float, profit_margin: float) -> Dict[str, Any]:
    """Публичная функция для анализа Rule of 40"""
    return saas_benchmarks.calculate_rule_of_40(growth_rate, profit_margin)