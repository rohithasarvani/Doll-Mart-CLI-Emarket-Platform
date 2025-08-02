import os
import sqlite3
import datetime
import random
import time
import hashlib
import uuid
from tabulate import tabulate
from abc import ABC, abstractmethod


PROCESSING_TIME_HOURS = 2  
DELIVERY_TIME_HOURS = 24  


def setup_database():
    """Initialize the SQLite database with necessary tables if they don't exist"""
    conn = sqlite3.connect('dollmart.db')
    cursor = conn.cursor()
    
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL,
        is_retail INTEGER NOT NULL,
        orders_count INTEGER DEFAULT 0,
        registration_date TEXT
    )
    ''')
    
   
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL,
        stock INTEGER NOT NULL,
        bulk_discount REAL DEFAULT 0
    )
    ''')
  
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        order_date TEXT NOT NULL,
        status TEXT NOT NULL,
        total_amount REAL NOT NULL,
        estimated_delivery TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS order_items (
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        PRIMARY KEY (order_id, product_id),
        FOREIGN KEY (order_id) REFERENCES orders (id),
        FOREIGN KEY (product_id) REFERENCES products (id)
    )
    ''')
    
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS coupons (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        code TEXT NOT NULL,
        discount_percentage REAL NOT NULL,
        used INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE role='admin'")
    if cursor.fetchone()[0] == 0:
        admin_pass = hashlib.sha256("admin123".encode()).hexdigest()
        cursor.execute("INSERT INTO users (username, password_hash, role, is_retail, registration_date) VALUES (?, ?, ?, ?, ?)", 
                      ("admin", admin_pass, "admin", 0, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    
   
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        sample_products = [
            ("Rice", "Groceries", 2.99, 100, 0.1),
            ("Milk", "Groceries", 1.99, 50, 0.1),
            ("Bread", "Groceries", 1.49, 30, 0.1),
            ("Smartphone", "Electronics", 499.99, 10, 0.05),
            ("Laptop", "Electronics", 899.99, 5, 0.05),
            ("Shampoo", "Personal Care", 4.99, 40, 0.15),
            ("Toothpaste", "Personal Care", 2.49, 60, 0.15)
        ]
        cursor.executemany("INSERT INTO products (name, category, price, stock, bulk_discount) VALUES (?, ?, ?, ?, ?)", 
                          sample_products)
    
    conn.commit()
    conn.close()



def update_order_statuses():
    """Update order statuses based on time elapsed since order creation"""
    conn = sqlite3.connect('dollmart.db')
    cursor = conn.cursor()
    
    
    current_time = datetime.datetime.now()
    
    
    cursor.execute("SELECT id, order_date, status FROM orders WHERE status != 'Delivered'")
    orders = cursor.fetchall()
    
    for order in orders:
        order_id, order_date_str, status = order
        order_date = datetime.datetime.strptime(order_date_str, "%Y-%m-%d %H:%M:%S")
        
        
        elapsed_time = current_time - order_date
        hours_elapsed = elapsed_time.total_seconds() / 3600
        
        new_status = status
        
       
        if status == "Processing" and hours_elapsed >= PROCESSING_TIME_HOURS:
            new_status = "Out for Delivery"
        elif status == "Out for Delivery" and hours_elapsed >= (PROCESSING_TIME_HOURS + DELIVERY_TIME_HOURS):
            new_status = "Delivered"
        
        
        if new_status != status:
            cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
    
    conn.commit()
    conn.close()

def generate_coupon_code(user_id, type_prefix):
    """Generate a unique coupon code based on user ID and coupon type
    
    Args:
        user_id: The user's ID
        type_prefix: A prefix indicating the coupon type (e.g., WELCOME, LOYAL)
        
    Returns:
        A unique coupon code string
    """
    timestamp = int(time.time())
    unique_id = hashlib.md5(f"{user_id}{timestamp}{random.randint(1000,9999)}".encode()).hexdigest()[:8].upper()
    return f"{type_prefix}-{unique_id}"


def create_coupon(user_id, discount_percentage, type_prefix="COUPON", existing_conn=None):
    """Create a new coupon for a user
    
    Args:
        user_id: The user's ID
        discount_percentage: The percentage discount to apply
        type_prefix: The type of coupon (e.g., WELCOME, LOYAL)
        existing_conn: An existing database connection (optional)
        
    Returns:
        The coupon ID and code
    """
   
    should_close_conn = False
    if existing_conn is None:
        conn = sqlite3.connect('dollmart.db')
        should_close_conn = True
    else:
        conn = existing_conn
    
    cursor = conn.cursor()
    
    coupon_code = generate_coupon_code(user_id, type_prefix)
    
    cursor.execute(
        "INSERT INTO coupons (user_id, code, discount_percentage, used) VALUES (?, ?, ?, ?)",
        (user_id, coupon_code, discount_percentage, 0)
    )
    
    coupon_id = cursor.lastrowid
    
    
    if should_close_conn:
        conn.commit()
        conn.close()
    
    return coupon_id, coupon_code


def apply_coupon(user_id, coupon_id, total_amount):
    """Apply a coupon to the total amount
    
    Args:
        user_id: The user's ID
        coupon_id: The ID of the coupon to apply
        total_amount: The current total amount
        
    Returns:
        tuple: (successful, new_total, discount, coupon_code, coupon_percentage)
    """
    conn = sqlite3.connect('dollmart.db')
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT code, discount_percentage FROM coupons WHERE id = ? AND user_id = ? AND used = 0",
        (coupon_id, user_id)
    )
    coupon = cursor.fetchone()
    
    if not coupon:
        conn.close()
        return False, total_amount, 0, None, None
    
    code, discount_percentage = coupon
    discount = total_amount * (discount_percentage / 100)
    new_total = total_amount - discount
    
    
    cursor.execute("UPDATE coupons SET used = 1 WHERE id = ?", (coupon_id,))
    conn.commit()
    conn.close()
    
    return True, new_total, discount, code, discount_percentage


class User(ABC):
    def __init__(self, user_id, username, role, is_retail=0):
        self.id = user_id
        self.username = username
        self.role = role
        self.is_retail = is_retail
        self.orders_count = 0
    
    @abstractmethod
    def show_menu(self):
        pass

class Customer(User):
    def __init__(self, user_id, username, is_retail=0, orders_count=0):
        super().__init__(user_id, username, "customer", is_retail)
        self.orders_count = orders_count
        self.cart = {}
    
    def show_menu(self):
        while True:

            update_order_statuses()
            
            print("\n===== DollMart Customer Menu =====")
            print("1. Browse Products by Category")
            print("2. Search Products")
            print("3. View Cart")
            print("4. Place Order")
            print("5. View Order History")
            print("6. Check Available Coupons")
            print("7. Logout")
            
            choice = input("\nEnter your choice: ")
            
            if choice == '1':
                self.browse_products()
            elif choice == '2':
                self.search_products()
            elif choice == '3':
                self.view_cart()
            elif choice == '4':
                self.place_order()
            elif choice == '5':
                self.view_order_history()
            elif choice == '6':
                self.check_coupons()
            elif choice == '7':
                print("Logging out...")
                return
            else:
                print("Invalid choice. Please try again.")
    
    def browse_products(self):
        conn = sqlite3.connect('dollmart.db')
        cursor = conn.cursor()
        
        
        cursor.execute("SELECT DISTINCT category FROM products")
        categories = cursor.fetchall()
        
        print("\n===== Product Categories =====")
        for i, category in enumerate(categories, 1):
            print(f"{i}. {category[0]}")
        
        try:
            choice = int(input("\nSelect a category (0 to cancel): "))
            if choice == 0:
                conn.close()
                return
            
            selected_category = categories[choice-1][0]
            
           
            cursor.execute("SELECT id, name, price, stock FROM products WHERE category = ?", (selected_category,))
            products = cursor.fetchall()
            
            print(f"\n===== Products in {selected_category} =====")
            products_table = []
            for product in products:
                products_table.append([product[0], product[1], f"${product[2]:.2f}", product[3]])
            
            print(tabulate(products_table, headers=["ID", "Name", "Price", "Stock"], tablefmt="simple"))
            
            
            product_id = input("\nEnter product ID to add to cart (0 to cancel): ")
            if product_id != '0':
                quantity = int(input("Enter quantity: "))
                self.add_to_cart(int(product_id), quantity)
        
        except (ValueError, IndexError):
            print("Invalid selection.")
        
        conn.close()
    
    def search_products(self):
        search_term = input("\nEnter product name to search: ")
        
        conn = sqlite3.connect('dollmart.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name, category, price, stock FROM products WHERE name LIKE ?", (f"%{search_term}%",))
        products = cursor.fetchall()
        
        if not products:
            print("No products found matching your search.")
        else:
            print("\n===== Search Results =====")
            products_table = []
            for product in products:
                products_table.append([product[0], product[1], product[2], f"${product[3]:.2f}", product[4]])
            
            print(tabulate(products_table, headers=["ID", "Name", "Category", "Price", "Stock"], tablefmt="simple"))
            
            
            product_id = input("\nEnter product ID to add to cart (0 to cancel): ")
            if product_id != '0':
                quantity = int(input("Enter quantity: "))
                self.add_to_cart(int(product_id), quantity)
        
        conn.close()
    
    def add_to_cart(self, product_id, quantity):
        conn = sqlite3.connect('dollmart.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT name, price, stock FROM products WHERE id = ?", (product_id,))
        product = cursor.fetchone()
        
        if not product:
            print("Product not found.")
            conn.close()
            return
        
        if product[2] < quantity:
            print(f"Sorry, only {product[2]} units available in stock.")
            conn.close()
            return
        
        
        if product_id in self.cart:
            self.cart[product_id]["quantity"] += quantity
        else:
            self.cart[product_id] = {
                "name": product[0],
                "price": product[1],
                "quantity": quantity
            }
        
        print(f"Added {quantity} x {product[0]} to your cart.")
        conn.close()
    
    def remove_from_cart(self, product_id):
        if product_id in self.cart:
            del self.cart[product_id]

    def update_cart(self, product_id, quantity):
        if product_id in self.cart:
            self.cart[product_id]["quantity"] = quantity
        else:
            print("Product not found in cart.")

    def place_order(self):
        """Place an order with improved coupon application flow"""
        if not self.cart:
            print("Your cart is empty. Add items before placing an order.")
            return
        
        
        self.view_cart()
        
        conn = sqlite3.connect('dollmart.db')
        cursor = conn.cursor()
        
        
        total_amount = sum(item["price"] * item["quantity"] for item in self.cart.values())
        final_amount = total_amount
        
        
        bulk_discount_applied = False
        bulk_discount_amount = 0
        if self.is_retail and self.calculate_total_quantity() >= 50:
            bulk_discount_amount = total_amount * 0.1
            final_amount = total_amount - bulk_discount_amount
            bulk_discount_applied = True
            print(f"\nRetail Bulk Discount (10%): -${bulk_discount_amount:.2f}")
            print(f"After Bulk Discount: ${final_amount:.2f}")
        
        
        coupon_applied = False
        coupon_id = None
        coupon_discount = 0
        
        
        cursor.execute("SELECT COUNT(*) FROM coupons WHERE user_id = ? AND used = 0", (self.id,))
        has_coupons = cursor.fetchone()[0] > 0
        
        if has_coupons:
            use_coupon = input("\nWould you like to use a coupon for this order? (y/n): ").lower()
            
            if use_coupon == 'y':
                
                cursor.execute(
                    "SELECT id, code, discount_percentage FROM coupons WHERE user_id = ? AND used = 0", 
                    (self.id,)
                )
                coupons = cursor.fetchall()
                
                print("\n===== Your Available Coupons =====")
                coupons_table = []
                for coupon in coupons:
                    coupons_table.append([coupon[0], coupon[1], f"{coupon[2]}%"])
                
                print(tabulate(coupons_table, headers=["Coupon ID", "Code", "Discount"], tablefmt="simple"))
                
               
                try:
                    coupon_id = int(input("\nEnter Coupon ID to apply (0 to skip): "))
                    
                    if coupon_id > 0:
                       
                        success, discounted_total, discount_amount, coupon_code, discount_percentage = apply_coupon(
                            self.id, coupon_id, final_amount
                        )
                        
                        if success:
                            coupon_applied = True
                            coupon_discount = discount_amount
                            final_amount = discounted_total
                            print(f"\nCoupon {coupon_code} applied!")
                            print(f"Coupon Discount ({discount_percentage}%): -${coupon_discount:.2f}")
                            print(f"Final Total: ${final_amount:.2f}")
                        else:
                            print("Invalid coupon ID or coupon already used.")
                            coupon_id = None
                except ValueError:
                    print("Invalid input. No coupon applied.")
                    coupon_id = None
        
        
        print("\n===== Order Summary =====")
        print(f"Subtotal: ${total_amount:.2f}")
        
        if bulk_discount_applied:
            print(f"Bulk Discount (10%): -${bulk_discount_amount:.2f}")
        
        if coupon_applied:
            print(f"Coupon Discount: -${coupon_discount:.2f}")
        
        print(f"Final Total: ${final_amount:.2f}")
        
        
        confirm = input("\nConfirm order? (y/n): ").lower()
        if confirm != 'y':
            print("Order cancelled.")
            conn.close()
            return
        
        
        order_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        estimated_delivery = (datetime.datetime.now() + datetime.timedelta(hours=PROCESSING_TIME_HOURS + DELIVERY_TIME_HOURS)).strftime("%Y-%m-%d %H:%M")
        
        cursor.execute(
            "INSERT INTO orders (user_id, order_date, status, total_amount, estimated_delivery) VALUES (?, ?, ?, ?, ?)",
            (self.id, order_date, "Processing", final_amount, estimated_delivery)
        )
        
        order_id = cursor.lastrowid
        
        
        for product_id, item in self.cart.items():
            cursor.execute(
                "INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)",
                (order_id, product_id, item["quantity"], item["price"])
            )
            
            cursor.execute(
                "UPDATE products SET stock = stock - ? WHERE id = ?",
                (item["quantity"], product_id)
            )
        
        
        if coupon_id:
            cursor.execute("UPDATE coupons SET used = 1 WHERE id = ?", (coupon_id,))
        
        
        self.orders_count += 1
        cursor.execute("UPDATE users SET orders_count = ? WHERE id = ?", (self.orders_count, self.id))
        
        
        if self.orders_count % 3 == 0:
            new_coupon_id, coupon_code = create_coupon(self.id, 5, "LOYAL", existing_conn=conn)
            print(f"\nCongratulations! You've earned a loyalty coupon: {coupon_code} (5% off)")
        
        conn.commit()
        conn.close()
        
        print(f"\nOrder placed successfully! Your order ID is: {order_id}")
        print(f"Status: Processing")
        print(f"Will be out for delivery after: {(datetime.datetime.now() + datetime.timedelta(hours=PROCESSING_TIME_HOURS)).strftime('%Y-%m-%d %H:%M')}")
        print(f"Estimated delivery by: {estimated_delivery}")
        
        
        self.cart = {}
    
    def view_cart(self):
        if not self.cart:
            print("Your cart is empty.")
            return
        
        print("\n===== Your Cart =====")
        cart_table = []
        total = 0
        
        for product_id, item in self.cart.items():
            subtotal = item["price"] * item["quantity"]
            cart_table.append([item["name"], item["quantity"], f"${item['price']:.2f}", f"${subtotal:.2f}"])
            total += subtotal
        
        print(tabulate(cart_table, headers=["Product", "Quantity", "Unit Price", "Subtotal"], tablefmt="simple"))
        print(f"\nTotal: ${total:.2f}")
        
        
        if self.is_retail and self.calculate_total_quantity() >= 50:
            discount = total * 0.1
            print(f"Retail Bulk Discount (10%): -${discount:.2f}")
            print(f"Final Total: ${total - discount:.2f}")
    
    def calculate_total_quantity(self):
        return sum(item["quantity"] for item in self.cart.values())
    
    def view_order_history(self):
        conn = sqlite3.connect('dollmart.db')
        cursor = conn.cursor()
        
        
        update_order_statuses()
        
        cursor.execute(
            """
            SELECT id, order_date, status, total_amount, estimated_delivery
            FROM orders
            WHERE user_id = ?
            ORDER BY order_date DESC
            """,
            (self.id,)
        )
        orders = cursor.fetchall()
        
        if not orders:
            print("You have no order history.")
        else:
            print("\n===== Your Order History =====")
            orders_table = []
            for order in orders:
                orders_table.append([
                    order[0],
                    order[1],
                    order[2],
                    f"${order[3]:.2f}",
                    order[4]
                ])
            
            print(tabulate(orders_table, headers=["Order ID", "Date", "Status", "Amount", "Est. Delivery"], tablefmt="simple"))
            
            
            order_id = input("\nEnter order ID to view details (0 to cancel): ")
            if order_id != '0':
                try:
                    self.view_order_details(int(order_id))
                except ValueError:
                    print("Invalid order ID.")
        
        conn.close()
    
    def view_order_details(self, order_id):
        conn = sqlite3.connect('dollmart.db')
        cursor = conn.cursor()
        
        
        cursor.execute("SELECT id FROM orders WHERE id = ? AND user_id = ?", (order_id, self.id))
        if not cursor.fetchone():
            print("Order not found or doesn't belong to you.")
            conn.close()
            return
        
        
        cursor.execute(
            """
            SELECT p.name, oi.quantity, oi.price, (oi.quantity * oi.price) as subtotal
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = ?
            """,
            (order_id,)
        )
        items = cursor.fetchall()
        
        print(f"\n===== Order #{order_id} Details =====")
        items_table = []
        for item in items:
            items_table.append([item[0], item[1], f"${item[2]:.2f}", f"${item[3]:.2f}"])
        
        print(tabulate(items_table, headers=["Product", "Quantity", "Unit Price", "Subtotal"], tablefmt="simple"))
        
        conn.close()
    
    def check_coupons(self):
        conn = sqlite3.connect('dollmart.db')
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, code, discount_percentage, used FROM coupons WHERE user_id = ?", 
            (self.id,)
        )
        coupons = cursor.fetchall()
        
        if not coupons:
            print("You don't have any coupons.")
        else:
            print("\n===== Your Coupons =====")
            coupons_table = []
            for coupon in coupons:
                status = "Used" if coupon[3] == 1 else "Available"
                coupons_table.append([coupon[0], coupon[1], f"{coupon[2]}%", status])
            
            print(tabulate(coupons_table, headers=["ID", "Code", "Discount", "Status"], tablefmt="simple"))
        
        conn.close()

class Admin(User):
    def __init__(self, user_id, username):
        super().__init__(user_id, username, "admin")
       
    
    def show_menu(self):
        while True:
            print("\n===== DollMart Admin Menu =====")
            print("1. Manage Products")
            print("2. Manage Orders")
            print("3. Manage Customers")
            print("4. Logout")
            
            choice = input("\nEnter your choice: ")
            
            if choice == '1':
                self.product_management()
            elif choice == '2':
                self.order_management()
            elif choice == '3':
                self.customer_management()
            elif choice == '4':
                print("Logging out...")
                return
            else:
                print("Invalid choice. Please try again.")
    
    def product_management(self):
        while True:
            print("\n===== Product Management =====")
            print("1. View All Products")
            print("2. Add New Product")
            print("3. Update Product")
            print("4. Delete Product")
            print("5. Back to Main Menu")
            
            choice = input("\nEnter your choice: ")
            
            if choice == '1':
                self.view_all_products()
            elif choice == '2':
                self.add_product()
            elif choice == '3':
                self.update_product()
            elif choice == '4':
                self.delete_product()
            elif choice == '5':
                return
            else:
                print("Invalid choice. Please try again.")
    
    def view_all_products(self):
        conn = sqlite3.connect('dollmart.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name, category, price, stock, bulk_discount FROM products")
        products = cursor.fetchall()
        
        if not products:
            print("No products found.")
        else:
            print("\n===== All Products =====")
            products_table = []
            for product in products:
                products_table.append([
                    product[0], 
                    product[1], 
                    product[2], 
                    f"${product[3]:.2f}", 
                    product[4],
                    f"{product[5]*100:.0f}%"
                ])
            
            print(tabulate(products_table, headers=["ID", "Name", "Category", "Price", "Stock", "Bulk Discount"], tablefmt="simple"))
        
        conn.close()
    
    def add_product(self):
        try:
            name = input("Enter product name: ")
            category = input("Enter product category: ")
            price = float(input("Enter product price: $"))
            stock = int(input("Enter initial stock quantity: "))
            bulk_discount_str = input("Enter bulk discount percentage (e.g., 10 for 10%): ")
            bulk_discount = float(bulk_discount_str) / 100 if bulk_discount_str else 0
            
            conn = sqlite3.connect('dollmart.db')
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO products (name, category, price, stock, bulk_discount) VALUES (?, ?, ?, ?, ?)",
                (name, category, price, stock, bulk_discount)
            )
            
            conn.commit()
            print(f"Product '{name}' added successfully with ID: {cursor.lastrowid}")
            
            conn.close()
        
        except ValueError:
            print("Invalid input. Please enter numeric values where required.")
    
    def update_product(self):
        self.view_all_products()
        
        try:
            product_id = int(input("\nEnter product ID to update: "))
            
            conn = sqlite3.connect('dollmart.db')
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
            product = cursor.fetchone()
            
            if not product:
                print("Product not found.")
                conn.close()
                return
            
            print("\nLeave field empty to keep current value.")
            name = input(f"Name [{product[1]}]: ") or product[1]
            category = input(f"Category [{product[2]}]: ") or product[2]
            price_str = input(f"Price [${product[3]:.2f}]: ")
            price = float(price_str) if price_str else product[3]
            stock_str = input(f"Stock [{product[4]}]: ")
            stock = int(stock_str) if stock_str else product[4]
            discount_str = input(f"Bulk discount [{product[5]*100}%]: ")
            bulk_discount = float(discount_str)/100 if discount_str else product[5]
            
            cursor.execute(
                "UPDATE products SET name = ?, category = ?, price = ?, stock = ?, bulk_discount = ? WHERE id = ?",
                (name, category, price, stock, bulk_discount, product_id)
            )
            
            conn.commit()
            print("Product updated successfully!")
            
            conn.close()
        
        except ValueError:
            print("Invalid input. Please enter numeric values where required.")
    
    def delete_product(self):
        self.view_all_products()
        
        try:
            product_id = int(input("\nEnter product ID to delete: "))
            
            confirm = input(f"Are you sure you want to delete product #{product_id}? (y/n): ").lower()
            if confirm != 'y':
                print("Deletion cancelled.")
                return
            
            conn = sqlite3.connect('dollmart.db')
            cursor = conn.cursor()
            
           
            cursor.execute("SELECT name FROM products WHERE id = ?", (product_id,))
            product = cursor.fetchone()
            
            if not product:
                print("Product not found.")
                conn.close()
                return
            
            
            cursor.execute("SELECT COUNT(*) FROM order_items WHERE product_id = ?", (product_id,))
            if cursor.fetchone()[0] > 0:
                print("Cannot delete product as it is part of existing orders.")
                conn.close()
                return
            
            cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
            
            conn.commit()
            print(f"Product '{product[0]}' deleted successfully!")
            
            conn.close()
        
        except ValueError:
            print("Invalid input. Please enter a numeric product ID.")
    
    def order_management(self):
        while True:
            print("\n===== Order Management =====")
            print("1. View All Orders")
            print("2. View Order Details")
            print("3. Back to Main Menu")
            
            choice = input("\nEnter your choice: ")
            
            if choice == '1':
                self.view_all_orders()
            elif choice == '2':
                order_id = input("Enter order ID: ")
                try:
                    self.view_order_details(int(order_id))
                except ValueError:
                    print("Invalid order ID. Please enter a number.")
            elif choice == '3':
                return
            else:
                print("Invalid choice. Please try again.")
    
    def view_all_orders(self):
        
        update_order_statuses()
        
        conn = sqlite3.connect('dollmart.db')
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT o.id, u.username, o.order_date, o.status, o.total_amount, o.estimated_delivery
            FROM orders o
            JOIN users u ON o.user_id = u.id
            ORDER BY o.order_date DESC
            """
        )
        orders = cursor.fetchall()
        
        if not orders:
            print("No orders found.")
        else:
            print("\n===== All Orders =====")
            orders_table = []
            for order in orders:
                orders_table.append([
                    order[0],
                    order[1],
                    order[2],
                    order[3],
                    f"${order[4]:.2f}",
                    order[5]
                ])
            
            print(tabulate(orders_table, headers=["Order ID", "Customer", "Date", "Status", "Amount", "Est. Delivery"], tablefmt="simple"))
            
           
            order_id = input("\nEnter order ID to view details (0 to cancel): ")
            if order_id != '0':
                self.view_order_details(int(order_id))
        
        conn.close()
    
    def view_order_details(self, order_id):
        conn = sqlite3.connect('dollmart.db')
        cursor = conn.cursor()
        
        
        cursor.execute("SELECT id FROM orders WHERE id = ?", (order_id,))
        if not cursor.fetchone():
            print("Order not found.")
            conn.close()
            return
        
        
        cursor.execute(
            """
            SELECT p.name, oi.quantity, oi.price, (oi.quantity * oi.price) as subtotal
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = ?
            """,
            (order_id,)
        )
        items = cursor.fetchall()
        
        print(f"\n===== Order #{order_id} Details =====")
        items_table = []
        for item in items:
            items_table.append([item[0], item[1], f"${item[2]:.2f}", f"${item[3]:.2f}"])
        
        print(tabulate(items_table, headers=["Product", "Quantity", "Unit Price", "Subtotal"], tablefmt="simple"))
        
        conn.close()
    
    def customer_management(self):
        while True:
            print("\n===== Customer Management =====")
            print("1. View All Customers")
            print("2. View Customer Details")
            print("3. Back to Main Menu")
            
            choice = input("\nEnter your choice: ")
            
            if choice == '1':
                self.view_all_customers()
            elif choice == '2':
                self.view_customer_details()
            elif choice == '3':
                return
            else:
                print("Invalid choice. Please try again.")
    
    def view_all_customers(self):
        conn = sqlite3.connect('dollmart.db')
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT id, username, is_retail, orders_count, registration_date
            FROM users
            WHERE role = 'customer'
            ORDER BY registration_date DESC
            """
        )
        customers = cursor.fetchall()
        
        if not customers:
            print("No customers found.")
        else:
            print("\n===== All Customers =====")
            customers_table = []
            for customer in customers:
                customer_type = "Retail Store" if customer[2] == 1 else "Individual"
                customers_table.append([
                    customer[0],
                    customer[1],
                    customer_type,
                    customer[3],
                    customer[4]
                ])
            
            print(tabulate(customers_table, headers=["ID", "Username", "Type", "Orders", "Registration Date"], tablefmt="simple"))
        
        conn.close()
    
    def view_customer_details(self):
        self.view_all_customers()
        
        try:
            customer_id = int(input("\nEnter customer ID to view details: "))
            
            conn = sqlite3.connect('dollmart.db')
            cursor = conn.cursor()
            
            
            cursor.execute("SELECT username, is_retail, orders_count, registration_date FROM users WHERE id = ? AND role = 'customer'", (customer_id,))
            customer = cursor.fetchone()
            
            if not customer:
                print("Customer not found.")
                conn.close()
                return
            
            print(f"\n===== Customer #{customer_id} Details =====")
            print(f"Username: {customer[0]}")
            print(f"Type: {'Retail Store' if customer[1] == 1 else 'Individual'}")
            print(f"Orders Count: {customer[2]}")
            print(f"Registration Date: {customer[3]}")
            
            
            cursor.execute(
                """
                SELECT id, order_date, status, total_amount
                FROM orders
                WHERE user_id = ?
                ORDER BY order_date DESC
                """,
                (customer_id,)
            )
            orders = cursor.fetchall()
            
            if orders:
                print("\nOrder History:")
                orders_table = []
                for order in orders:
                    orders_table.append([
                        order[0],
                        order[1],
                        order[2],
                        f"${order[3]:.2f}"
                    ])
                
                print(tabulate(orders_table, headers=["Order ID", "Date", "Status", "Amount"], tablefmt="simple"))
                
                
                cursor.execute(
                    """
                    SELECT id, code, discount_percentage, used
                    FROM coupons
                    WHERE user_id = ?
                    """,
                    (customer_id,)
                )
                coupons = cursor.fetchall()
                
                if coupons:
                    print("\nCoupons:")
                    coupons_table = []
                    for coupon in coupons:
                        status = "Used" if coupon[3] == 1 else "Available"
                        coupons_table.append([
                            coupon[0],
                            coupon[1],
                            f"{coupon[2]}%",
                            status
                        ])
                    
                    print(tabulate(coupons_table, headers=["ID", "Code", "Discount", "Status"], tablefmt="simple"))
                else:
                    print("\nNo coupons available for this customer.")
            else:
                print("\nNo order history found for this customer.")
            
            conn.close()
            
        except ValueError:
            print("Invalid input. Please enter a numeric customer ID.")


def login():
    """Authenticate user and return User object if successful"""
    username = input("Enter username: ")
    password = input("Enter password: ")
    
    conn = sqlite3.connect('dollmart.db')
    cursor = conn.cursor()
    
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    cursor.execute("SELECT id, role, is_retail, orders_count FROM users WHERE username = ? AND password_hash = ?", 
                  (username, password_hash))
    user = cursor.fetchone()
    
    conn.close()
    
    if user:
        user_id, role, is_retail, orders_count = user
        if role == "admin":
            return Admin(user_id, username)
        else:
            return Customer(user_id, username, is_retail, orders_count)
    else:
        print("Invalid username or password.")
        return None



def register():
    """Register a new customer account with improved welcome coupon generation"""
    username = input("Enter username: ")
    password = input("Enter password: ")
    
    
    customer_type = input("Are you a retail store? (y/n): ").lower()
    is_retail = 1 if customer_type == 'y' else 0
    
    conn = sqlite3.connect('dollmart.db')
    cursor = conn.cursor()
    
    
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        print("Username already exists. Please choose another one.")
        conn.close()
        return None
    
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    registration_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash, role, is_retail, registration_date) VALUES (?, ?, ?, ?, ?)",
            (username, password_hash, "customer", is_retail, registration_date)
        )
        
        conn.commit()
        user_id = cursor.lastrowid
        
        print("Registration successful! You can now login.")
        
        
        coupon_id, coupon_code = create_coupon(user_id, 10, "WELCOME", existing_conn=conn)
        
        print(f"Welcome gift! You've received a 10% off coupon: {coupon_code}")
        print(f"Use Coupon ID: {coupon_id} during checkout to apply this discount.")
        
        conn.commit()
        conn.close()
        return Customer(user_id, username, is_retail)
    
    except sqlite3.Error as e:
        print(f"Error during registration: {e}")
        conn.close()
        return None

def main():
    
    setup_database()
    
    while True:
        print("\n===== Welcome to DollMart =====")
        print("1. Login")
        print("2. Register")
        print("3. Exit")
        
        choice = input("\nEnter your choice: ")
        
        if choice == '1':
            user = login()
            if user:
                user.show_menu()
        elif choice == '2':
            user = register()
            if user:
                user.show_menu()
        elif choice == '3':
            print("Thank you for using DollMart. Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()