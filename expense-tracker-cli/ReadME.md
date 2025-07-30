# 🧾 Expense Tracker CLI

A simple command-line interface (CLI) application to manage your personal finances. Built as part of the roadmap.sh backend development journey, this project helps reinforce core backend concepts like CLI design, file handling, and data persistence.

Project URL : https://roadmap.sh/projects/expense-tracker

GitHub URL : https://github.com/Purvee90/Backend-Projects/tree/main/expense-tracker-cli

## 📌 Project Overview

This CLI tool allows users to:
- Add, update, and delete expenses
- View all expenses
- Get summaries of total expenses
- View monthly summaries
- Filter expenses by category

The goal is to build a practical tool while learning how to structure backend logic and interact with the filesystem and databases.

## ✨ Features

- `add`: Add an expense with description and amount
- `update`: Modify an existing expense
- `delete`: Remove an expense by ID
- `list`: Display all recorded expenses
- `summary`: Show total expenses
- `summary --month`: Show expenses for a specific month

### 🔗 Enhancements

- **Streamlit Frontend**: A user-friendly web interface built using Streamlit to visualize and interact with your expenses.
- **SQL Database Integration**: Persistent storage using SQLite for reliable and scalable data management.
- **Unit Testing**: Core functionalities are covered with unit tests to ensure robustness and maintainability.

## 🛠 Installation

```bash
git clone https://github.com/your-username/expense-tracker-cli.git
cd expense-tracker-cli
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
pip install -r requirements.txt
