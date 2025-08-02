import pytest
import sqlite3
import hashlib
import datetime
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from dollmart import setup_database, generate_coupon_code, create_coupon, apply_coupon, Customer, Admin


setup_database()

@pytest.fixture
def db_connection():
    conn = sqlite3.connect('dollmart.db')
    yield conn
    conn.close()

def test_generate_coupon_code():
    user_id = 1
    type_prefix = "TEST"
    coupon_code = generate_coupon_code(user_id, type_prefix)
    assert coupon_code.startswith("TEST-")
    assert len(coupon_code) == 13

def test_create_coupon(db_connection):
    user_id = 1
    discount_percentage = 10
    coupon_id, coupon_code = create_coupon(user_id, discount_percentage, "TEST", db_connection)
    cursor = db_connection.cursor()
    cursor.execute("SELECT code, discount_percentage FROM coupons WHERE id = ?", (coupon_id,))
    coupon = cursor.fetchone()
    assert coupon is not None
    assert coupon[0] == coupon_code
    assert coupon[1] == discount_percentage

def test_apply_invalid_coupon(db_connection):
    user_id = 1
    total_amount = 100.0
    success, new_total, discount, code, coupon_percentage = apply_coupon(user_id, 999, total_amount)
    assert not success
    assert new_total == total_amount
    assert discount == 0
    assert code is None
    assert coupon_percentage is None

def test_apply_used_coupon(db_connection):
    user_id = 1
    discount_percentage = 10
    total_amount = 100.0
    coupon_id, coupon_code = create_coupon(user_id, discount_percentage, "TEST", db_connection)
    apply_coupon(user_id, coupon_id, total_amount)  # Apply once
    success, new_total, discount, code, coupon_percentage = apply_coupon(user_id, coupon_id, total_amount)
    assert not success
    assert new_total == total_amount
    assert discount == 0
    assert code is None
    assert coupon_percentage is None

def test_register_user(db_connection):
    username = "testuser"
    password = "testpass"
    customer_type = "n"
    is_retail = 1 if customer_type == 'y' else 0
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    registration_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor = db_connection.cursor()
    cursor.execute(
        "INSERT INTO users (username, password_hash, role, is_retail, registration_date) VALUES (?, ?, ?, ?, ?)",
        (username, password_hash, "customer", is_retail, registration_date)
    )
    db_connection.commit()
    user_id = cursor.lastrowid
    assert user_id is not None

def test_register_existing_user(db_connection):
    username = "testuser"
    password = "testpass"
    customer_type = "n"
    is_retail = 1 if customer_type == 'y' else 0
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    registration_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor = db_connection.cursor()
    
   
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash, role, is_retail, registration_date) VALUES (?, ?, ?, ?, ?)",
            (username, password_hash, "customer", is_retail, registration_date)
        )
        db_connection.commit()
    except sqlite3.IntegrityError:
        db_connection.rollback()
    
   
    with pytest.raises(sqlite3.IntegrityError):
        try:
            cursor.execute(
                "INSERT INTO users (username, password_hash, role, is_retail, registration_date) VALUES (?, ?, ?, ?, ?)",
                (username, password_hash, "customer", is_retail, registration_date)
            )
            db_connection.commit()
        except sqlite3.IntegrityError:
            db_connection.rollback()
            raise

def test_login_user(db_connection):
    username = "testuser"
    password = "testpass"
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    cursor = db_connection.cursor()
    cursor.execute("SELECT id, role, is_retail, orders_count FROM users WHERE username = ? AND password_hash = ?", 
                  (username, password_hash))
    user = cursor.fetchone()
    assert user is not None

def test_login_invalid_user(db_connection):
    username = "invaliduser"
    password = "invalidpass"
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    cursor = db_connection.cursor()
    cursor.execute("SELECT id, role, is_retail, orders_count FROM users WHERE username = ? AND password_hash = ?", 
                  (username, password_hash))
    user = cursor.fetchone()
    assert user is None

def test_customer_cart_operations():
    customer = Customer(1, "testuser")
    customer.add_to_cart(1, 2)
    assert customer.cart[1]["quantity"] == 2
    customer.add_to_cart(1, 3)
    assert customer.cart[1]["quantity"] == 5

def test_customer_cart_invalid_product():
    customer = Customer(1, "testuser")
    customer.add_to_cart(999, 2)
    assert 999 not in customer.cart

def test_customer_place_order(db_connection, monkeypatch):
    customer = Customer(1, "testuser")
    customer.add_to_cart(1, 2)
    
    
    monkeypatch.setattr('builtins.input', lambda _: 'y')
    
    customer.place_order()
    cursor = db_connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM orders WHERE user_id = ?", (customer.id,))
    order_count = cursor.fetchone()[0]
    assert order_count > 0

def test_customer_place_order_empty_cart():
    customer = Customer(1, "testuser")
    customer.place_order()
    assert not customer.cart

def test_admin_view_all_products(db_connection):
    admin = Admin(1, "admin")
    conn = db_connection
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM products")
    product_count = cursor.fetchone()[0]
    assert product_count > 0

def test_admin_add_product(db_connection):
    admin = Admin(1, "admin")
    name = "Test Product"
    category = "Test Category"
    price = 9.99
    stock = 100
    bulk_discount = 0.1
    cursor = db_connection.cursor()
    cursor.execute(
        "INSERT INTO products (name, category, price, stock, bulk_discount) VALUES (?, ?, ?, ?, ?)",
        (name, category, price, stock, bulk_discount)
    )
    db_connection.commit()
    product_id = cursor.lastrowid
    assert product_id is not None

def test_admin_update_product(db_connection):
    admin = Admin(1, "admin")
    product_id = 1
    new_name = "Updated Product"
    cursor = db_connection.cursor()
    cursor.execute(
        "UPDATE products SET name = ? WHERE id = ?",
        (new_name, product_id)
    )
    db_connection.commit()
    cursor.execute("SELECT name FROM products WHERE id = ?", (product_id,))
    updated_name = cursor.fetchone()[0]
    assert updated_name == new_name

def test_admin_delete_product(db_connection):
    admin = Admin(1, "admin")
    product_id = 1
    cursor = db_connection.cursor()
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    db_connection.commit()
    cursor.execute("SELECT COUNT(*) FROM products WHERE id = ?", (product_id,))
    product_count = cursor.fetchone()[0]
    assert product_count == 0

def test_apply_coupon_invalid_amount(db_connection):
    user_id = 1
    discount_percentage = 10
    total_amount = -50.0  
    coupon_id, coupon_code = create_coupon(user_id, discount_percentage, "TEST", db_connection)
    success, new_total, discount, code, coupon_percentage = apply_coupon(user_id, coupon_id, total_amount)
    assert not success
    assert new_total == total_amount
    assert discount == 0
    assert code is None
    assert coupon_percentage is None

def test_register_user_with_existing_username(db_connection):
    username = "testuser"
    password = "testpass"
    customer_type = "n"
    is_retail = 1 if customer_type == 'y' else 0
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    registration_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor = db_connection.cursor()
    
    
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash, role, is_retail, registration_date) VALUES (?, ?, ?, ?, ?)",
            (username, password_hash, "customer", is_retail, registration_date)
        )
        db_connection.commit()
    except sqlite3.IntegrityError:
        db_connection.rollback()
    
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,))
    user_count = cursor.fetchone()[0]
    assert user_count == 1
    
   
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute(
            "INSERT INTO users (username, password_hash, role, is_retail, registration_date) VALUES (?, ?, ?, ?, ?)",
            (username, password_hash, "customer", is_retail, registration_date)
        )
        db_connection.commit()

def test_login_user_with_wrong_password(db_connection):
    username = "testuser"
    password = "wrongpass"
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    cursor = db_connection.cursor()
    cursor.execute("SELECT id, role, is_retail, orders_count FROM users WHERE username = ? AND password_hash = ?", 
                  (username, password_hash))
    user = cursor.fetchone()
    assert user is None

def test_customer_cart_remove_item(db_connection):
   
    cursor = db_connection.cursor()
    cursor.execute(
        "INSERT INTO products (id, name, category, price, stock, bulk_discount) VALUES (?, ?, ?, ?, ?, ?)",
        (1, "Test Product", "Test Category", 9.99, 100, 0.1)
    )
    db_connection.commit()
    
    customer = Customer(1, "testuser")
    customer.add_to_cart(1, 2)
    assert customer.cart[1]["quantity"] == 2
    customer.remove_from_cart(1)
    assert 1 not in customer.cart

def test_customer_cart_update_quantity(db_connection):
    cursor = db_connection.cursor()
    
    
    cursor.execute("SELECT COUNT(*) FROM products WHERE id = ?", (1,))
    product_exists = cursor.fetchone()[0] > 0
    
    if not product_exists:
        cursor.execute(
            "INSERT INTO products (id, name, category, price, stock, bulk_discount) VALUES (?, ?, ?, ?, ?, ?)",
            (1, "Test Product", "Test Category", 9.99, 100, 0.1)
        )
        db_connection.commit()
    
    customer = Customer(1, "testuser")
    customer.add_to_cart(1, 2)
    assert customer.cart[1]["quantity"] == 2
    customer.update_cart(1, 5)
    assert customer.cart[1]["quantity"] == 5
