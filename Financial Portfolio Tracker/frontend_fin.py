import streamlit as st
import pandas as pd
from datetime import datetime
from backend_fin import DatabaseManager

# Initialize the database manager
db = DatabaseManager()

# --- Page Configuration ---
st.set_page_config(layout="wide", page_title="Financial Portfolio Tracker")
st.title("💰 Personal Financial Portfolio Tracker")
st.write("---")

# --- Main Dashboard Section ---
st.header("📈 Portfolio Summary")

summary = db.get_portfolio_summary()
if summary:
    total_cost = summary.get('total_cost', 0)
    current_value = summary.get('current_value', 0)
    gain_loss = summary.get('gain_loss', 0)
    gain_loss_percent = summary.get('gain_loss_percent', 0)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Portfolio Value", f"${current_value:,.2f}")
    with col2:
        st.metric("Total Gain/Loss", f"${gain_loss:,.2f}", delta=f"{gain_loss_percent:,.2f}%")
    with col3:
        st.metric("Total Assets", summary.get('total_assets', 0))

    st.markdown("### Asset Allocation by Class")
    breakdown_data = summary.get('breakdown', [])
    if breakdown_data:
        breakdown_df = pd.DataFrame(breakdown_data)
        st.bar_chart(breakdown_df.set_index('asset_class'))
    else:
        st.info("No assets to display. Add some below!")

st.write("---")

# --- CRUD Operations Section ---
st.header("💼 Asset Management")
tab1, tab2 = st.tabs(["Add New Asset", "Update/Delete Asset"])

with tab1:
    st.subheader("Add New Asset")
    with st.form("add_asset_form", clear_on_submit=True):
        add_ticker = st.text_input("Ticker Symbol", placeholder="e.g., AAPL, TSLA")
        add_date = st.date_input("Purchase Date", datetime.now())
        add_shares = st.number_input("Number of Shares", min_value=0.0001, format="%.4f")
        add_cost = st.number_input("Total Cost Basis ($)", min_value=0.01, format="%.2f")
        add_class = st.selectbox("Asset Class", ["Equity", "Fixed Income", "Crypto", "Other"])
        submitted = st.form_submit_button("Add Asset")
        
        if submitted:
            if db.create_asset(add_ticker, add_date, add_shares, add_cost, add_class):
                st.success(f"Asset '{add_ticker}' added successfully!")
                st.cache_data.clear()
                st.rerun()
            else:
                st.error("Error adding asset.")

with tab2:
    st.subheader("Update/Delete Asset")
    assets_df = pd.DataFrame(db.read_assets())
    
    if not assets_df.empty:
        assets_df['display'] = assets_df['ticker'] + ' - ' + assets_df['asset_class']
        selected_asset = st.selectbox("Select Asset", assets_df['display'].tolist())
        selected_id = assets_df[assets_df['display'] == selected_asset]['asset_id'].iloc[0]
        
        asset_to_update = assets_df[assets_df['asset_id'] == selected_id].iloc[0]
        
        with st.form("update_delete_asset_form"):
            update_shares = st.number_input("Update Shares", value=float(asset_to_update['shares']), min_value=0.0001, format="%.4f")
            update_cost = st.number_input("Update Cost Basis", value=float(asset_to_update['cost_basis']), min_value=0.01, format="%.2f")
            
            col_update, col_delete = st.columns(2)
            with col_update:
                update_button = st.form_submit_button("Update Asset")
            with col_delete:
                delete_button = st.form_submit_button("Delete Asset")

            if update_button:
                if db.update_asset(selected_id, update_shares, update_cost):
                    st.success(f"Asset '{asset_to_update['ticker']}' updated successfully!")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("Error updating asset.")
            
            if delete_button:
                if db.delete_asset(selected_id):
                    st.success(f"Asset '{asset_to_update['ticker']}' deleted successfully!")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("Error deleting asset.")
    else:
        st.info("No assets to manage. Add one in the 'Add New Asset' tab.")

st.write("---")

# --- Transaction Logging Section ---
st.header("📝 Log Transactions")
assets_df = pd.DataFrame(db.read_assets())
if not assets_df.empty:
    assets_df['display'] = assets_df['ticker'] + ' - ' + assets_df['asset_class']
    selected_asset_trans = st.selectbox("Select Asset for Transaction", assets_df['display'].tolist())
    selected_id_trans = assets_df[assets_df['display'] == selected_asset_trans]['asset_id'].iloc[0]

    trans_type = st.selectbox("Transaction Type", ["Buy", "Sell", "Dividend"])
    trans_quantity = st.number_input("Quantity", min_value=0.0001, format="%.4f")
    trans_price = st.number_input("Price per Share/Unit ($)", min_value=0.01, format="%.2f")

    if st.button("Log Transaction"):
        total_amount = trans_quantity * trans_price
        if db.create_transaction(selected_id_trans, trans_type, trans_quantity, trans_price, total_amount):
            st.success("Transaction logged successfully!")
            st.cache_data.clear()
            st.rerun()
        else:
            st.error("Error logging transaction.")

