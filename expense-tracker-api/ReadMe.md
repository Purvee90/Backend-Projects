# 📊 Expense Tracker API

An API-based backend for tracking personal or organizational expenses, built using **Flask** and designed to integrate with a **Streamlit frontend**. This project is part of a broader roadmap to build full-stack and data-driven applications.

Project URL - https://roadmap.sh/projects/expense-tracker-api

## 🚀 Project Overview

The **Expense Tracker API** allows users to:
- Add, update, and delete expense entries
- Categorize expenses
- Retrieve summaries and analytics
- Integrate with a frontend dashboard (Streamlit)
- Store data securely using a database backend

## 🛠️ Technologies Used

- **Backend Framework**: Flask  
- **Frontend**: Streamlit (separate repo/project)  
- **Database**: SQLite / PostgreSQL (based on configuration)  
- **Authentication**: Token-based (optional)  
- **Deployment**: Localhost / Cloud-ready  

## 📦 Features Implemented

### ✅ Core Features
- **CRUD operations** for expenses
- **Category tagging** for better organization
- **Date-based filtering** (daily, weekly, monthly)
- **Summary endpoints** for total and category-wise expenses
- **API documentation** using Swagger or Postman

### 📈 Analytics
- Monthly and category-wise expense summaries
- Top spending categories
- Expense trends over time

### 🔐 Optional Enhancements
- Role-based access (admin/user)
- Export to CSV or Excel

## 🧭 Roadmap

This project is part of a larger roadmap:
1. ✅ **Backend API** (this repo)
2. ✅ **Streamlit Frontend** (dashboard and visualizations)
3. 🔜 **Data Science Module** (spending predictions, anomaly detection)
4. 🔜 **Cloud Deployment** (Docker + CI/CD)

## 📌 Setup Instructions

```bash
# Clone the repo
git clone https://github.com/Purvee90/expense-tracker-api.git
cd expense-tracker-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Run the app
python app.py

# # 📬 API Endpoints

| Method | Endpoint        | Description         |
|--------|-----------------|---------------------|
| GET    | `/expenses`     | List all expenses   |
| POST   | `/expenses`     | Add a new expense   |
| PUT    | `/expenses/<id>`| Update an expense   |
| DELETE | `/expenses/<id>`| Delete an expense   |
| GET    | `/summary`      | Get expense summary |


##📊 Frontend Integration
The Streamlit frontend connects to this API to display:

Interactive charts
Filters and search
Expense entry forms



