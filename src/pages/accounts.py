import streamlit as st
from src.database.utils import db_ops, Account

st.subheader("Accounts")

# Create a new account
with st.form("create_account"):
    st.write("## Create a new account")
    name = st.text_input("Account Name")
    balance = st.number_input("Initial Balance")
    acc_type = st.text_input("Account Type")
    submitted = st.form_submit_button("Create Account")
    if submitted:
        account = db_ops.add_account(name, balance, acc_type)
        st.success(f"Account '{account.name}' created successfully")

# List all accounts
st.write("## Accounts List")
accounts = db_ops.list_accounts()
if accounts:
    for account in accounts:
        st.write(f"- {account.name} (Balance: {account.balance}, Type: {account.type})")
else:
    st.write("No accounts found.")

# Delete an account (optional)
with st.form("delete_account"):
    st.write("## Delete an account")
    account_ids = {account.id: account.name for account in accounts}
    account_to_delete = st.selectbox("Select an account to delete", options=list(account_ids.keys()), format_func=lambda x: account_ids[x])
    submitted = st.form_submit_button("Delete Account")
    if submitted:
        # Note: may want to add a confirmation step before deleting
        # For simplicity, we're directly deleting here
        db_ops.db.delete(db_ops.db.get(Account, account_to_delete))
        db_ops.db.commit()
        st.success(f"Account '{account_ids[account_to_delete]}' deleted successfully")