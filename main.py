import tkinter as tk
import uuid
from datetime import datetime, timedelta
from tkinter import messagebox, ttk
from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, create_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    sessionmaker,
)

# ===================== DATABASE =====================


class Base(DeclarativeBase):
    id: Mapped[UUID] = mapped_column(default=uuid.uuid4, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now)
    deleted_at: Mapped[datetime] = mapped_column(nullable=True)


class Customer(Base):
    __tablename__ = "customers"
    name: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)


class Position(Base):
    __tablename__ = "positions"
    name: Mapped[str] = mapped_column(unique=True)
    salary: Mapped[float]


class Shift(Base):
    __tablename__ = "shifts"

    employee_id: Mapped[UUID] = mapped_column(ForeignKey("employees.id"))
    employee: Mapped["Employee"] = relationship()

    start_time: Mapped[datetime]
    end_time: Mapped[Optional[datetime]]

    def worked_hours(self) -> float:
        if not self.end_time:
            return 0.0
        delta: timedelta = self.end_time - self.start_time
        return round(delta.total_seconds() / 3600, 2)

    def earned_money(self) -> float:
        if not self.end_time or not self.employee or not self.employee.position:
            return 0.0
        return round(self.worked_hours() * self.employee.position.salary, 2)


class Employee(Base):
    __tablename__ = "employees"
    first_name: Mapped[str]
    last_name: Mapped[str]
    email: Mapped[str] = mapped_column(nullable=True)

    position_id: Mapped[UUID] = mapped_column(ForeignKey("positions.id"))
    position: Mapped["Position"] = relationship()


class ItemCategory(Base):
    __tablename__ = "item_categories"
    name: Mapped[str] = mapped_column(unique=True)


class MenuItem(Base):
    __tablename__ = "menu_items"
    name: Mapped[str] = mapped_column(unique=True)
    price: Mapped[float]

    category_id: Mapped[UUID] = mapped_column(ForeignKey("item_categories.id"))
    category: Mapped["ItemCategory"] = relationship()


engine = create_engine("sqlite:///app.db", echo=False)
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

# ===================== HELPERS =====================


def create_table(parent, columns, headers):
    tree = ttk.Treeview(parent, columns=columns, show="headings")
    for c, h in zip(columns, headers):
        tree.heading(c, text=h)
        tree.column(c, width=150)
    tree.pack(fill="both", expand=True)
    return tree


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
    record_id = UUID(item["values"][0])

    s = Session()
    obj = s.get(model, record_id)
    if obj:
        s.delete(obj)
        s.commit()
    s.close()

    reload_func()


# ===================== LOADERS =====================


def load_customers():
    s = Session()
    rows = s.query(Customer.id, Customer.name, Customer.email).all()
    s.close()
    reload_tree(customers_tree, rows)


def load_shifts():
    s = Session()
    shifts = s.query(Shift).join(Employee).join(Position).all()

    rows = []
    for sh in shifts:
        rows.append(
            (
                sh.id,
                f"{sh.employee.first_name} {sh.employee.last_name}",
                sh.start_time.strftime("%Y-%m-%d %H:%M"),
                sh.end_time.strftime("%Y-%m-%d %H:%M") if sh.end_time else "",
                sh.worked_hours(),
                sh.earned_money(),
            )
        )

    s.close()
    reload_tree(shifts_tree, rows)


def load_positions():
    s = Session()
    rows = s.query(Position.id, Position.name, Position.salary).all()
    s.close()
    reload_tree(positions_tree, rows)


def load_employees():
    s = Session()
    rows = (
        s.query(Employee.id, Employee.first_name, Employee.last_name, Position.name)
        .outerjoin(Position)
        .all()
    )
    s.close()
    reload_tree(employees_tree, rows)


def load_categories():
    s = Session()
    rows = s.query(ItemCategory.id, ItemCategory.name).all()
    s.close()
    reload_tree(categories_tree, rows)


def load_menu():
    s = Session()
    rows = (
        s.query(MenuItem.id, MenuItem.name, MenuItem.price, ItemCategory.name)
        .outerjoin(ItemCategory)
        .all()
    )
    s.close()
    reload_tree(menu_tree, rows)


# ===================== CREATE FORMS =====================


def create_position():
    win = tk.Toplevel(root)
    win.title("Новая должность")

    tk.Label(win, text="Название").grid(row=0, column=0)
    tk.Label(win, text="Зарплата").grid(row=1, column=0)

    e_name = tk.Entry(win)
    e_salary = tk.Entry(win)
    e_name.grid(row=0, column=1)
    e_salary.grid(row=1, column=1)

    def save():
        if not e_name.get() or not e_salary.get():
            messagebox.showerror("Ошибка", "Заполните все поля")
            return
        s = Session()
        s.add(Position(name=e_name.get(), salary=float(e_salary.get())))
        s.commit()
        s.close()
        load_positions()
        win.destroy()

    tk.Button(win, text="Сохранить", command=save).grid(columnspan=2)


def create_shift():
    win = tk.Toplevel(root)
    win.title("Новая смена")

    tk.Label(win, text="Сотрудник").grid(row=0, column=0)
    tk.Label(win, text="Начало (YYYY-MM-DD HH:MM)").grid(row=1, column=0)
    tk.Label(win, text="Конец (опц.)").grid(row=2, column=0)

    emp_var = tk.StringVar()
    emp_box = ttk.Combobox(win, textvariable=emp_var, state="readonly")
    emp_box.grid(row=0, column=1)

    e_start = tk.Entry(win)
    e_end = tk.Entry(win)
    e_start.grid(row=1, column=1)
    e_end.grid(row=2, column=1)

    s = Session()
    employees = s.query(Employee).all()
    emp_map = {f"{e.first_name} {e.last_name}": e.id for e in employees}
    emp_box["values"] = list(emp_map.keys())
    s.close()

    def save():
        employee_id = emp_map.get(emp_var.get())
        if not employee_id:
            messagebox.showerror("Ошибка", "Выберите сотрудника")
            return

        start = datetime.strptime(e_start.get(), "%Y-%m-%d %H:%M")
        end = datetime.strptime(e_end.get(), "%Y-%m-%d %H:%M") if e_end.get() else None

        s = Session()
        s.add(Shift(employee_id=employee_id, start_time=start, end_time=end))
        s.commit()
        s.close()

        load_shifts()
        win.destroy()

    tk.Button(win, text="Сохранить", command=save).grid(columnspan=2)


def create_employee():
    win = tk.Toplevel(root)
    win.title("Новый сотрудник")

    tk.Label(win, text="Имя").grid(row=0, column=0)
    tk.Label(win, text="Фамилия").grid(row=1, column=0)
    tk.Label(win, text="Должность").grid(row=2, column=0)

    e_fn = tk.Entry(win)
    e_ln = tk.Entry(win)
    e_fn.grid(row=0, column=1)
    e_ln.grid(row=1, column=1)

    pos_var = tk.StringVar()
    pos_box = ttk.Combobox(win, textvariable=pos_var, state="readonly")
    pos_box.grid(row=2, column=1)

    s = Session()
    pos_box["values"] = [p.name for p in s.query(Position).all()]
    s.close()

    def save():
        s = Session()
        pos = s.query(Position).filter_by(name=pos_var.get()).first()
        s.add(Employee(first_name=e_fn.get(), last_name=e_ln.get(), position=pos))
        s.commit()
        s.close()
        load_employees()
        win.destroy()

    tk.Button(win, text="Сохранить", command=save).grid(columnspan=2)


def create_menu_item():
    win = tk.Toplevel(root)
    win.title("Новый пункт меню")

    tk.Label(win, text="Название").grid(row=0, column=0)
    tk.Label(win, text="Цена").grid(row=1, column=0)
    tk.Label(win, text="Категория").grid(row=2, column=0)

    e_name = tk.Entry(win)
    e_price = tk.Entry(win)
    e_name.grid(row=0, column=1)
    e_price.grid(row=1, column=1)

    cat_var = tk.StringVar()
    cat_box = ttk.Combobox(win, textvariable=cat_var, state="readonly")
    cat_box.grid(row=2, column=1)

    s = Session()
    cats = s.query(ItemCategory).all()
    cat_box["values"] = [c.name for c in cats]
    s.close()

    def save():
        s = Session()
        cat = s.query(ItemCategory).filter_by(name=cat_var.get()).first()
        s.add(MenuItem(name=e_name.get(), price=float(e_price.get()), category=cat))
        s.commit()
        s.close()
        load_menu()
        win.destroy()

    tk.Button(win, text="Сохранить", command=save).grid(columnspan=2)


def create_customer():
    win = tk.Toplevel(root)
    win.title("Новый клиент")

    tk.Label(win, text="Имя").grid(row=0, column=0)
    tk.Label(win, text="Email").grid(row=1, column=0)

    e_name = tk.Entry(win)
    e_email = tk.Entry(win)
    e_name.grid(row=0, column=1)
    e_email.grid(row=1, column=1)

    def save():
        s = Session()
        s.add(Customer(name=e_name.get(), email=e_email.get()))
        s.commit()
        s.close()
        load_customers()
        win.destroy()

    tk.Button(win, text="Сохранить", command=save).grid(columnspan=2)


def create_category():
    win = tk.Toplevel(root)
    win.title("Новая категория")

    tk.Label(win, text="Название").grid(row=0, column=0)
    e_name = tk.Entry(win)
    e_name.grid(row=0, column=1)

    def save():
        s = Session()
        s.add(ItemCategory(name=e_name.get()))
        s.commit()
        s.close()
        load_categories()
        win.destroy()

    tk.Button(win, text="Сохранить", command=save).grid(columnspan=2)


# ===================== GUI =====================

root = tk.Tk()
root.title("Business App")
root.geometry("1000x600")

nb = ttk.Notebook(root)
nb.pack(fill="both", expand=True)

# Customers
fc = ttk.Frame(nb)
nb.add(fc, text="Customers")
customers_tree = create_table(fc, ("id", "name", "email"), ("ID", "Имя", "Email"))
tk.Button(fc, text="➕ Добавить", command=create_customer).pack()
tk.Button(
    fc,
    text="🗑 Удалить",
    command=lambda: delete_selected(customers_tree, Customer, load_customers),
).pack()
load_customers()

# Positions
fp = ttk.Frame(nb)
nb.add(fp, text="Positions")
positions_tree = create_table(fp, ("id", "name", "salary"), ("ID", "Название", "ЗП"))
tk.Button(fp, text="➕ Добавить", command=create_position).pack()
tk.Button(
    fp,
    text="🗑 Удалить",
    command=lambda: delete_selected(positions_tree, Position, load_positions),
).pack()
load_positions()

# Employees
fe = ttk.Frame(nb)
nb.add(fe, text="Employees")
employees_tree = create_table(
    fe,
    ("id", "first", "last", "position"),
    ("ID", "Имя", "Фамилия", "Должность"),
)
tk.Button(fe, text="➕ Добавить", command=create_employee).pack()
tk.Button(
    fe,
    text="🗑 Удалить",
    command=lambda: delete_selected(employees_tree, Employee, load_employees),
).pack()
load_employees()

# Categories
fcat = ttk.Frame(nb)
nb.add(fcat, text="Categories")
categories_tree = create_table(fcat, ("id", "name"), ("ID", "Название"))
tk.Button(fcat, text="➕ Добавить", command=create_category).pack()
tk.Button(
    fcat,
    text="🗑 Удалить",
    command=lambda: delete_selected(categories_tree, ItemCategory, load_categories),
).pack()
load_categories()

# Menu
fm = ttk.Frame(nb)
nb.add(fm, text="Menu")
menu_tree = create_table(
    fm,
    ("id", "name", "price", "category"),
    ("ID", "Название", "Цена", "Категория"),
)
tk.Button(fm, text="➕ Добавить", command=create_menu_item).pack()
tk.Button(
    fm,
    text="🗑 Удалить",
    command=lambda: delete_selected(menu_tree, MenuItem, load_menu),
).pack()
load_menu()

# Shifts
fs = ttk.Frame(nb)
nb.add(fs, text="Shifts")

shifts_tree = create_table(
    fs,
    ("id", "employee", "start", "end", "hours", "money"),
    ("ID", "Сотрудник", "Начало", "Конец", "Часы", "Заработал"),
)
tk.Button(fs, text="➕ Добавить", command=create_shift).pack()
tk.Button(
    fs,
    text="🗑 Удалить",
    command=lambda: delete_selected(shifts_tree, Shift, load_shifts),
).pack()

load_shifts()

root.mainloop()
