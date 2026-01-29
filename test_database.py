import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import db_manager, Company

def test_company_creation():
    print("Тестирование создания компании...")
    
    # Инициализируем БД
    db_manager.initialize_database()
    
    # Создаем тестовую компанию
    company = Company(
        name="Test Company",
        stage="seed",
        current_mrr=50000.0,
        current_customers=500,
        monthly_price=100.0,
        team_size=25,
        cash_balance=1000000.0,
        industry="SaaS",
        description="Тестовая компания"
    )
    
    # Сохраняем
    company_id = db_manager.create_company(company)
    print(f"Создана компания с ID: {company_id}")
    
    # Проверяем
    retrieved = db_manager.get_company(company_id)
    if retrieved:
        print(f"Компания найдена: {retrieved.name}")
    else:
        print("Ошибка: компания не найдена")
    
    # Показываем все компании
    all_companies = db_manager.get_all_companies()
    print(f"\nВсего компаний в БД: {len(all_companies)}")
    for comp in all_companies:
        print(f"- {comp.name} (ID: {comp.id})")

if __name__ == "__main__":
    test_company_creation()