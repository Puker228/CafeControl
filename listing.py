# описание таблиц бд
class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(primary_key=True)


class Customer(Base):
    __tablename__ = "customers"

    name: Mapped[str]
    phone: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    loyalty_level: Mapped[str] = mapped_column(default="Bronze")
    discount_percent: Mapped[float] = mapped_column(default=0.0)

    orders: Mapped[list["Order"]] = relationship(
        back_populates="customer", cascade="all, delete"
    )


class Employee(Base):
    __tablename__ = "employees"
    fio: Mapped[str]
    role: Mapped[str]
    phone: Mapped[str]
    hire_date: Mapped[datetime] = mapped_column(default=datetime.now)
    salary: Mapped[float] = mapped_column(Numeric(10, 2))

    orders: Mapped[list["Order"]] = relationship(back_populates="employee")

#########################

# описание триггеров
trigger_dml_2_func = """
CREATE OR REPLACE FUNCTION notify_customer_update()
RETURNS TRIGGER AS $$
BEGIN
    RAISE NOTICE 'Данные клиента обновлены: ID %', NEW.name;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

trigger_dml_2 = """
DROP TRIGGER IF EXISTS trg_notify_customer_update ON customers;
CREATE TRIGGER trg_notify_customer_update
AFTER UPDATE ON customers
FOR EACH ROW EXECUTE FUNCTION notify_customer_update();
"""

# 3. DML Trigger: Логирование удаления блюда из меню
trigger_dml_3_func = """
CREATE OR REPLACE FUNCTION notify_menu_item_deletion()
RETURNS TRIGGER AS $$
BEGIN
    RAISE NOTICE 'Блюдо удалено из меню: ID %, Название: %', OLD.id, OLD.name;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;
"""

trigger_dml_3 = """
DROP TRIGGER IF EXISTS trg_notify_menu_item_deletion ON menu_items;
CREATE TRIGGER trg_notify_menu_item_deletion
AFTER DELETE ON menu_items
FOR EACH ROW EXECUTE FUNCTION notify_menu_item_deletion();
"""

# подключение триггеров
with engine.connect() as conn:
    print("Creating triggers...")
    conn.execute(text(trigger_dml_1_func))
    conn.execute(text(trigger_dml_1))
    conn.execute(text(trigger_dml_2_func))
    conn.execute(text(trigger_dml_2))
    conn.execute(text(trigger_dml_3_func))
    conn.execute(text(trigger_dml_3))
    conn.execute(text(trigger_ddl_func))
    conn.commit()
    print("Triggers created.")

#########################

# "помощники" в интерфейсе
def reload_tree(tree, rows):
    tree.delete(*tree.get_children())
    for r in rows:
        tree.insert("", "end", values=[str(v) if v is not None else "" for v in r])


def delete_selected(tree, model, reload_func):
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Внимание", "Выберите запись")
        return

    if not messagebox.askyesno("Подтверждение", "Удалить выбранную запись?"):
        return

    item = tree.item(selected[0])
    record_id = int(item["values"][0])

    s = Session()
    obj = s.get(model, record_id)
    if obj:
        s.delete(obj)
        s.commit()
    s.close()

    reload_func()


#########################

# загрузчики данных для таблиц в интерфейсе
def load_customers():
    s = Session()
    rows = s.query(
        Customer.id,
        Customer.name,
        Customer.phone,
        Customer.email,
        Customer.loyalty_level,
        Customer.discount_percent,
    ).all()
    s.close()
    reload_tree(customers_tree, rows)


def load_suppliers():
    s = Session()
    rows = s.query(
        Supplier.id, Supplier.name, Supplier.phone, Supplier.email, Supplier.address
    ).all()
    s.close()
    reload_tree(suppliers_tree, rows)


#########################

# формы для добавления/редактирования данных
def report_all_orders():
    s = Session()

    rows = (
        s.query(
            Order.id,
            Customer.name,
            MenuItem.name,
            OrderComposition.quantity,
            OrderComposition.price_at_sale,
            (OrderComposition.quantity * OrderComposition.price_at_sale).label("total"),
        )
        .outerjoin(Customer, Order.customer_id == Customer.id)
        .join(OrderComposition, OrderComposition.order_id == Order.id)
        .join(MenuItem, OrderComposition.menu_item_id == MenuItem.id)
        .all()
    )

    s.close()
    return rows

#########################

# формирование отчета
def export_report():
    s = Session()
    wb = Workbook()

    def bold(ws):
        for c in ws[1]:
            c.font = Font(bold=True)

    ws = wb.active
    ws.title = "Продажи по дням"
    ws.append(["Дата", "Заказов", "Позиций", "Выручка"])

    rows = s.execute(
        text("""
        SELECT
            DATE(o.order_date) AS day,
            COUNT(DISTINCT o.id) AS orders,
            SUM(oc.quantity) AS items,
            SUM(oc.quantity * oc.price_at_sale) AS revenue
        FROM orders o
        JOIN order_compositions oc ON oc.order_id = o.id
        GROUP BY day
        ORDER BY day
    """)
    ).all()

    for r in rows:
        ws.append(tuple(r))

    bold(ws)


#########################

# отрисовка интерфейса
root = tk.Tk()
root.title("Cafe Control")
root.geometry("1280x720")

nb = ttk.Notebook(root)
nb.pack(fill="both", expand=True)
tk.Button(
    root,
    text="Выгрузить отчеты в Excel",
    font=("Arial", 12, "bold"),
    command=export_report,
).pack(fill="x", padx=10, pady=5)

# Customers
fc = ttk.Frame(nb)
nb.add(fc, text="Customers")
customers_tree = create_table(
    fc,
    ("id", "name", "phone", "email", "loyalty", "discount"),
    ("ID", "Имя", "Телефон", "Email", "Уровень", "Скидка (%)"),
)
tk.Button(fc, text="Добавить", command=create_customer).pack(side="left")
tk.Button(fc, text="Редактировать", command=lambda: edit_customer(customers_tree)).pack(
    side="left"
)
tk.Button(
    fc,
    text="Удалить",
    command=lambda: delete_selected(customers_tree, Customer, load_customers),
).pack(side="left")
load_customers()