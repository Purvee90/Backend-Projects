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


# Add Expense Section
st.header("Add Expense")
with st.form("add_expense_form"):
    description = st.text_input("Description")
    amount = st.number_input("Amount", min_value=0.0, format="%.2f")
    category = st.text_input("Category")
    submitted = st.form_submit_button("Add Expense")
    if submitted:
        payload = {"description": description, "amount": amount, "category": category}
        res = requests.post(f"{API_BASE}/add-expense", json=payload)
        if res.ok:
            st.success("Expense added successfully!")
        else:
            st.error(res.json().get("error", "Failed to add expense."))

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

# Summary Section
st.header("Monthly Summary")
summary_month = st.text_input("Enter Month for Summary (e.g., Jul25)")
if st.button("Get Summary"):
    res = requests.get(f"{API_BASE}/summary/{summary_month}")
    if res.ok:
        data = res.json()
        st.subheader(f"Summary for {data['month']}")
        st.write(f"**Total Expense:** ₹{data['total_expense']}")
        st.write(f"**Budget:** ₹{data['budget']}")
        st.write(f"**Remaining:** ₹{data['remaining']}")

        show_base64_image(data["budget_chart_base64"], "Budget vs Expense")
        show_base64_image(data["category_chart_base64"], "Category-wise Expenses")

    else:
        st.error(res.json().get("error", "Failed to fetch summary."))

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

#
# streamlit run app.py
