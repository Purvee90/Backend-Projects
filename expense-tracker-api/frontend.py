import streamlit as st
import requests
from datetime import date
import jwt

API_BASE = "http://127.0.0.1:5000"  # Update if deployed

st.set_page_config(page_title="Expense Tracker", layout="centered")
st.title("💰 Expense Tracker")

st.sidebar.title("User Authentication")

auth_mode = st.sidebar.radio("Choose Mode", ["Login", "Signup"])
username = st.sidebar.text_input("Username")
email = st.sidebar.text_input("Email") if auth_mode == "Signup" else None
password = st.sidebar.text_input("Password", type="password")
headers = {"Authorization": st.session_state.get("token", "")}

if st.sidebar.button(auth_mode):
    payload = {"username": username, "password": password}

    if auth_mode == "Signup":
        if email:
            payload["email"] = email
        else:
            st.sidebar.error("Email is required for signup.")
            st.stop()
        res = requests.post(f"{API_BASE}/signup", json=payload)
    else:
        res = requests.post(f"{API_BASE}/login", json=payload)

    if res.ok:
        data = res.json()
        st.sidebar.success(data.get("message", "Success"))
        if auth_mode == "Login":
            token = data.get("token")
            if token:
                st.session_state["token"] = token
                try:
                    decoded = jwt.decode(token, options={"verify_signature": False})
                    user_id = decoded.get("user_id")
                    if user_id is not None:
                        st.session_state["user_id"] = str(user_id)
                except Exception as e:
                    st.sidebar.error(f"Token decoding failed: {e}")
            else:
                st.sidebar.error("No token received from server.")
    else:
        st.sidebar.error(res.json().get("error", "Authentication failed"))


# if "user_id" in st.session_state:
#     st.sidebar.markdown(f"**Logged in as User ID:** {st.session_state['user_id']}")
if "token" not in st.session_state:
    st.warning("Please log in to access expense features.")
    st.stop()

# Add Expense
st.header("Add Expense")
with st.form("add_expense_form"):
    description = st.text_input("Description")
    amount = st.number_input("Amount", min_value=0.0, format="%.2f")
    category = st.selectbox(
        "Category",
        [
            "Groceries",
            "Leisure",
            "Electronics",
            "Utilities",
            "Clothing",
            "Health",
            "Others",
        ],
    )

    expense_date = st.date_input("Date", value=date.today())
    submitted = st.form_submit_button("Add Expense")
    if submitted:
        payload = {
            "description": description,
            "amount": amount,
            "category": category,
            "date": expense_date.strftime("%Y-%m-%d"),
        }
        try:
            res = requests.post(
                f"{API_BASE}/add-expense", json=payload, headers=headers
            )
            if res.ok:
                st.success(res.json()["message"])
            else:
                st.error(res.json().get("error", "Failed to add expense."))
        except Exception as e:
            st.error(f"Error: {e}")

# Update Expense
st.header("Update Expense")
with st.form("update_expense_form"):
    expense_id = st.number_input("Expense ID", min_value=1, step=1)
    new_description = st.text_input("New Description")
    new_amount = st.number_input("New Amount", min_value=0.0, format="%.2f")
    new_category = st.text_input("New Category")
    update_submit = st.form_submit_button("Update Expense")
    if update_submit:
        payload = {
            "description": new_description,
            "amount": new_amount,
            "category": new_category,
        }
        try:
            res = requests.put(
                f"{API_BASE}/update-expense/{expense_id}", json=payload, headers=headers
            )
            if res.ok:
                st.success(res.json()["message"])
            else:
                st.error(res.json().get("error", "Failed to update expense."))
        except Exception as e:
            st.error(f"Error: {e}")

# Delete Expense
st.header("Delete Expense")
delete_id = st.number_input("Expense ID to Delete", min_value=1, step=1)
if st.button("Delete Expense"):
    try:
        res = requests.delete(f"{API_BASE}/delete-expense/{delete_id}", headers=headers)
        if res.ok:
            st.success(res.json()["message"])
        else:
            st.error(res.json().get("error", "Failed to delete expense."))
    except Exception as e:
        st.error(f"Error: {e}")

# Set Budget
st.header("Set Budget")
with st.form("set_budget_form"):
    month = st.text_input("Month (e.g., Jul25)")
    amount = st.number_input("Budget Amount", min_value=0.0, format="%.2f")
    start_date = st.date_input("Start Date", value=date.today())
    end_date = st.date_input("End Date", value=date.today())
    budget_submit = st.form_submit_button("Set Budget")
    category = st.selectbox(
        "Category",
        [
            "Groceries",
            "Leisure",
            "Electronics",
            "Utilities",
            "Clothing",
            "Health",
            "Others",
        ],
    )
    if budget_submit:
        payload = {
            "month": month,
            "amount": amount,
            "category": category,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
        }
        try:
            res = requests.post(f"{API_BASE}/set-budget", json=payload, headers=headers)
            if res.ok:
                st.success(res.json()["message"])
            else:
                st.error(res.json().get("error", "Failed to set budget."))
        except Exception as e:
            st.error(f"Error: {e}")

# Charts Section
st.header("📊 Expense Charts")
selected_month = st.text_input("Enter Month for Charts (e.g., Jul25)")

col1, col2 = st.columns(2)

with col1:
    if st.button("Show Budget vs Expense Chart"):
        try:
            res = requests.get(
                f"{API_BASE}/budget-vs-expense-chart",
                params={"month": selected_month},
                headers=headers,
            )
            if res.ok:
                st.image(res.content, caption=f"Budget vs Expense for {selected_month}")
            else:
                st.error(res.json().get("error", "Failed to fetch chart."))
        except Exception as e:
            st.error(f"Error: {e}")

with col2:
    if st.button("Show Category-wise Expense Chart"):
        try:
            res = requests.get(
                f"{API_BASE}/category-expense-chart",
                params={"month": selected_month},
                headers=headers,
            )
            if res.ok:
                st.image(
                    res.content, caption=f"Category-wise Expenses for {selected_month}"
                )
            else:
                st.error(res.json().get("error", "Failed to fetch chart."))
        except Exception as e:
            st.error(f"Error: {e}")

# Export Expenses to CSV
st.header("📁 Export Expenses")
export_month = st.text_input("Enter Month to Export (e.g., Jul25)", key="export_month")

if st.button("Download CSV"):
    try:
        res = requests.get(
            f"{API_BASE}/export-expenses",
            params={"month": export_month},
            headers=headers,
        )
        if res.ok:
            st.download_button(
                label=f"Download expenses_{export_month}.csv",
                data=res.content,
                file_name=f"expenses_{export_month}.csv",
                mime="text/csv",
            )
        else:
            st.error(res.json().get("error", "Failed to export CSV."))
    except Exception as e:
        st.error(f"Error: {e}")
