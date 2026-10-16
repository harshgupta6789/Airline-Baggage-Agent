import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000/claims"

st.set_page_config(
    page_title="Airline Baggage Claim Agent",
    page_icon="✈️"
)

st.title("Airline Baggage Claim Agent")

pnr = st.text_input("PNR")
bag_tag = st.text_input("Bag Tag")

claim_type = st.selectbox(
    "Claim Type",
    ["DAMAGED_BAGGAGE", "LOST_BAGGAGE", "DELAYED_BAGGAGE"]
)

st.subheader("Expenses")

expenses_count = st.number_input(
    "Number of expenses",
    min_value=1,
    max_value=5,
    value=1
)

expenses = []

for i in range(expenses_count):
    st.markdown(f"**Expense {i+1}**")
    category = st.text_input("Category", key=f"category_{i}")
    amount = st.number_input(
        "Amount",
        min_value=0,
        step=10,
        key=f"amount_{i}"
    )

    expenses.append({"category": category, "amount": amount})

if st.button("Submit Claim"):
    payload = {
        "pnr": pnr,
        "bag_tag": bag_tag,
        "claim_type": claim_type,
        "expenses": expenses,
    }

    try:
        response = requests.post(
            API_URL,
            json=payload,
            timeout=60,
        )

        response.raise_for_status()

        result = response.json()

        st.subheader("Decision")

        st.write(f"**Decision:** {result.get('decision')}")
        st.write(f"**Reason:** {result.get('reason')}")

        if result.get("approved_amount") is not None:
            st.write(
                f"**Approved Amount:** "
                f"${result.get('approved_amount'):.2f}"
            )
        
        if result.get("confidence") is not None:
            st.write(
                f"**Confidence:** "
                f"{result.get('confidence'):.2f}"
            )

        if result.get("policy_source"):
            st.write(
                f"**Policy Used:** "
                f"{result.get('policy_source')}"
            )

    except requests.RequestException as exc:
        st.error(f"Request failed: {exc}")