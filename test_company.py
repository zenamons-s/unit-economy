import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import db_manager, Company

print("=== ТЕСТ СОЗДАНИЯ КОМПАНИИ ===")

# Инициализация БД
db_manager.initialize_database()
print("✅ База данных инициализирована")

# Проверяем текущие компании
print("\n📊 Текущие компании в БД:")
companies = db_manager.get_all_companies()
print(f"Количество компаний: {len(companies)}")
for comp in companies:
    print(f"  - {comp.name} (ID: {comp.id})")

# Создаем тестовую компанию
print("\n➕ Создаем тестовую компанию...")
test_company = Company(
    name="Комета",
    stage="pre_seed",
    current_mrr=15000.0,
    current_customers=120,
    monthly_price=125.0,
    team_size=8,
    cash_balance=600000.0,
    industry="SaaS",
    description="Тестовая компания для отладки"
)

try:
    company_id = db_manager.create_company(test_company)
    print(f"✅ Компания создана! ID: {company_id}")
    
    # Проверяем создание
    created_company = db_manager.get_company(company_id)
    if created_company:
        print(f"✅ Компания найдена: {created_company.name}")
        print(f"   Детали: MRR=${created_company.current_mrr}, Клиентов={created_company.current_customers}")
    else:
        print("❌ Компания не найдена!")
    
    # Снова проверяем все компании
    print("\n📊 Компании после создания:")
    companies = db_manager.get_all_companies()
    print(f"Количество компаний: {len(companies)}")
    for comp in companies:
        print(f"  - {comp.name} (ID: {comp.id}, Stage: {comp.stage})")
        
except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()