# Restaurant Management System

# Assumptions:
*only customer registers the manager has fixed 
          username:manager
          password:manager123
*no constraint on any user detail(no domain constraints)
*the restaurant contains infinite amount of each item on the menu
*there are two statuses for order If it is a takeaway-processing,delivered
*there are two statuses for order If it is a homedelivery-out for delivery,delivered
*The agents are automatically assigned based on the availability (id starts from 2)
*no agent for takeaway
*there are 5 agents for this restaurant
*if an order comes when all 5 agents are occupied then the order istaken but it will wait (time left=N/A)


## Overview
This project is a Restaurant Management System that allows customers to place orders, managers to view and manage orders, and delivery agents to handle deliveries. The system uses SQLite for the database and Python for the backend logic.

## Setup Instructions
**Manually add src/ to Python’s path:sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
(add this on top of the test.py)

**delete if the database already exists
## Running the Application
To run the application, execute the following command:
```sh
python3 restaurant_management.py
```

## Running Unit Tests
To run the unit tests, execute the following command:
```sh
python3 -m unittest discover -s testcases

```

## Test Cases
The test cases cover the following functionalities:
- **User registration and login:**
  - `test_register_user`: Tests if a new user can be registered.
  - `test_register_user_existing_username`: Tests if registering with an existing username raises an error.
  - `test_login`: Tests if a user can log in with valid credentials.
  - `test_login_invalid_credentials`: Tests if logging in with invalid credentials returns `None`.

- **Placing orders:**
  - `test_place_order`: Tests if an order can be placed successfully.
  - `test_place_order_empty_items`: Tests if placing an order with empty items raises a `ValueError`.

- **Viewing order status and history:**
  - `test_view_order_status`: Tests if the order status can be viewed.
  - `test_view_order_history`: Tests if the order history can be viewed.

- **Viewing incoming orders and delivery agents:**
  - `test_view_incoming_orders`: Tests if incoming orders can be viewed by the manager.
  - `test_view_delivery_agents`: Tests if delivery agents can be viewed by the manager.

- **Assigning delivery agents and updating order statuses:**
  - `test_view_assigned_orders`: Tests if assigned orders can be viewed by the delivery agent.
  - `test_update_order_statuses`: Tests if order statuses can be updated.
  - `test_assign_delivery_agent`: Tests if a delivery agent can be assigned to an order.

- **Calculating estimated preparation and delivery times:**
  - `test_calculate_estimated_time`: Tests if the estimated preparation and delivery times can be calculated for home delivery.
  - `test_calculate_estimated_time_takeaway`: Tests if the estimated preparation time can be calculated for takeaway.

Each test case ensures that the respective functionality works as expected and handles edge cases appropriately.

## Notes
- The database is initialized with default menu items, an admin user, a manager, and delivery agents.
- The system uses threading to update order statuses periodically.
- The application uses the `tabulate` library to display data in a tabular format.


<!-- ......................................................................................... -->

# Restaurant Management System

## Software Specifications

### Overview
The Restaurant Management System is designed to streamline the operations of a restaurant, including order management, menu management, and delivery tracking. The system supports multiple user roles, including customers, restaurant managers, and delivery agents.

### Technologies Used
- **Programming Language:** Python
- **Database:** SQLite
- **Libraries:** `os`, `sqlite3`, `time`, `datetime`, `random`, `tabulate`, `threading`, `getpass`

### Database Schema
1. **Users Table**
   - `id`: INTEGER PRIMARY KEY AUTOINCREMENT
   - `username`: TEXT UNIQUE NOT NULL
   - `password`: TEXT NOT NULL
   - `role`: TEXT NOT NULL
   - `contact`: TEXT
   - `address`: TEXT

2. **Menu Table**
   - `id`: INTEGER PRIMARY KEY AUTOINCREMENT
   - `name`: TEXT NOT NULL
   - `price`: REAL NOT NULL
   - `preparation_time`: INTEGER NOT NULL

3. **Orders Table**
   - `id`: INTEGER PRIMARY KEY AUTOINCREMENT
   - `customer_id`: INTEGER NOT NULL
   - `order_time`: TIMESTAMP NOT NULL
   - `status`: TEXT NOT NULL
   - `delivery_type`: TEXT NOT NULL
   - `address`: TEXT
   - `total_amount`: REAL NOT NULL
   - `estimated_ready_time`: TIMESTAMP
   - `estimated_delivery_time`: TIMESTAMP
   - `delivery_agent_id`: INTEGER
   - FOREIGN KEY (`customer_id`) REFERENCES `users`(`id`)
   - FOREIGN KEY (`delivery_agent_id`) REFERENCES `users`(`id`)

4. **OrderItems Table**
   - `id`: INTEGER PRIMARY KEY AUTOINCREMENT
   - `order_id`: INTEGER NOT NULL
   - `menu_item_id`: INTEGER NOT NULL
   - `quantity`: INTEGER NOT NULL
   - FOREIGN KEY (`order_id`) REFERENCES `orders`(`id`)
   - FOREIGN KEY (`menu_item_id`) REFERENCES `menu`(`id`)

5. **DeliveryAgents Table**
   - `id`: INTEGER PRIMARY KEY
   - `status`: TEXT NOT NULL
   - `current_order_id`: INTEGER
   - FOREIGN KEY (`id`) REFERENCES `users`(`id`)
   - FOREIGN KEY (`current_order_id`) REFERENCES `orders`(`id`)

### User Roles
- **Customer:** Can register, login, view menu, place orders, track current orders, and view order history.
- **Restaurant Manager:** Can view incoming orders, view delivery agents, and manage the restaurant operations.
- **Delivery Agent:** Can view assigned orders and track delivery status.

## Use Cases

### 1. Customer Use Cases

#### 1.1 Register
- **Use Case ID:** UC-001
- **Actors:** Customer
- **Preconditions:** None
- **Main Flow:**
  1. Customer provides username, password, contact number, and address.
  2. System validates the input and creates a new customer account.
  3. System confirms successful registration.
- **Alternate Flows:**
  - 1a. Username already exists: System prompts the customer to choose a different username.
- **Postconditions:** Customer account is created and stored in the database.

#### 1.2 Login
- **Use Case ID:** UC-002
- **Actors:** Customer
- **Preconditions:** Customer must have a registered account.
- **Main Flow:**
  1. Customer provides username and password.
  2. System validates the credentials.
  3. System grants access to the customer.
- **Alternate Flows:**
  - 2a. Invalid credentials: System prompts the customer to re-enter username and password.
- **Postconditions:** Customer is logged in and can access the system.

#### 1.3 View Menu
- **Use Case ID:** UC-003
- **Actors:** Customer
- **Preconditions:** Customer must be logged in.
- **Main Flow:**
  1. Customer requests to view the menu.
  2. System retrieves and displays the list of available menu items with prices.
- **Postconditions:** Customer views the menu.

#### 1.4 Place Order
- **Use Case ID:** UC-004
- **Actors:** Customer
- **Preconditions:** Customer must be logged in.
- **Main Flow:**
  1. Customer selects menu items and specifies quantities.
  2. Customer chooses delivery type (Home Delivery or Takeaway).
  3. System calculates the total amount and estimated times.
  4. System creates a new order and stores it in the database.
  5. System confirms successful order placement.
- **Alternate Flows:**
  - 2a. Invalid item selection: System prompts the customer to select valid menu items.
- **Postconditions:** Order is created and stored in the database.

#### 1.5 Track Current Orders
- **Use Case ID:** UC-005
- **Actors:** Customer
- **Preconditions:** Customer must be logged in and have active orders.
- **Main Flow:**
  1. Customer requests to track current orders.
  2. System retrieves and displays the status of active orders.
- **Postconditions:** Customer views the status of active orders.

#### 1.6 View Order History
- **Use Case ID:** UC-006
- **Actors:** Customer
- **Preconditions:** Customer must be logged in and have past orders.
- **Main Flow:**
  1. Customer requests to view order history.
  2. System retrieves and displays the list of past orders.
- **Postconditions:** Customer views the order history.

### 2. Restaurant Manager Use Cases

#### 2.1 Login
- **Use Case ID:** UC-007
- **Actors:** Restaurant Manager
- **Preconditions:** Manager must have a registered account.
- **Main Flow:**
  1. Manager provides username and password.
  2. System validates the credentials.
  3. System grants access to the manager.
- **Alternate Flows:**
  - 2a. Invalid credentials: System prompts the manager to re-enter username and password.
- **Postconditions:** Manager is logged in and can access the system.

#### 2.2 View Incoming Orders
- **Use Case ID:** UC-008
- **Actors:** Restaurant Manager
- **Preconditions:** Manager must be logged in.
- **Main Flow:**
  1. Manager requests to view incoming orders.
  2. System retrieves and displays the list of incoming orders with status filters.
- **Postconditions:** Manager views the list of incoming orders.

#### 2.3 View Delivery Agents
- **Use Case ID:** UC-009
- **Actors:** Restaurant Manager
- **Preconditions:** Manager must be logged in.
- **Main Flow:**
  1. Manager requests to view delivery agents.
  2. System retrieves and displays the list of delivery agents with their current status and assignments.
- **Postconditions:** Manager views the list of delivery agents.

### 3. Delivery Agent Use Cases

#### 3.1 Login
- **Use Case ID:** UC-010
- **Actors:** Delivery Agent
- **Preconditions:** Delivery agent must have a registered account.
- **Main Flow:**
  1. Delivery agent provides username and password.
  2. System validates the credentials.
  3. System grants access to the delivery agent.
- **Alternate Flows:**
  - 2a. Invalid credentials: System prompts the delivery agent to re-enter username and password.
- **Postconditions:** Delivery agent is logged in and can access the system.

#### 3.2 View Assigned Orders
- **Use Case ID:** UC-011
- **Actors:** Delivery Agent
- **Preconditions:** Delivery agent must be logged in and have assigned orders.
- **Main Flow:**
  1. Delivery agent requests to view assigned orders.
  2. System retrieves and displays the list of assigned orders with their status.
- **Postconditions:** Delivery agent views the list of assigned orders.

### 4. System Use Cases

#### 4.1 Update Order Statuses
- **Use Case ID:** UC-012
- **Actors:** System
- **Preconditions:** Orders must exist in the database.
- **Main Flow:**
  1. System periodically checks the current time.
  2. System updates the status of orders based on the current time and estimated times.
- **Postconditions:** Order statuses are updated in the database.

#### 4.2 Assign Delivery Agent
- **Use Case ID:** UC-013
- **Actors:** System
- **Preconditions:** Home delivery orders must exist in the database.
- **Main Flow:**
  1. System identifies available delivery agents.
  2. System assigns an available delivery agent to a new home delivery order.
- **Postconditions:** Delivery agent is assigned to the order.
<!-- <----------------------------------------------------------------------------------------------------------------------------------------------> 
# DollMart Application Documentation


# Assumptions

*in search product the system fetches all products that contains that substring,need not start from beginning
*in update products if you do not fill a field it stays the old value
*no user will have username as admin and password as admin123
*admin has fixed username-admin and password admin123
## Setup Instructions

**Manually add src/ to Python’s path:sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
(add this on top of the test_dollmart.py)

**run from Q3 folder
**delete if the database already exists
## Running the Application
go to src folder
To run the application, execute the following command:
```sh
python3 dollmart.py
```

## Running Unit Tests
To run the unit tests, execute the following command:
```sh
pytest testcases/test_dollmart.py

```


## System Overview

DollMart is a Python-based inventory management system that allows both retail and individual customers to browse products, place orders, and manage their shopping experience, while providing administrators with tools to manage products, orders, and customers.

## Database Schema

The system uses SQLite with the following tables:

### Users
- `id`: INTEGER PRIMARY KEY
- `username`: TEXT UNIQUE NOT NULL
- `password_hash`: TEXT NOT NULL
- `role`: TEXT NOT NULL
- `is_retail`: INTEGER NOT NULL
- `orders_count`: INTEGER DEFAULT 0
- `registration_date`: TEXT

### Products
- `id`: INTEGER PRIMARY KEY
- `name`: TEXT NOT NULL
- `category`: TEXT NOT NULL
- `price`: REAL NOT NULL
- `stock`: INTEGER NOT NULL
- `bulk_discount`: REAL DEFAULT 0

### Orders
- `id`: INTEGER PRIMARY KEY
- `user_id`: INTEGER NOT NULL (FOREIGN KEY to users.id)
- `order_date`: TEXT NOT NULL
- `status`: TEXT NOT NULL
- `total_amount`: REAL NOT NULL
- `estimated_delivery`: TEXT

### Order Items
- `order_id`: INTEGER NOT NULL (FOREIGN KEY to orders.id)
- `product_id`: INTEGER NOT NULL (FOREIGN KEY to products.id)
- `quantity`: INTEGER NOT NULL
- `price`: REAL NOT NULL
- PRIMARY KEY (order_id, product_id)

### Coupons
- `id`: INTEGER PRIMARY KEY
- `user_id`: INTEGER NOT NULL (FOREIGN KEY to users.id)
- `code`: TEXT NOT NULL
- `discount_percentage`: REAL NOT NULL
- `used`: INTEGER DEFAULT 0

## Dependencies

- Python 3.x
- SQLite3 (built-in Python library)
- tabulate (for formatted table display)
- Standard Python libraries:
  - os
  - datetime
  - random
  - time
  - hashlib
  - uuid
  - abc (for abstract base classes)

## System Flow

1. **Application Initialization**
   - Database setup and creation of necessary tables
   - Sample data initialization if tables are empty
   - Default admin user creation

2. **Main Menu Flow**
   - User presented with Login/Register/Exit options
   - Authentication or registration process
   - Role-based menu display (Admin vs Customer)

3. **Customer Flow**
   - Browse products by category
   - Search for specific products
   - Manage shopping cart
   - Place orders with coupon application
   - View order history and details
   - Check available coupons

4. **Admin Flow**
   - Product management (view, add, update, delete)
   - Order management (view all orders, view order details)
   - Customer management (view all customers, view customer details)

5. **Order Processing Flow**
   - Orders are created with "Processing" status
   - Status automatically updates based on elapsed time
   - Loyalty coupons generated based on order count

## Functional Components

### Database Management
- `setup_database()`: Initializes SQLite database with tables and sample data

### Order Status Management
- `update_order_statuses()`: Automatically updates order statuses based on elapsed time

### Coupon Management
- `generate_coupon_code()`: Creates unique coupon codes
- `create_coupon()`: Creates coupon records in the database
- `apply_coupon()`: Applies coupon discounts to orders

### User Authentication and Management
- `login()`: Authenticates users and returns appropriate User object
- `register()`: Creates new customer accounts with welcome coupons

### User Classes
- `User`: Abstract base class for all user types
- `Customer`: Handles customer-specific functionality
- `Admin`: Handles administrator-specific functionality

## Detailed Function Documentation

### Database Setup and Utilities

#### `setup_database()`
- Creates the database tables if they don't exist
- Initializes a default admin user
- Populates the products table with sample data if empty

#### `update_order_statuses()`
- Updates order statuses based on time elapsed since order creation
- Processing -> Out for Delivery -> Delivered

### Coupon Management

#### `generate_coupon_code(user_id, type_prefix)`
- Generates a unique coupon code based on user ID and coupon type
- Returns a formatted coupon code string

#### `create_coupon(user_id, discount_percentage, type_prefix="COUPON", existing_conn=None)`
- Creates a new coupon for a user
- Returns the coupon ID and code

#### `apply_coupon(user_id, coupon_id, total_amount)`
- Applies a coupon to the total order amount
- Returns success status, new total, discount amount, and coupon details

### User Authentication

#### `login()`
- Authenticates user credentials
- Returns appropriate User object based on role

#### `register()`
- Creates a new customer account
- Generates a welcome coupon
- Returns a new Customer object

### Customer Functionality

#### `Customer.browse_products()`
- Shows products by category
- Allows adding products to cart

#### `Customer.search_products()`
- Searches for products by name
- Allows adding products to cart

#### `Customer.add_to_cart(product_id, quantity)`
- Adds products to the shopping cart

#### `Customer.view_cart()`
- Displays cart contents with prices and quantities
- Shows bulk discount if applicable

#### `Customer.place_order()`
- Processes order placement with coupon application
- Updates product stock
- Generates loyalty coupons
- Updates order status

#### `Customer.view_order_history()`
- Shows past orders with status information

#### `Customer.view_order_details(order_id)`
- Shows details of specific orders

#### `Customer.check_coupons()`
- Displays available and used coupons

### Admin Functionality

#### `Admin.product_management()`
- Menu for managing products

#### `Admin.view_all_products()`
- Displays all products in the system

#### `Admin.add_product()`
- Creates new product records

#### `Admin.update_product()`
- Modifies existing product details

#### `Admin.delete_product()`
- Removes products if not part of existing orders

#### `Admin.order_management()`
- Menu for managing orders

#### `Admin.view_all_orders()`
- Shows all orders in the system

#### `Admin.view_order_details(order_id)`
- Shows detailed information about specific orders

#### `Admin.customer_management()`
- Menu for managing customers

#### `Admin.view_all_customers()`
- Displays all customer accounts

#### `Admin.view_customer_details()`
- Shows detailed information about specific customers

## Main Application Flow

The application follows this execution flow:

1. `main()` function initializes the database
2. Main menu prompts for login/register/exit
3. User authenticates or registers
4. Role-specific menu is displayed
5. User performs operations within their permission scope
6. System updates order statuses and stock levels accordingly
7. User logs out and returns to main menu

The system implements object-oriented design with abstract base classes and inheritance to separate admin and customer functionality while maintaining a consistent interface through the User abstract class.

## Special Features

1. **Retail Customer Discounts**: Bulk discounts for retail stores on large orders
2. **Automatic Status Updates**: Order status progresses automatically based on time
3. **Coupon System**: Welcome coupons for new users and loyalty coupons for repeat customers
4. **Database Locking Prevention**: Proper connection handling to prevent SQLite database locks



<!-- <---------------------------------------------------------------------------------------------------------------------------------------> 
# Test Cases Documentation

## Overview

This document provides an overview of the test cases written for the `dollmart` application, including the purpose of each test case and instructions on how to run the unit tests.

## Test Cases

### 1. `test_generate_coupon_code`
- **Purpose**: To verify that the `generate_coupon_code` function generates a coupon code with the correct prefix and length.
- **Assertions**: 
  - The coupon code starts with the specified prefix.
  - The length of the coupon code is 13 characters.

### 2. `test_create_coupon`
- **Purpose**: To test the creation of a coupon and ensure it is correctly stored in the database.
- **Assertions**:
  - The coupon is not `None`.
  - The coupon code matches the generated code.
  - The discount percentage is correctly stored.

### 3. `test_apply_invalid_coupon`
- **Purpose**: To verify that applying an invalid coupon does not alter the total amount.
- **Assertions**:
  - The application of the coupon is unsuccessful.
  - The total amount remains unchanged.
  - The discount is zero.
  - The coupon code and percentage are `None`.

### 4. `test_apply_used_coupon`
- **Purpose**: To ensure that a used coupon cannot be applied again.
- **Assertions**:
  - The application of the coupon is unsuccessful.
  - The total amount remains unchanged.
  - The discount is zero.
  - The coupon code and percentage are `None`.

### 5. `test_register_user`
- **Purpose**: To test the registration of a new user.
- **Assertions**:
  - The user ID is not `None`.

### 6. `test_register_existing_user`
- **Purpose**: To verify that registering an existing user raises an `IntegrityError`.
- **Assertions**:
  - The second insertion raises an `IntegrityError`.

### 7. `test_login_user`
- **Purpose**: To test the login functionality for a valid user.
- **Assertions**:
  - The user is not `None`.

### 8. `test_login_invalid_user`
- **Purpose**: To verify that logging in with invalid credentials returns `None`.
- **Assertions**:
  - The user is `None`.

### 9. `test_customer_cart_operations`
- **Purpose**: To test adding items to the cart and updating their quantities.
- **Assertions**:
  - The quantity of the item in the cart is correctly updated.

### 10. `test_customer_cart_invalid_product`
- **Purpose**: To ensure that adding an invalid product to the cart does not succeed.
- **Assertions**:
  - The invalid product is not in the cart.

### 11. `test_customer_place_order`
- **Purpose**: To test placing an order with items in the cart.
- **Assertions**:
  - The order count for the user is greater than zero.

### 12. `test_customer_place_order_empty_cart`
- **Purpose**: To verify that placing an order with an empty cart does not succeed.
- **Assertions**:
  - The cart remains empty.

### 13. `test_admin_view_all_products`
- **Purpose**: To test the admin's ability to view all products.
- **Assertions**:
  - The product count is greater than zero.

### 14. `test_admin_add_product`
- **Purpose**: To test adding a new product as an admin.
- **Assertions**:
  - The product ID is not `None`.

### 15. `test_admin_update_product`
- **Purpose**: To verify that an admin can update product details.
- **Assertions**:
  - The product name is updated correctly.

### 16. `test_admin_delete_product`
- **Purpose**: To test the deletion of a product by an admin.
- **Assertions**:
  - The product count for the deleted product ID is zero.

### 17. `test_apply_coupon_invalid_amount`
- **Purpose**: To ensure that applying a coupon to an invalid total amount does not succeed.
- **Assertions**:
  - The application of the coupon is unsuccessful.
  - The total amount remains unchanged.
  - The discount is zero.
  - The coupon code and percentage are `None`.

### 18. `test_register_user_with_existing_username`
- **Purpose**: To verify that registering a user with an existing username raises an `IntegrityError`.
- **Assertions**:
  - The user count for the existing username is one.
  - The second insertion raises an `IntegrityError`.

### 19. `test_login_user_with_wrong_password`
- **Purpose**: To ensure that logging in with the wrong password returns `None`.
- **Assertions**:
  - The user is `None`.

### 20. `test_customer_cart_remove_item`
- **Purpose**: To test removing an item from the cart.
- **Assertions**:
  - The item is removed from the cart.

### 21. `test_customer_cart_update_quantity`
- **Purpose**: To verify that updating the quantity of an item in the cart works correctly.
- **Assertions**:
  - The quantity of the item in the cart is updated correctly.

## Running the Tests

To run the unit tests, follow these steps:

1. Ensure you have `pytest` installed. If not, install it using:
   ```sh
   pip install pytest
   ```

2. Navigate to the directory containing the `testcases.py` file.

3. Run the tests using the following command:
   ```sh
   pytest testcases.py
   ```

This will execute all the test cases and provide a summary of the results.

<!-- <---------------------------------------------------------------------------------> 
# Gobblet Game
# Assumptions
2 the rewind part is a bit ambiguous(it is said to be in another version of the game)so no rewind