import random
from datetime import datetime, timedelta
from faker import Faker
from sqlalchemy.orm import Session

# Импортируем модели и сессию из твоего кода
from main import (
    engine, Session as SessionLocal,
    Customer, Employee, Supplier, Ingredient, MenuItem, Order, OrderComposition
)

fake = Faker('ru_RU')
Faker.seed(42)
random.seed(42)

s = SessionLocal()

# ===================== CUSTOMERS =====================
def get_fake_ru_phone():
    # Генерируем что-то вроде +7 (999) 123-45-67 или 89991234567
    fmt = random.choice([
        "+7 (9{0}{1}) {2}{3}{4}-{5}{6}-{7}{8}",
        "89{0}{1}{2}{3}{4}{5}{6}{7}{8}",
        "79{0}{1}{2}{3}{4}{5}{6}{7}{8}",
        "+79{0}{1}{2}{3}{4}{5}{6}{7}{8}"
    ])
    digits = [random.randint(0, 9) for _ in range(9)]
    return fmt.format(*digits)

for _ in range(20):
    customer = Customer(
        name=fake.name(),
        phone=get_fake_ru_phone(),
        email=fake.unique.email(),
        loyalty_level=random.choice(["Bronze", "Silver", "Gold"]),
        discount_percent=random.choice([0.0, 5.0, 10.0])
    )
    s.add(customer)

# ===================== EMPLOYEES =====================
roles = ["Бармен", "Официант", "Администратор", "Повар"]
for _ in range(20):
    employee = Employee(
        fio=fake.name(),
        role=random.choice(roles),
        phone=get_fake_ru_phone(),
        hire_date=fake.date_between(start_date='-2y', end_date='today'),
        salary=round(random.uniform(30000, 80000), 2)
    )
    s.add(employee)

# ===================== SUPPLIERS =====================
for _ in range(20):
    supplier = Supplier(
        name=fake.company(),
        phone=get_fake_ru_phone(),
        email=fake.unique.company_email(),
        address=fake.address()
    )
    s.add(supplier)

s.commit()  # Сохраняем клиентов, сотрудников, поставщиков, чтобы получить их id

# ===================== INGREDIENTS =====================
suppliers = s.query(Supplier).all()
units = ["кг", "л", "шт"]
for _ in range(20):
    ingredient = Ingredient(
        name=fake.word().capitalize(),
        unit=random.choice(units),
        stock_quantity=round(random.uniform(5, 100), 2),
        min_stock_level=round(random.uniform(1, 10), 2),
        purchase_price=round(random.uniform(50, 500), 2),
        supplier_id=random.choice(suppliers).id
    )
    s.add(ingredient)

# ===================== MENU ITEMS =====================
types = ["Еда", "Напиток", "Алкоголь"]
for _ in range(20):
    item = MenuItem(
        name=fake.word().capitalize(),
        type=random.choice(types),
        selling_price=round(random.uniform(100, 1000), 2),
        volume_or_weight=f"{random.randint(100, 500)} г"
    )
    s.add(item)

s.commit()  # Сохраняем ингредиенты и меню

# ===================== ORDERS =====================
customers = s.query(Customer).all()
employees = s.query(Employee).all()
menu_items = s.query(MenuItem).all()

for _ in range(20):
    customer = random.choice(customers + [None])  # иногда "в зале"
    employee = random.choice(employees)
    order = Order(
        customer_id=customer.id if customer else None,
        employee_id=employee.id,
        order_type=random.choice(["В зале", "С собой"]),
        payment_method=random.choice(["Карта", "Наличные"]),
        status=random.choice(["Новый", "Готов", "Оплачен"]),
        order_date=fake.date_time_between(start_date='-90d', end_date='now')
    )
    s.add(order)
    s.flush()  # чтобы получить order.id

    # Добавим 1-5 позиций в заказ
    for _ in range(random.randint(1, 5)):
        item = random.choice(menu_items)
        qty = random.randint(1, 3)
        s.add(OrderComposition(
            order_id=order.id,
            menu_item_id=item.id,
            quantity=qty,
            price_at_sale=item.selling_price
        ))

s.commit()
s.close()
print("Заполнение базы данных завершено!")
