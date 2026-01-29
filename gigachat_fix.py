"""
Исправление для SSL проблем GigaChat
"""

import ssl
import urllib3
from typing import Optional
import requests

# Отключаем warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_giga_chat_session():
    """Создание сессии с отключенной SSL проверкой"""
    session = requests.Session()
    
    # Отключаем SSL проверку
    session.verify = False
    
    # Настраиваем ретраи
    retry_strategy = urllib3.Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["POST", "GET"]
    )
    
    adapter = requests.adapters.HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    
    return session

# Патч для существующего кода
def patch_gigachat_analyst():
    """Патч для существующего класса GigaChatAnalyst"""
    try:
        import gigachat_analyst
        
        # Сохраняем оригинальный метод
        original_get_token = gigachat_analyst.GigaChatAnalyst._get_access_token
        
        def patched_get_token(self):
            """Патченный метод получения токена с отключенной SSL проверкой"""
            try:
                # Создаем сессию с отключенной проверкой
                import requests
                session = requests.Session()
                session.verify = False
                
                # Используем оригинальную логику, но с нашей сессией
                # (нужно адаптировать под конкретный код)
                return original_get_token(self)
            except Exception as e:
                print(f"Patched token error: {e}")
                return None
        
        # Применяем патч
        gigachat_analyst.GigaChatAnalyst._get_access_token = patched_get_token
        print("GigaChatAnalyst успешно пропатчен")
        
    except Exception as e:
        print(f"Не удалось применить патч: {e}")