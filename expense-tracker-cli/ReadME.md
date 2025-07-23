# 🧾 Expense Tracker CLI

A simple command-line interface (CLI) application to manage your personal finances. Built as part of the [roadmap.sh backend development journey](https://roadmap.sh/projects/expense-tracker), this project helps reinforce core backend concepts like CLI design, file handling, and data persistence.

## 📌 Project Overview

This CLI tool allows users to:
- Add, update, and delete expenses
- View all expenses
- Get summaries of total expenses
- View monthly summaries
- Filter expenses by category

The goal is to build a practical tool while learning how to structure backend logic and interact with the filesystem.

## ✨ Features

- `add`: Add an expense with description and amount
- `update`: Modify an existing expense
- `delete`: Remove an expense by ID
- `list`: Display all recorded expenses
- `summary`: Show total expenses
- `summary --month`: Show expenses for a specific month
- Optional: Export to CSV, set monthly budgets, and filter by category

## 🛠 Installation

```bash
git clone https://github.com/your-username/expense-tracker-cli.git
cd expense-tracker-cli
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
pip install -r requirements.txt

