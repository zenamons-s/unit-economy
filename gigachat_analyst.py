"""
AI аналитик на основе GigaChat API
Анализ SaaS метрик и генерация рекомендаций
Поддержка Client Secret и Client ID
"""

import os
import json
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta
import requests
from enum import Enum
import base64
import time
import ssl
import certifi
import urllib3

# Импортируем с обработкой ошибок
try:
    from database.db_manager import db_manager
except ImportError as e:
    print(f"Warning: Could not import db_manager: {e}")
    
    class MockDBManager:
        def get_company(self, company_id):
            return None
        def get_actual_financials_by_filters(self, filters):
            return []
        def get_financial_plans(self, company_id):
            return []
    
    db_manager = MockDBManager()

try:
    from services.core.stage_aware_metrics import stage_aware_metrics
except ImportError as e:
    print(f"Warning: Could not import stage_aware_metrics: {e}")
    
    class MockStageAwareMetrics:
        def calculate_metrics(self, company_id):
            return {}
        def get_key_metrics_for_stage(self, stage):
            return []
        def assess_company_metrics(self, stage, metrics):
            return {}
    
    stage_aware_metrics = MockStageAwareMetrics()

try:
    from services.financial_system.saas_benchmarks import saas_benchmarks
except ImportError as e:
    print(f"Warning: Could not import saas_benchmarks: {e}")
    
    class MockSaaSBenchmarks:
        def compare_with_benchmarks(self, company_metrics, stage):
            return {}
    
    saas_benchmarks = MockSaaSBenchmarks()

class AnalysisType(Enum):
    """Типы AI анализа"""
    FULL_BUSINESS_ANALYSIS = "full_business_analysis"
    FINANCIAL_HEALTH = "financial_health"
    GROWTH_RECOMMENDATIONS = "growth_recommendations"
    RISK_ANALYSIS = "risk_analysis"
    COMPETITIVE_ANALYSIS = "competitive_analysis"
    FORECAST_12M = "forecast_12m"
    CUSTOM_QUERY = "custom_query"

@dataclass
class AIGigaChatConfig:
    """Конфигурация GigaChat API с поддержкой Client Secret"""
    client_id: str = ""
    client_secret: str = ""
    scope: str = "GIGACHAT_API_PERS"
    base_url: str = "https://gigachat.devices.sberbank.ru/api/v1"
    auth_url: str = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    model: str = "GigaChat"
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 30
    verify_ssl: bool = False  # По умолчанию отключаем SSL проверку для тестирования

@dataclass
class GigaChatToken:
    """Токен GigaChat API"""
    access_token: str
    expires_at: datetime
    token_type: str = "Bearer"

@dataclass
class AIAnalysisRequest:
    """Запрос на AI анализ"""
    company_id: int
    analysis_type: AnalysisType
    context: Dict[str, Any]
    custom_query: Optional[str] = None
    language: str = "ru"

@dataclass
class AIAnalysisResponse:
    """Ответ AI анализа"""
    success: bool
    analysis: Dict[str, Any]
    error: Optional[str] = None
    processing_time: Optional[float] = None
    tokens_used: Optional[int] = None

class GigaChatAnalyst:
    """
    AI аналитик на основе GigaChat API
    Поддержка Client Secret и Client ID авторизации
    """
    
    def __init__(self, config: Optional[AIGigaChatConfig] = None):
        self.config = config or self._load_config()
        self.current_token: Optional[GigaChatToken] = None
        
        # Отключаем SSL warnings для тестирования
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Создаем сессию с настройками SSL
        self.session = self._create_session_with_ssl_config()
        
        # Кэш для часто запрашиваемых данных
        self.cache = {}
        
        # Статистика использования
        self.usage_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "fallback_used": 0,
            "tokens_total": 0
        }
    
    def _create_session_with_ssl_config(self) -> requests.Session:
        """Создание сессии с настройками SSL"""
        session = requests.Session()
        
        # Настраиваем адаптер с увеличенными таймаутами и ретраями
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=10
        )
        
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        
        # Настраиваем SSL верификацию в зависимости от конфигурации
        if hasattr(self, 'config') and self.config:
            session.verify = self.config.verify_ssl
        else:
            session.verify = False  # По умолчанию отключаем SSL проверку
        
        return session
    
    def _load_config(self) -> AIGigaChatConfig:
        """Загрузка конфигурации"""
        
        # Загрузка из переменных окружения
        client_id = os.getenv("GIGACHAT_CLIENT_ID", "")
        client_secret = os.getenv("GIGACHAT_CLIENT_SECRET", "")
        scope = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
        base_url = os.getenv("GIGACHAT_BASE_URL", "https://gigachat.devices.sberbank.ru/api/v1")
        auth_url = os.getenv("GIGACHAT_AUTH_URL", "https://ngw.devices.sberbank.ru:9443/api/v2/oauth")
        verify_ssl = os.getenv("GIGACHAT_VERIFY_SSL", "false").lower() == "true"
        
        # Загрузка из Streamlit secrets (если доступно)
        try:
            import streamlit as st
            if "GIGACHAT_CLIENT_ID" in st.secrets:
                client_id = st.secrets["GIGACHAT_CLIENT_ID"]
            if "GIGACHAT_CLIENT_SECRET" in st.secrets:
                client_secret = st.secrets["GIGACHAT_CLIENT_SECRET"]
            if "GIGACHAT_SCOPE" in st.secrets:
                scope = st.secrets["GIGACHAT_SCOPE"]
            if "GIGACHAT_BASE_URL" in st.secrets:
                base_url = st.secrets["GIGACHAT_BASE_URL"]
            if "GIGACHAT_AUTH_URL" in st.secrets:
                auth_url = st.secrets["GIGACHAT_AUTH_URL"]
            if "GIGACHAT_VERIFY_SSL" in st.secrets:
                verify_ssl = st.secrets["GIGACHAT_VERIFY_SSL"].lower() == "true"
        except:
            pass
        
        # Проверяем наличие сертификатов Sberbank
        if verify_ssl:
            cert_found = self._check_sberbank_certificates()
            if not cert_found:
                print("⚠️ SSL verification enabled but Sberbank certificates not found")
                verify_ssl = False
        
        return AIGigaChatConfig(
            client_id=client_id,
            client_secret=client_secret,
            scope=scope,
            base_url=base_url,
            auth_url=auth_url,
            model="GigaChat",
            temperature=0.7,
            max_tokens=2000,
            timeout=30,
            verify_ssl=verify_ssl
        )
    
    def _check_sberbank_certificates(self) -> bool:
        """Проверка наличия сертификатов Sberbank"""
        cert_paths = [
            '/etc/ssl/certs/sberbank.pem',
            '/usr/local/share/ca-certificates/sberbank.pem',
            './sberbank_cert.pem',
            './gigachat_cert.pem',
        ]
        
        for cert_path in cert_paths:
            if os.path.exists(cert_path):
                return True
        return False
    
    def _get_access_token(self) -> Optional[str]:
        """Получение access token с использованием Client Secret"""
        
        # Проверка наличия client_id и client_secret
        if not self.config.client_id or not self.config.client_secret:
            print("GigaChat: Client ID or Client Secret not configured")
            return None
        
        # Проверка наличия валидного токена
        if self.current_token and self.current_token.expires_at > datetime.now():
            return self.current_token.access_token
        
        try:
            # Подготовка данных для запроса токена
            auth_string = f"{self.config.client_id}:{self.config.client_secret}"
            auth_bytes = auth_string.encode('utf-8')
            auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
            
            headers = {
                "Authorization": f"Basic {auth_b64}",
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
                "RqUID": self._generate_rquid()
            }
            
            data = {
                "scope": self.config.scope
            }
            
            # Запрос токена
            response = self.session.post(
                self.config.auth_url,
                headers=headers,
                data=data,
                timeout=self.config.timeout
                # verify управляется настройкой сессии
            )
            
            if response.status_code == 200:
                token_data = response.json()
                
                access_token = token_data.get("access_token")
                expires_in = token_data.get("expires_in", 1800)
                token_type = token_data.get("token_type", "Bearer")
                
                expires_at = datetime.now() + timedelta(seconds=expires_in - 60)
                
                self.current_token = GigaChatToken(
                    access_token=access_token,
                    expires_at=expires_at,
                    token_type=token_type
                )
                
                print(f"✅ GigaChat: Token obtained successfully")
                return access_token
            else:
                print(f"❌ GigaChat: Failed to get token, status: {response.status_code}")
                print(f"Response: {response.text[:200]}")
                return None
                
        except Exception as e:
            print(f"❌ GigaChat: Error getting token: {str(e)}")
            return None
    
    def _generate_rquid(self) -> str:
        """Генерация уникального RqUID для запроса"""
        import uuid
        return str(uuid.uuid4())
    
    def analyze_company(self, request: AIAnalysisRequest) -> AIAnalysisResponse:
        """
        Основной метод анализа компании
        
        Args:
            request: Запрос на анализ
        
        Returns:
            Результат анализа
        """
        
        start_time = datetime.now()
        self.usage_stats["total_requests"] += 1
        
        try:
            # Получение данных компании
            company_data = self._get_company_data(request.company_id)
            if not company_data:
                return AIAnalysisResponse(
                    success=False,
                    analysis={},
                    error="Company data not found"
                )
            
            # Проверка доступности GigaChat
            if not self._is_gigachat_available():
                self.usage_stats["fallback_used"] += 1
                print("⚠️ GigaChat not available, using fallback analysis")
                return self._generate_fallback_analysis(request)
            
            # Подготовка контекста для AI
            analysis_context = self._prepare_analysis_context(
                company_data, request.analysis_type, request.context
            )
            
            # Генерация промпта
            prompt = self._generate_prompt(
                request.analysis_type, 
                analysis_context, 
                request.custom_query,
                request.language
            )
            
            # Вызов GigaChat API
            ai_response = self._call_gigachat_api(prompt)
            
            # Парсинг ответа
            analysis_result = self._parse_ai_response(
                ai_response, request.analysis_type
            )
            
            # Обогащение результата
            enriched_result = self._enrich_analysis_result(
                analysis_result, company_data, request.analysis_type
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Обновление статистики
            self.usage_stats["successful_requests"] += 1
            if "tokens" in ai_response:
                self.usage_stats["tokens_total"] += ai_response.get("tokens", 0)
            
            return AIAnalysisResponse(
                success=True,
                analysis=enriched_result,
                processing_time=processing_time,
                tokens_used=ai_response.get("tokens", 0)
            )
            
        except Exception as e:
            self.usage_stats["failed_requests"] += 1
            print(f"❌ Error in analyze_company: {str(e)}")
            # Fallback на локальный анализ в случае ошибки
            return self._generate_fallback_analysis(request, str(e))
    
    def _safe_json_serialize(self, obj: Any) -> Any:
        """Безопасная сериализация объектов в JSON-совместимый формат"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, (timedelta, date)):
            return str(obj)
        elif isinstance(obj, Enum):
            return obj.value
        elif isinstance(obj, dict):
            return {k: self._safe_json_serialize(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._safe_json_serialize(item) for item in obj]
        elif hasattr(obj, '__dict__'):
            # Для объектов
            return {k: self._safe_json_serialize(v) for k, v in obj.__dict__.items() 
                    if not k.startswith('_')}
        else:
            return obj

    def _is_gigachat_available(self) -> bool:
        """Проверка доступности GigaChat API"""
        
        # Проверяем наличие client_id и client_secret
        if not self.config.client_id or not self.config.client_secret:
            print("GigaChat: Client ID or Client Secret not configured")
            return False
        
        # Пытаемся получить токен
        token = self._get_access_token()
        if not token:
            print("GigaChat: Failed to obtain access token")
            return False
        
        # Дополнительная проверка доступности API (опциональная)
        # Для тестирования можем пропустить эту проверку
        demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
        if demo_mode:
            print("GigaChat: Demo mode enabled, skipping API check")
            return True
        
        try:
            # Проверка моделей
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            response = self.session.get(
                f"{self.config.base_url}/models",
                headers=headers,
                timeout=5
                # verify управляется настройкой сессии
            )
            
            if response.status_code == 200:
                print("✅ GigaChat: API is available")
                return True
            else:
                print(f"⚠️ GigaChat: API check failed, status: {response.status_code}")
                # Даже если проверка не удалась, токен есть - можем попробовать работать
                return True
                
        except Exception as e:
            print(f"⚠️ GigaChat: API availability check error: {str(e)[:100]}")
            # Все равно возвращаем True, так как токен получен
            return True
    
    def _get_company_data(self, company_id: int) -> Optional[Dict[str, Any]]:
        """Получение данных компании"""
        
        # Проверка кэша
        cache_key = f"company_{company_id}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        company = db_manager.get_company(company_id)
        if not company:
            return None
        
        # Получение финансовых данных
        actuals = db_manager.get_actual_financials_by_filters(
            {"company_id": company_id}
        )
        
        # Получение планов
        plans = db_manager.get_financial_plans(company_id)
        
        # Вместо несуществующего метода calculate_metrics, используем свои расчеты
        metrics = self._calculate_metrics_from_data(company, actuals)
        
        # Benchmark сравнение
        benchmark_comparison = None
        if metrics:
            try:
                benchmark_comparison = saas_benchmarks.compare_with_benchmarks(
                    metrics, company.stage
                )
            except:
                benchmark_comparison = None
        
        company_data = {
            "basic_info": self._company_to_dict(company),
            "actuals": [self._actual_to_dict(a) for a in actuals] if actuals else [],
            "plans": [self._plan_to_dict(p) for p in plans] if plans else [],
            "metrics": metrics or {},
            "benchmark_comparison": benchmark_comparison,
            "data_points_count": len(actuals) + len(plans)
        }
        
        # Сохранение в кэш
        self.cache[cache_key] = company_data
        
        return company_data
    
    def _company_to_dict(self, company) -> Dict[str, Any]:
        """Конвертация объекта компании в словарь"""
        if hasattr(company, 'to_dict'):
            return company.to_dict()
        else:
            return {
                "id": getattr(company, 'id', 0),
                "company_name": getattr(company, 'company_name', 'Unknown'),
                "stage": getattr(company, 'stage', 'pre_seed'),
                "current_mrr": getattr(company, 'current_mrr', 0),
                "cash_balance": getattr(company, 'cash_balance', 0)
            }
    
    def _actual_to_dict(self, actual) -> Dict[str, Any]:
        """Конвертация фактических данных в словарь"""
        if hasattr(actual, 'to_dict'):
            return actual.to_dict()
        else:
            return {
                "id": getattr(actual, 'id', 0),
                "company_id": getattr(actual, 'company_id', 0),
                "year": getattr(actual, 'year', 0),
                "month_number": getattr(actual, 'month_number', 0),
                "actual_mrr": getattr(actual, 'actual_mrr', 0),
                "actual_total_revenue": getattr(actual, 'actual_total_revenue', 0),
                "actual_total_costs": getattr(actual, 'actual_total_costs', 0),
                "actual_burn_rate": getattr(actual, 'actual_burn_rate', 0),
                "actual_cash_balance": getattr(actual, 'actual_cash_balance', 0),
                "actual_runway": getattr(actual, 'actual_runway', 0),
                "actual_new_customers": getattr(actual, 'actual_new_customers', 0),
                "actual_churned_customers": getattr(actual, 'actual_churned_customers', 0),
                "actual_marketing_spend": getattr(actual, 'actual_marketing_spend', 0)
            }
    
    def _plan_to_dict(self, plan) -> Dict[str, Any]:
        """Конвертация плана в словарь"""
        if hasattr(plan, 'to_dict'):
            return plan.to_dict()
        else:
            return {
                "id": getattr(plan, 'id', 0),
                "year": getattr(plan, 'year', 0),
                "month_number": getattr(plan, 'month_number', 0),
                "plan_mrr": getattr(plan, 'plan_mrr', 0),
                "plan_total_revenue": getattr(plan, 'plan_total_revenue', 0),
                "plan_total_costs": getattr(plan, 'plan_total_costs', 0)
            }
    
    def _calculate_metrics_from_data(self, company, actuals: List) -> Dict[str, Any]:
        """Расчет метрик из данных"""
        metrics = {}
        
        if not actuals:
            return metrics
        
        try:
            # Расчет основных метрик
            latest_actual = actuals[0]
            
            # MRR
            metrics["mrr"] = getattr(latest_actual, 'actual_mrr', 0)
            metrics["arr"] = metrics["mrr"] * 12
            
            # Burn rate
            metrics["burn_rate"] = getattr(latest_actual, 'actual_burn_rate', 0)
            
            # Runway
            cash_balance = getattr(latest_actual, 'actual_cash_balance', 0)
            if metrics["burn_rate"] > 0:
                metrics["runway_months"] = cash_balance / metrics["burn_rate"]
            else:
                metrics["runway_months"] = 0
            
            # Growth (если есть исторические данные)
            if len(actuals) > 1:
                previous_mrr = getattr(actuals[1], 'actual_mrr', 0)
                if previous_mrr > 0:
                    metrics["monthly_growth_rate"] = (metrics["mrr"] - previous_mrr) / previous_mrr
                else:
                    metrics["monthly_growth_rate"] = 0
            else:
                metrics["monthly_growth_rate"] = 0
            
            # Customer metrics
            new_customers = getattr(latest_actual, 'actual_new_customers', 0)
            churned_customers = getattr(latest_actual, 'actual_churned_customers', 0)
            total_customers = new_customers + max(0, 100 - churned_customers)  # Примерный расчет
            
            if total_customers > 0:
                metrics["monthly_churn_rate"] = churned_customers / total_customers
            else:
                metrics["monthly_churn_rate"] = 0
            
            # CAC
            marketing_spend = getattr(latest_actual, 'actual_marketing_spend', 0)
            if new_customers > 0:
                metrics["cac"] = marketing_spend / new_customers
            else:
                metrics["cac"] = 0
            
            # Примерные значения для остальных метрик
            metrics["gross_margin"] = 0.75  # Предположение
            metrics["ltv"] = metrics.get("cac", 0) * 3  # Предположение
            if metrics.get("cac", 0) > 0:
                metrics["ltv_cac_ratio"] = metrics["ltv"] / metrics["cac"]
            else:
                metrics["ltv_cac_ratio"] = 0
            
            # Magic number (упрощенный)
            if marketing_spend > 0:
                revenue_growth = metrics.get("monthly_growth_rate", 0) * metrics["mrr"]
                metrics["magic_number"] = revenue_growth / marketing_spend
            else:
                metrics["magic_number"] = 0
            
            # Net revenue retention (примерное)
            metrics["net_revenue_retention"] = 0.95  # Предположение
            
        except Exception as e:
            print(f"Error calculating metrics: {e}")
        
        return metrics
    
    def _prepare_analysis_context(self, company_data: Dict[str, Any],
                             analysis_type: AnalysisType,
                             user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Подготовка контекста для анализа"""
        
        context = {
            "company": company_data["basic_info"],
            "analysis_type": analysis_type.value,
            "current_date": datetime.now().isoformat(),  # Это уже строка
            "data_summary": {}
        }
        
        # Добавляем метрики
        if company_data["metrics"]:
            context["metrics"] = self._summarize_metrics(company_data["metrics"])
        
        # Добавляем исторические данные - УБЕДИТЕСЬ, что это сериализуемо
        if company_data["actuals"]:
            context["historical_data"] = self._summarize_actuals(company_data["actuals"])
        
        # Добавляем benchmark сравнение
        if company_data["benchmark_comparison"]:
            context["benchmark"] = company_data["benchmark_comparison"]
        
        # Добавляем пользовательский контекст - ПРОВЕРЬТЕ на datetime объекты
        # Преобразуем все datetime в строки
        sanitized_context = {}
        for key, value in user_context.items():
            if isinstance(value, datetime):
                sanitized_context[key] = value.isoformat()
            else:
                sanitized_context[key] = value
        context.update(sanitized_context)
        
        # Summary статистика
        context["data_summary"] = {
            "actuals_count": len(company_data["actuals"]),
            "plans_count": len(company_data["plans"]),
            "data_quality": self._assess_data_quality(company_data),
            "analysis_complexity": "detailed" if len(company_data["actuals"]) >= 6 else "basic"
        }
        
        return context
    
    def _summarize_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Суммаризация метрик для AI"""
        
        key_metrics = {}
        
        # Финансовые метрики
        financial_keys = ["mrr", "arr", "burn_rate", "runway_months", "gross_margin"]
        for key in financial_keys:
            if key in metrics:
                key_metrics[key] = metrics[key]
        
        # Эффективность
        efficiency_keys = ["ltv", "cac", "ltv_cac_ratio", "cac_payback_months", "magic_number"]
        for key in efficiency_keys:
            if key in metrics:
                key_metrics[key] = metrics[key]
        
        # Ростовые метрики
        growth_keys = ["monthly_growth_rate", "monthly_churn_rate", "net_revenue_retention"]
        for key in growth_keys:
            if key in metrics:
                key_metrics[key] = metrics[key]
        
        return key_metrics
    
    def _summarize_actuals(self, actuals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Суммаризация фактических данных"""
        
        if not actuals:
            return {}
        
        # Сортировка по дате
        sorted_actuals = sorted(
            actuals, 
            key=lambda x: (x.get("year", 0), x.get("month_number", 0))
        )
        
        # Расчет трендов
        if len(sorted_actuals) >= 2:
            first = sorted_actuals[0]
            last = sorted_actuals[-1]
            
            mrr_growth = None
            if first.get("actual_mrr", 0) > 0:
                mrr_growth = (last.get("actual_mrr", 0) - first.get("actual_mrr", 0)) / first.get("actual_mrr", 0)
            
            avg_burn_rate = sum(a.get("actual_burn_rate", 0) for a in sorted_actuals) / len(sorted_actuals)
            
            return {
                "periods_analyzed": len(sorted_actuals),
                "starting_mrr": first.get("actual_mrr", 0),
                "ending_mrr": last.get("actual_mrr", 0),
                "mrr_growth_rate": mrr_growth,
                "average_burn_rate": avg_burn_rate,
                "latest_runway": last.get("actual_runway", 0),
                "data_currency": "Fresh" if len(sorted_actuals) <= 3 else "Historical"
            }
        
        return {"periods_analyzed": len(sorted_actuals)}
    
    def _assess_data_quality(self, company_data: Dict[str, Any]) -> str:
        """Оценка качества данных"""
        
        actuals_count = len(company_data["actuals"])
        plans_count = len(company_data["plans"])
        
        if actuals_count >= 12 and plans_count >= 1:
            return "Excellent"
        elif actuals_count >= 6 and plans_count >= 1:
            return "Good"
        elif actuals_count >= 3:
            return "Fair"
        else:
            return "Limited"
    
    def _serialize_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Сериализация контекста для JSON"""
        import json
        
        def serialize(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, timedelta):
                return str(obj)
            elif hasattr(obj, '__dict__'):
                return {k: serialize(v) for k, v in obj.__dict__.items() if not k.startswith('_')}
            elif isinstance(obj, dict):
                return {k: serialize(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [serialize(item) for item in obj]
            else:
                return obj
        
        return serialize(context)

    def _generate_prompt(self, analysis_type: AnalysisType,
                        context: Dict[str, Any],
                        custom_query: Optional[str],
                        language: str) -> str:
        # Безопасная сериализация контекста
        safe_context = self._safe_json_serialize(context)

        # Добавление контекста
        try:
            context_str = json.dumps(safe_context, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Ошибка сериализации JSON: {e}")
            # Fallback: упрощенный контекст
            context_str = json.dumps({
                "company_name": context.get("company", {}).get("company_name", "Unknown"),
                "analysis_type": analysis_type.value,
                "metrics": safe_context.get("metrics", {}),
                "data_summary": safe_context.get("data_summary", {})
            }, indent=2, ensure_ascii=False)

        """Генерация промпта для GigaChat"""
        
        # Базовый промпт
        if language == "ru":
            base_prompt = """Ты - опытный финансовый аналитик SaaS бизнеса.
Твоя задача - проанализировать данные компании и предоставить полезные insights.
"""
        else:
            base_prompt = """You are an experienced SaaS financial analyst.
Your task is to analyze company data and provide useful insights.
"""
        
        # Добавление типа анализа
        analysis_prompts = {
            AnalysisType.FULL_BUSINESS_ANALYSIS: {
                "ru": "Проведи полный анализ бизнеса, включая финансовое здоровье, метрики роста, риски и рекомендации.",
                "en": "Conduct a full business analysis including financial health, growth metrics, risks and recommendations."
            },
            AnalysisType.FINANCIAL_HEALTH: {
                "ru": "Проанализируй финансовое здоровье компании. Оцени runway, burn rate, profitability и sustainability.",
                "en": "Analyze the company's financial health. Assess runway, burn rate, profitability and sustainability."
            },
            AnalysisType.GROWTH_RECOMMENDATIONS: {
                "ru": "Предоставь рекомендации по ускорению роста. Проанализируй текущие метрики роста и предложи стратегии улучшения.",
                "en": "Provide growth acceleration recommendations. Analyze current growth metrics and suggest improvement strategies."
            },
            AnalysisType.RISK_ANALYSIS: {
                "ru": "Проведи анализ рисков компании. Идентифицируй ключевые риски и предложи mitigation strategies.",
                "en": "Conduct company risk analysis. Identify key risks and suggest mitigation strategies."
            },
            AnalysisType.COMPETITIVE_ANALYSIS: {
                "ru": "Проанализируй конкурентную позицию компании. Сравни с benchmark и индустрии best practices.",
                "en": "Analyze the company's competitive position. Compare with benchmarks and industry best practices."
            },
            AnalysisType.FORECAST_12M: {
                "ru": "Создай 12-месячный прогноз на основе текущих данных. Включи ключевые метрики и assumptions.",
                "en": "Create a 12-month forecast based on current data. Include key metrics and assumptions."
            },
            AnalysisType.CUSTOM_QUERY: {
                "ru": "Ответь на пользовательский запрос на основе данных компании.",
                "en": "Answer the user's custom query based on company data."
            }
        }
        
        analysis_prompt = analysis_prompts.get(analysis_type, {"ru": "", "en": ""})[language]
        
        # Добавление custom query если есть
        custom_query_part = ""
        if custom_query:
            if language == "ru":
                custom_query_part = f"\nПользовательский запрос: {custom_query}"
            else:
                custom_query_part = f"\nUser query: {custom_query}"
        
        # Структура ответа
        if language == "ru":
            structure_prompt = """
Структурируй ответ в формате JSON со следующими разделами:
1. executive_summary: Краткое резюме анализа (1-2 абзаца)
2. key_findings: Список ключевых выводов
3. recommendations: Список рекомендаций с приоритетами (high/medium/low)
4. financial_insights: Инсайты по финансовым метрикам
5. risk_assessment: Оценка рисков
6. action_plan: План действий

Будь конкретным, data-driven и практичным в рекомендациях.
"""
        else:
            structure_prompt = """
Structure your response in JSON format with the following sections:
1. executive_summary: Brief analysis summary (1-2 paragraphs)
2. key_findings: List of key findings
3. recommendations: List of recommendations with priorities (high/medium/low)
4. financial_insights: Financial metric insights
5. risk_assessment: Risk assessment
6. action_plan: Action plan

Be specific, data-driven and practical in your recommendations.
"""
        
        # Сборка полного промпта
        full_prompt = f"""{base_prompt}

{analysis_prompt}

Контекст компании:
{context_str}

{custom_query_part}

{structure_prompt}

Ответ должен быть строго в формате JSON.
"""
        
        return full_prompt
    
    def _call_gigachat_api(self, prompt: str) -> Dict[str, Any]:
        """Вызов GigaChat API"""
        
        # Получение токена
        token = self._get_access_token()
        if not token:
            raise Exception("Failed to obtain GigaChat access token")
        
        try:
            # Подготовка запроса
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            payload = {
                "model": self.config.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens
            }
            
            # Отправка запроса через сессию с настройками SSL
            response = self.session.post(
                f"{self.config.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.config.timeout
                # verify управляется настройкой сессии
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Извлечение ответа
                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0]["message"]["content"]
                    
                    # Парсинг JSON из ответа
                    try:
                        parsed_response = json.loads(content)
                        parsed_response["tokens"] = result.get("usage", {}).get("total_tokens", 0)
                        return parsed_response
                    except json.JSONDecodeError:
                        # Если не JSON, пытаемся извлечь JSON из текста
                        return self._extract_json_from_text(content)
                else:
                    raise Exception("No choices in GigaChat response")
            else:
                error_msg = f"GigaChat API error: {response.status_code}"
                if response.text:
                    error_msg += f" - {response.text}"
                raise Exception(error_msg)
                
        except Exception as e:
            print(f"❌ GigaChat API call error: {str(e)}")
            raise
    
    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """Извлечение JSON из текстового ответа"""
        
        try:
            # Пытаемся найти JSON в тексте
            start_idx = text.find('{')
            end_idx = text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # Если не нашли JSON, создаем структурированный ответ из текста
                return {
                    "executive_summary": text[:500],
                    "key_findings": ["AI анализ завершен", "Смотрите executive summary"],
                    "recommendations": [{"priority": "medium", "recommendation": "Review the analysis"}],
                    "raw_response": text
                }
        except:
            # Fallback response
            return {
                "executive_summary": text[:500] if text else "AI analysis completed",
                "key_findings": ["Analysis completed successfully"],
                "recommendations": [],
                "raw_response": text
            }
    
    def _parse_ai_response(self, ai_response: Dict[str, Any], 
                          analysis_type: AnalysisType) -> Dict[str, Any]:
        """Парсинг ответа AI"""
        
        result = {
            "analysis_type": analysis_type.value,
            "generated_at": datetime.now().isoformat(),
            "ai_model": self.config.model
        }
        
        # Копируем все поля из AI ответа
        result.update(ai_response)
        
        # Добавляем метаданные
        if "tokens" not in result:
            result["tokens"] = 0
        
        return result
    
    def _enrich_analysis_result(self, analysis_result: Dict[str, Any],
                               company_data: Dict[str, Any],
                               analysis_type: AnalysisType) -> Dict[str, Any]:
        """Обогащение результата анализа"""
        
        # Добавление company context
        analysis_result["company_context"] = {
            "company_name": company_data["basic_info"].get("company_name", "Unknown"),
            "stage": company_data["basic_info"].get("stage", "unknown"),
            "current_mrr": company_data["basic_info"].get("current_mrr", 0),
            "data_points": company_data["data_points_count"]
        }
        
        # Добавление benchmark данных
        if company_data.get("benchmark_comparison"):
            analysis_result["benchmark_data"] = {
                "overall_score": company_data["benchmark_comparison"].get("overall_score", 0),
                "performance_level": company_data["benchmark_comparison"].get("overall_performance", "N/A")
            }
        
        # Добавление автоматически сгенерированных рекомендаций если их нет
        if "recommendations" not in analysis_result or not analysis_result["recommendations"]:
            analysis_result["recommendations"] = self._generate_basic_recommendations(
                company_data, analysis_type
            )
        
        # Добавление временных меток
        analysis_result["metadata"] = {
            "processing_time": datetime.now().isoformat(),
            "analysis_version": "1.0",
            "data_freshness": "current"
        }
        
        return analysis_result
    
    def _generate_basic_recommendations(self, company_data: Dict[str, Any],
                                       analysis_type: AnalysisType) -> List[Dict[str, Any]]:
        """Генерация базовых рекомендаций (fallback)"""
        
        recommendations = []
        
        # Общие рекомендации на основе данных
        if company_data["metrics"]:
            metrics = company_data["metrics"]
            
            # Рекомендации по финансовому здоровью
            runway = metrics.get("runway_months", 0)
            if runway < 6:
                recommendations.append({
                    "category": "Financial",
                    "priority": "high",
                    "recommendation": "Extend runway to at least 12 months",
                    "rationale": f"Current runway is only {runway:.1f} months",
                    "expected_impact": "Critical"
                })
            
            # Рекомендации по unit economics
            ltv_cac_ratio = metrics.get("ltv_cac_ratio", 0)
            if ltv_cac_ratio < 3:
                recommendations.append({
                    "category": "Unit Economics",
                    "priority": "medium",
                    "recommendation": "Improve LTV/CAC ratio to at least 3x",
                    "rationale": f"Current ratio is {ltv_cac_ratio:.1f}x",
                    "expected_impact": "High"
                })
            
            # Рекомендации по росту
            growth_rate = metrics.get("monthly_growth_rate", 0)
            if growth_rate < 0.1:
                recommendations.append({
                    "category": "Growth",
                    "priority": "medium",
                    "recommendation": "Accelerate monthly growth rate",
                    "rationale": f"Current growth is {growth_rate*100:.1f}%/month",
                    "expected_impact": "Medium"
                })
        
        # Специфические рекомендации по типу анализа
        if analysis_type == AnalysisType.FINANCIAL_HEALTH:
            recommendations.append({
                "category": "Financial Management",
                "priority": "high",
                "recommendation": "Implement monthly financial review process",
                "rationale": "Regular monitoring improves financial discipline",
                "expected_impact": "High"
            })
        
        elif analysis_type == AnalysisType.GROWTH_RECOMMENDATIONS:
            recommendations.append({
                "category": "Growth Strategy",
                "priority": "medium",
                "recommendation": "Diversify customer acquisition channels",
                "rationale": "Reduces dependency on single channel",
                "expected_impact": "Medium"
            })
        
        # Добавление общих рекомендаций
        if len(recommendations) < 3:
            recommendations.extend([
                {
                    "category": "Data Management",
                    "priority": "low",
                    "recommendation": "Improve data collection and tracking",
                    "rationale": "Better data enables better decisions",
                    "expected_impact": "Medium"
                },
                {
                    "category": "Team",
                    "priority": "medium",
                    "recommendation": "Regular team performance reviews",
                    "rationale": "Aligns team with business objectives",
                    "expected_impact": "High"
                }
            ])
        
        return recommendations
    
    def _generate_fallback_analysis(self, request: AIAnalysisRequest,
                                   error: Optional[str] = None) -> AIAnalysisResponse:
        """Генерация fallback анализа при недоступности GigaChat"""
        
        print(f"GigaChat: Using fallback analysis. Error: {error}")
        
        # Получение данных компании
        company_data = self._get_company_data(request.company_id)
        if not company_data:
            return AIAnalysisResponse(
                success=False,
                analysis={},
                error="Company data not found"
            )
        
        # Генерация локального анализа
        local_analysis = self._generate_local_analysis(
            company_data, request.analysis_type, request.custom_query
        )
        
        return AIAnalysisResponse(
            success=True,
            analysis=local_analysis,
            error="GigaChat недоступен. Использован локальный анализ." if not error else error
        )
    
    def _generate_local_analysis(self, company_data: Dict[str, Any],
                                analysis_type: AnalysisType,
                                custom_query: Optional[str]) -> Dict[str, Any]:
        """Генерация локального анализа"""
        
        # Базовый анализ на основе данных
        analysis = {
            "analysis_type": analysis_type.value,
            "generated_at": datetime.now().isoformat(),
            "ai_model": "Local Algorithm",
            "executive_summary": self._generate_executive_summary(company_data, analysis_type),
            "key_findings": self._generate_key_findings(company_data),
            "recommendations": self._generate_basic_recommendations(company_data, analysis_type),
            "financial_insights": self._generate_financial_insights(company_data),
            "risk_assessment": self._generate_risk_assessment(company_data),
            "action_plan": self._generate_action_plan(company_data),
            "company_context": {
                "company_name": company_data["basic_info"].get("company_name", "Unknown"),
                "stage": company_data["basic_info"].get("stage", "unknown"),
                "current_mrr": company_data["basic_info"].get("current_mrr", 0)
            },
            "metadata": {
                "processing_time": datetime.now().isoformat(),
                "analysis_version": "1.0",
                "data_freshness": "current",
                "is_fallback": True
            }
        }
        
        # Добавление ответа на custom query если есть
        if custom_query:
            analysis["custom_query_response"] = self._respond_to_custom_query(
                custom_query, company_data
            )
        
        return analysis
    
    def _generate_executive_summary(self, company_data: Dict[str, Any],
                                   analysis_type: AnalysisType) -> str:
        """Генерация executive summary"""
        
        company = company_data["basic_info"]
        metrics = company_data["metrics"]
        
        summary = f"Анализ компании {company.get('company_name', 'Unknown')} ({company.get('stage', 'unknown')} stage). "
        
        if metrics:
            mrr = metrics.get("mrr", 0)
            runway = metrics.get("runway_months", 0)
            growth = metrics.get("monthly_growth_rate", 0) * 100
            
            summary += f"Текущий MRR: ${mrr:,.0f}, Runway: {runway:.1f} месяцев, Рост: {growth:.1f}%/мес. "
            
            if runway < 6:
                summary += "Требуется внимание к финансовому здоровью. "
            elif growth < 10:
                summary += "Рост ниже оптимального уровня для SaaS. "
            else:
                summary += "Компания демонстрирует стабильные показатели. "
        
        summary += "Рекомендуется регулярный мониторинг ключевых метрик и адаптация стратегии по мере роста бизнеса."
        
        return summary
    
    def _generate_key_findings(self, company_data: Dict[str, Any]) -> List[str]:
        """Генерация ключевых выводов"""
        
        findings = []
        metrics = company_data["metrics"]
        
        if metrics:
            # Финансовые выводы
            runway = metrics.get("runway_months", 0)
            if runway < 6:
                findings.append(f"Критически низкий runway: {runway:.1f} месяцев")
            elif runway < 12:
                findings.append(f"Runway требует внимания: {runway:.1f} месяцев")
            
            # Ростовые выводы
            growth = metrics.get("monthly_growth_rate", 0) * 100
            if growth < 5:
                findings.append(f"Низкий рост: {growth:.1f}%/месяц")
            elif growth > 20:
                findings.append(f"Высокий рост: {growth:.1f}%/месяц")
            
            # Unit economics выводы
            ltv_cac = metrics.get("ltv_cac_ratio", 0)
            if ltv_cac < 3:
                findings.append(f"LTV/CAC ratio ниже оптимального: {ltv_cac:.1f}x")
        
        # Данные выводы
        if company_data["data_points_count"] < 3:
            findings.append("Ограниченное количество данных для анализа")
        
        if len(findings) == 0:
            findings = [
                "Стабильные финансовые показатели",
                "Адекватный уровень данных для анализа",
                "Рекомендуется углубленный анализ при наличии больше данных"
            ]
        
        return findings
    
    def _generate_financial_insights(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Генерация финансовых инсайтов"""
        
        insights = {}
        metrics = company_data["metrics"]
        
        if metrics:
            insights = {
                "current_mrr": metrics.get("mrr", 0),
                "annual_run_rate": metrics.get("arr", 0),
                "burn_rate": metrics.get("burn_rate", 0),
                "runway_months": metrics.get("runway_months", 0),
                "gross_margin": metrics.get("gross_margin", 0) * 100,
                "ltv_cac_ratio": metrics.get("ltv_cac_ratio", 0),
                "monthly_growth": metrics.get("monthly_growth_rate", 0) * 100
            }
        
        return insights
    
    def _generate_risk_assessment(self, company_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Генерация оценки рисков"""
        
        risks = []
        metrics = company_data["metrics"]
        
        if metrics:
            runway = metrics.get("runway_months", 0)
            if runway < 3:
                risks.append({
                    "risk": "Cash runway exhaustion",
                    "severity": "critical",
                    "description": f"Only {runway:.1f} months of cash remaining",
                    "mitigation": "Immediate fundraising or cost reduction"
                })
            elif runway < 6:
                risks.append({
                    "risk": "Short cash runway",
                    "severity": "high",
                    "description": f"{runway:.1f} months runway may be insufficient",
                    "mitigation": "Start fundraising preparation"
                })
            
            growth = metrics.get("monthly_growth_rate", 0)
            if growth < 0.05:
                risks.append({
                    "risk": "Stagnant growth",
                    "severity": "medium",
                    "description": f"Growth rate of {growth*100:.1f}% is below SaaS benchmarks",
                    "mitigation": "Review and adjust growth strategy"
                })
        
        # Общие риски
        risks.extend([
            {
                "risk": "Market competition",
                "severity": "medium",
                "description": "Increasing competition in SaaS market",
                "mitigation": "Differentiate product and improve value proposition"
            },
            {
                "risk": "Team scaling",
                "severity": "low",
                "description": "Challenges in scaling team with growth",
                "mitigation": "Implement structured hiring and onboarding"
            }
        ])
        
        return risks
    
    def _generate_action_plan(self, company_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Генерация плана действий"""
        
        actions = [
            {
                "action": "Monthly financial review",
                "timeline": "Next 30 days",
                "owner": "CEO/CFO",
                "priority": "high"
            },
            {
                "action": "Update 12-month financial plan",
                "timeline": "Next 60 days",
                "owner": "Finance team",
                "priority": "medium"
            },
            {
                "action": "Review key metric targets",
                "timeline": "Next 90 days",
                "owner": "Leadership team",
                "priority": "medium"
            }
        ]
        
        # Добавление специфических действий на основе данных
        metrics = company_data["metrics"]
        if metrics and metrics.get("runway_months", 0) < 6:
            actions.insert(0, {
                "action": "Fundraising preparation",
                "timeline": "Immediate",
                "owner": "CEO",
                "priority": "critical"
            })
        
        return actions
    
    def _respond_to_custom_query(self, query: str, company_data: Dict[str, Any]) -> str:
        """Ответ на пользовательский запрос"""
        
        # Простая логика ответа на основе ключевых слов
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["рост", "growth", "увеличить"]):
            return "Для ускорения роста рекомендую: 1) Оптимизировать каналы привлечения клиентов, 2) Улучшить retention, 3) Рассмотреть upselling возможности."
        
        elif any(word in query_lower for word in ["затраты", "costs", "экономить"]):
            return "Для оптимизации затрат: 1) Аудит текущих расходов, 2) Приоритизация инвестиций, 3) Переговоры с поставщиками, 4) Автоматизация процессов."
        
        elif any(word in query_lower for word in ["инвестор", "funding", "раунд"]):
            return "Для подготовки к раунду финансирования: 1) Улучшить unit economics, 2) Подготовить финансовую модель, 3) Собрать успешные case studies, 4) Подготовить pitch deck."
        
        else:
            return f"На основе анализа данных компании {company_data['basic_info'].get('company_name', '')} рекомендую сосредоточиться на ключевых метриках: MRR growth, LTV/CAC ratio, и runway. Регулярный мониторинг и корректировка стратегии помогут достичь целей."
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Получение статистики использования"""
        return self.usage_stats
    
    def clear_cache(self) -> None:
        """Очистка кэша"""
        self.cache.clear()
        self.current_token = None

# Глобальный экземпляр аналитика
gigachat_analyst = GigaChatAnalyst()

# Публичные функции для использования в приложении
def analyze_with_gigachat(company_id: int,
                         context: Dict[str, Any],
                         analysis_type: str = "full_business_analysis",
                         custom_query: Optional[str] = None,
                         language: str = "ru") -> Dict[str, Any]:
    """
    Публичная функция для анализа с GigaChat
    
    Args:
        company_id: ID компании
        context: Контекст анализа
        analysis_type: Тип анализа
        custom_query: Пользовательский запрос
        language: Язык анализа
    
    Returns:
        Результат анализа
    """
    
    try:
        analysis_type_enum = AnalysisType(analysis_type)
    except ValueError:
        analysis_type_enum = AnalysisType.FULL_BUSINESS_ANALYSIS
    
    request = AIAnalysisRequest(
        company_id=company_id,
        analysis_type=analysis_type_enum,
        context=context,
        custom_query=custom_query,
        language=language
    )
    
    response = gigachat_analyst.analyze_company(request)
    
    return {
        "success": response.success,
        "analysis": response.analysis,
        "error": response.error,
        "processing_time": response.processing_time
    }

def get_gigachat_health_check() -> Dict[str, Any]:
    """
    Проверка здоровья GigaChat подключения
    
    Returns:
        Статус подключения
    """
    
    # Упрощенная проверка - просто проверяем, можем ли получить токен
    token = gigachat_analyst._get_access_token()
    stats = gigachat_analyst.get_usage_stats()
    
    return {
        "status": "connected" if token else "disconnected",
        "token_available": bool(token),
        "usage_stats": stats,
        "config_available": bool(gigachat_analyst.config.client_id and gigachat_analyst.config.client_secret),
        "ssl_verification": gigachat_analyst.config.verify_ssl,
        "timestamp": datetime.now().isoformat()
    }

def clear_gigachat_cache() -> Dict[str, Any]:
    """
    Очистка кэша GigaChat аналитика
    
    Returns:
        Статус операции
    """
    
    gigachat_analyst.clear_cache()
    
    return {
        "success": True,
        "message": "GigaChat cache cleared",
        "timestamp": datetime.now().isoformat()
    }

# Демо-функция для тестирования
def test_gigachat_connection() -> Dict[str, Any]:
    """Тестирование подключения к GigaChat"""
    
    print("Testing GigaChat connection...")
    
    # Проверка конфигурации
    config = gigachat_analyst.config
    config_status = {
        "client_id_configured": bool(config.client_id),
        "client_secret_configured": bool(config.client_secret),
        "base_url": config.base_url,
        "auth_url": config.auth_url,
        "verify_ssl": config.verify_ssl
    }
    
    # Проверка токена
    token = gigachat_analyst._get_access_token()
    token_status = {
        "has_token": bool(token),
        "token_valid": False
    }
    
    if token and gigachat_analyst.current_token:
        token_status["token_valid"] = gigachat_analyst.current_token.expires_at > datetime.now()
        token_status["expires_at"] = gigachat_analyst.current_token.expires_at.isoformat()
    
    # Простой тестовый запрос
    test_result = {
        "config": config_status,
        "token": token_status,
        "overall_status": "unknown"
    }
    
    if token_status["has_token"] and token_status["token_valid"]:
        test_result["overall_status"] = "connected"
        print("✅ GigaChat: Connection test - CONNECTED")
    elif config_status["client_id_configured"] and config_status["client_secret_configured"]:
        test_result["overall_status"] = "config_ok_but_no_token"
        print("⚠️ GigaChat: Connection test - CONFIG OK BUT NO TOKEN")
    else:
        test_result["overall_status"] = "not_configured"
        print("❌ GigaChat: Connection test - NOT CONFIGURED")
    
    return test_result
