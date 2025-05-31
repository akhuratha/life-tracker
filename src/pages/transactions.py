import streamlit as st
from src.database.utils import db_ops, Account
import pandas as pd

st.subheader("Transactions")

# Create a new transaction
accounts = db_ops.list_accounts()
if accounts:
    account_ids = {account.id: account.name for account in accounts}
    with st.form("create_transaction"):
        st.write("## Create a new transaction")
        account_id = st.selectbox("Account", options=list(account_ids.keys()), format_func=lambda x: account_ids[x])
        amount = st.number_input("Amount")
        txn_date = st.date_input("Transaction Date")
        description = st.text_area("Description")
        tag_names = st.text_input("Tags (comma-separated)").split(',')
        tag_names = [tag.strip() for tag in tag_names]
        submitted = st.form_submit_button("Create Transaction")
        if submitted:
            account = db_ops.db.get(Account, account_id)
            transaction = db_ops.create_transaction(account, amount, txn_date, description, tag_names)
            st.success(f"Transaction '{transaction.id}' created successfully")
else:
    st.write("No accounts found. Please create an account first.")

# List all transactions
st.write("## Transactions List")
transactions = db_ops.list_transactions()
if transactions:
    data = []
    for transaction in transactions:
        account = db_ops.db.get(Account, transaction.account_id)
        tags = ', '.join([tag.name for tag in transaction.tags])
        data.append({
            'Account': account.name,
            'Amount': transaction.amount,
            'Date': transaction.date,
            'Description': transaction.description,
            'Tags': tags
        })
    df = pd.DataFrame(data)
    st.write(df)
else:
    st.write("No transactions found.")
