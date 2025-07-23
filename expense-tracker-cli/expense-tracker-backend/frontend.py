import streamlit as st
import requests
import base64
from PIL import Image
from io import BytesIO


API_BASE = "http://127.0.0.1:5000"

st.set_page_config(page_title="Expense Tracker", layout="centered")
st.title("💰 Expense Tracker")


def show_base64_image(base64_str, caption):
    image = Image.open(BytesIO(base64.b64decode(base64_str)))
    st.image(image, caption=caption)


# This section of the code in the Streamlit app is responsible for allowing users to add an expense.
# Here's a breakdown of what it does:
# Add Expense Section
st.header("Add Expense")
with st.form("add_expense_form"):
    description = st.text_input("Description")
    amount = st.number_input("Amount", min_value=0.0, format="%.2f")
    category = st.text_input("Category")
    date = st.date_input("Date", format="YYYY-MM-DD")
    submitted = st.form_submit_button("Add Expense")
    if submitted:
        payload = {
            "description": description,
            "amount": amount,
            "category": category,
            "date": date.strftime("%Y-%m-%d"),
        }
        res = requests.post(f"{API_BASE}/add-expense", json=payload)
        if res.ok:
            st.success("Expense added successfully!")
        else:
            st.error(res.json().get("error", "Failed to add expense."))


# Update Expense Section
st.header("Update Expense")
with st.form("update_expense_form"):
    update_id = st.number_input("Expense ID to Update", min_value=1, step=1)
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
        res = requests.put(f"{API_BASE}/update-expense/{update_id}", json=payload)
        if res.ok:
            st.success("Expense updated successfully!")
        else:
            st.error(res.json().get("error", "Failed to update expense."))

# Delete Expense Section
st.header("Delete Expense")
delete_id = st.number_input("Expense ID to Delete", min_value=1, step=1)
if st.button("Delete Expense"):
    res = requests.delete(f"{API_BASE}/delete-expense/{delete_id}")
    if res.ok:
        st.success("Expense deleted successfully!")
    else:
        st.error(res.json().get("error", "Failed to delete expense."))

# This section of the code in the Streamlit app is responsible for allowing users to set a budget for
# a specific month. Here's a breakdown of what it does:
# Set Budget Section
st.header("Set Budget")
with st.form("set_budget_form"):
    budget_month = st.text_input("Month (e.g., Jul25)")
    budget_amount = st.number_input("Budget Amount", min_value=0.0, format="%.2f")
    budget_submit = st.form_submit_button("Set Budget")
    if budget_submit:
        payload = {"month": budget_month, "amount": budget_amount}
        res = requests.post(f"{API_BASE}/set-budget", json=payload)
        if res.ok:
            st.success(res.json().get("message", "Budget set successfully!"))
        else:
            st.error(res.json().get("error", "Failed to set budget."))

# This section of the code in the Streamlit app is responsible for displaying the monthly summary of
# expenses. Here's a breakdown of what it does:
# Summary Section
st.header("Monthly Summary")
summary_month = st.text_input("Enter Month for Summary (e.g., Jul25)")

if st.button("Get Summary"):
    res = requests.get(f"{API_BASE}/summary/{summary_month}")
    if res.ok:
        try:
            data = res.json()
            st.subheader(f"Summary for {data['month']}")
            st.write(f"**Total Expense:** ₹{data['total_expense']}")
            st.write(f"**Budget:** ₹{data['budget']}")
            st.write(f"**Remaining:** ₹{data['remaining']}")

            if data.get("warning"):
                st.warning(data["warning"])

            # Display charts
            show_base64_image(data["budget_chart_base64"], "Budget vs Expense")
            show_base64_image(data["category_chart_base64"], "Category-wise Expenses")

        except Exception as e:
            st.error(f"Error parsing response: {e}")
    else:
        try:
            st.error(res.json().get("error", "Failed to fetch summary."))
        except Exception:
            st.error("Failed to fetch summary. Server returned non-JSON response.")


# Export CSV Section
st.header("Export Monthly Expenses")
export_month = st.text_input("Enter Month to Export (e.g., Jul25)")
if st.button("Export CSV"):
    res = requests.get(f"{API_BASE}/export/{export_month}")
    if res.ok:
        st.success("CSV file downloaded successfully.")
        st.download_button(
            "Download CSV", res.content, file_name=f"expenses_{export_month}.csv"
        )
    else:
        st.error(res.json().get("message", "Failed to export CSV."))

# View All Expenses for Selected Month
st.header("View All Expenses")
view_month = st.text_input("Enter Month to View Expenses (e.g., Jul25)")
if st.button("View Expenses"):
    res = requests.get(f"{API_BASE}/view-expenses/{view_month}")
    if res.ok:
        data = res.json()
        expenses = data.get("expenses", [])
        if expenses:
            import pandas as pd

            df = pd.DataFrame(expenses)
            st.dataframe(df, height=400)  # Scrollable table
        else:
            st.info("No expenses found for the selected month.")
    else:
        st.error(res.json().get("error", "Failed to fetch expenses."))

#
# streamlit run app.py
