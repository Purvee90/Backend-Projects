# 📊 Expense Tracker API

An API-based backend for tracking personal or organizational expenses, built using **Flask** and designed to integrate with a **Streamlit frontend**. 

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
- **Frontend**: Streamlit 
- **Database**: SQLite 
- **Authentication**: Token-based (JWT)  
- **Deployment**: Localhost

## 📦 Features Implemented

### ✅ Core Features
- **CRUD operations** for expenses
- **Category tagging** for better organization
- **Summary endpoints** for total and category-wise expenses

### 📈 Analytics
- Monthly and category-wise expense summaries
- Top spending categories

### 🔐 Planned Enhancements
- Role-based access (admin/user)
- Expense trends over time
- Date-based filtering (daily, weekly, monthly)

## 🧭 Roadmap

This project is part of a larger roadmap:
1. ✅ **Backend API** (this repo)
2. ✅ **Streamlit Frontend** (dashboard and visualizations)

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
Expense entry forms



