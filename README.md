Inventory and Order Management System

Project Overview

The Inventory and Order Management System is a full-stack application developed using a microservices architecture. It helps customers browse products, manage shopping carts, place orders, and make payments. Administrators can manage products, inventory, orders, customers, and sales reports.

Technologies Used

Frontend

- React.js
- Vite
- HTML5
- CSS3
- JavaScript
- Axios

Backend

- Python
- FastAPI
- SQLAlchemy
- SQLite
- JWT Authentication
- Role-Based Access Control

Additional Technologies

- RabbitMQ – Message communication
- Redis – Caching
- ReportLab – PDF report generation
- Postman – API testing
- Git and GitHub – Version control

Microservices Architecture

Service| Port
API Gateway| 8000
Auth Service| 8001
Product Service| 8002
Cart Service| 8003
Inventory Service| 8004
Order Service| 8005
Payment Service| 8006
Notification Service| 8007
Review Service| 8008
Coupon Service| 8009
Return Service| 8010
Analytics Service| 8011

Main Features

Customer Features

- Customer registration and login
- Browse products
- Add products to cart
- Place orders
- Make test payments
- View order history
- Receive notifications

Administrator Features

- Admin dashboard
- Manage products
- Manage inventory
- Manage orders
- Manage customers
- View sales analytics
- Generate PDF reports
- Manage notifications

Project Structure

inventory-order-management/
│
├── api-gateway/
├── auth-service/
├── product-service/
├── cart-service/
├── inventory-service/
├── order-service/
├── payment-service/
├── notification-service/
├── review-service/
├── coupon-service/
├── return-service/
├── analytics-service/
│
├── frontend/
├── shared/
├── scripts/
├── tests/
├── .gitignore
└── README.md

How to Run the Project

1. Clone the repository

git clone https://github.com/divyasrisudharani/Inventory-order-management-system.git

2. Open the project

cd Inventory-order-management-system

3. Backend Setup

Create and activate a virtual environment:

python -m venv venv

Windows:

venv\Scripts\activate

Install dependencies using the project's requirements file, if available:

pip install -r requirements.txt

Configure the required environment variables in local ".env" files. Never upload secrets to GitHub.

4. Frontend Setup

cd frontend
npm install
npm run dev

Open:

http://localhost:5173

5. Backend Services

Start the API Gateway and individual microservices using their configured FastAPI/Uvicorn commands and ports.

Configure SQLite, RabbitMQ, and Redis before starting the services.

Authentication and Security

- JWT-based authentication
- Access and refresh tokens
- Secure password hashing
- Role-based access control
- Protected API endpoints

Project Status

The project includes customer authentication, product management, cart operations, inventory management, order processing, simulated payments, notifications, customer management, analytics, and PDF reports.

Author

Divyasri Sudharani

GitHub: https://github.com/divyasrisudharani

License

This project is intended for educational and portfolio purposes.