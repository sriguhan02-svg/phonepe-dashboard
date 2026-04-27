import streamlit as st
import pandas as pd
import plotly.express as px
import json

st.set_page_config(layout="wide", page_title="PhonePe Analytics")

# ---------------- LOAD DATA ----------------
txn_df = pd.read_csv("aggregated_transaction.csv")
user_df = pd.read_csv("aggregated_user.csv")
ins_df = pd.read_csv("aggregated_insurance.csv")

# ---------------- GEOJSON ----------------
with open("india_states.geojson") as f:
    geo = json.load(f)

# ---------------- STATE MAP ----------------
state_map = {
    'andaman-&-nicobar-islands': 'Andaman and Nicobar',
    'andhra-pradesh': 'Andhra Pradesh',
    'arunachal-pradesh': 'Arunachal Pradesh',
    'assam': 'Assam',
    'bihar': 'Bihar',
    'chandigarh': 'Chandigarh',
    'chhattisgarh': 'Chhattisgarh',
    'dadra-&-nagar-haveli-&-daman-&-diu': 'Dadra and Nagar Haveli and Daman and Diu',
    'delhi': 'Delhi',
    'goa': 'Goa',
    'gujarat': 'Gujarat',
    'haryana': 'Haryana',
    'himachal-pradesh': 'Himachal Pradesh',
    'jammu-&-kashmir': 'Jammu and Kashmir',
    'jharkhand': 'Jharkhand',
    'karnataka': 'Karnataka',
    'kerala': 'Kerala',
    'ladakh': 'Ladakh',
    'lakshadweep': 'Lakshadweep',
    'madhya-pradesh': 'Madhya Pradesh',
    'maharashtra': 'Maharashtra',
    'manipur': 'Manipur',
    'meghalaya': 'Meghalaya',
    'mizoram': 'Mizoram',
    'nagaland': 'Nagaland',
    'odisha': 'Odisha',
    'puducherry': 'Puducherry',
    'punjab': 'Punjab',
    'rajasthan': 'Rajasthan',
    'sikkim': 'Sikkim',
    'tamil-nadu': 'Tamil Nadu',
    'telangana': 'Telangana',
    'tripura': 'Tripura',
    'uttar-pradesh': 'Uttar Pradesh',
    'uttarakhand': 'Uttarakhand',
    'west-bengal': 'West Bengal'
}

def map_state(s):
    return state_map.get(s.lower(), None)

# ---------------- FILTERS ----------------
years = sorted(txn_df["Year"].unique())
quarters = [1,2,3,4]

year = st.sidebar.selectbox("📅 Year", years)
quarter = st.sidebar.selectbox("📊 Quarter", quarters)

# ---------------- KPI ----------------
txn = txn_df[txn_df["Year"] == year]["Transaction_Amount"].sum()
usr = user_df[user_df["Year"] == year]["User_Count"].sum()
ins = ins_df[ins_df["Year"] == year]["Insurance_Amount"].sum()

c1,c2,c3 = st.columns(3)
c1.metric("💰 Transactions", f"₹ {txn/1e7:.2f} Cr")
c2.metric("👥 Users", f"{usr/1e6:.2f} M")
c3.metric("🛡️ Insurance", f"₹ {ins/1e7:.2f} Cr")

# ---------------- NAV ----------------
page = st.sidebar.selectbox("Navigation", ["🏠 Home","📊 Analysis"])

# =================================================
# 🏠 HOME
# =================================================
if page == "🏠 Home":

    st.title("📊 India Transaction Heatmap")

    df = txn_df[(txn_df["Year"]==year) & (txn_df["Quarter"]==quarter)]
    df = df.groupby("State")["Transaction_Amount"].sum().reset_index()

    df["State_clean"] = df["State"].apply(map_state)
    df = df.dropna()

    fig = px.choropleth(
        df,
        geojson=geo,
        featureidkey="properties.NAME_1",
        locations="State_clean",
        color="Transaction_Amount",
        color_continuous_scale="Blues"
    )

    fig.update_geos(fitbounds="locations", visible=False)
    st.plotly_chart(fig, use_container_width=True)

# =================================================
# 📊 ANALYSIS
# =================================================
else:

    option = st.selectbox("Choose Analysis", ["Transactions","Users","Insurance"])

# ---------------- TRANSACTIONS ----------------
    if option=="Transactions":

        df = txn_df.groupby("Year")["Transaction_Amount"].sum().reset_index()
        df["Year"] = df["Year"].astype(int)

        fig = px.line(df,x="Year",y="Transaction_Amount",markers=True,title="Yearly Growth")
        fig.update_xaxes(dtick=1)
        st.plotly_chart(fig,use_container_width=True)

        df = txn_df.groupby("Quarter")["Transaction_Amount"].sum().reset_index()
        st.plotly_chart(px.bar(df,x="Quarter",y="Transaction_Amount",title="Quarter Trend"),use_container_width=True)

        df = txn_df.groupby("State")["Transaction_Amount"].sum().reset_index().sort_values("Transaction_Amount",ascending=False).head(10)
        st.plotly_chart(px.bar(df,x="Transaction_Amount",y="State",orientation="h",title="Top States"),use_container_width=True)

        df = txn_df.groupby("Transaction_Type")["Transaction_Amount"].sum().reset_index()
        st.plotly_chart(px.pie(df,names="Transaction_Type",values="Transaction_Amount",hole=0.4,title="Transaction Split"),use_container_width=True)

# ---------------- USERS ----------------
    elif option=="Users":

        df = user_df.groupby("Year")["User_Count"].sum().reset_index()
        df["Year"] = df["Year"].astype(int)

        fig = px.line(df,x="Year",y="User_Count",markers=True,title="User Growth")
        fig.update_xaxes(dtick=1)
        st.plotly_chart(fig,use_container_width=True)

        df = user_df.groupby("Brand")["User_Count"].sum().reset_index().sort_values("User_Count",ascending=False).head(10)
        st.plotly_chart(px.bar(df,x="Brand",y="User_Count",title="Top Brands"),use_container_width=True)

        df = user_df.groupby("Brand")["User_Percentage"].mean().reset_index()
        st.plotly_chart(px.pie(df,names="Brand",values="User_Percentage",hole=0.4,title="Brand Share"),use_container_width=True)

        df = user_df.groupby(["Year","Brand"])["User_Count"].sum().reset_index()
        df["Year"] = df["Year"].astype(int)

        top = df.groupby("Brand")["User_Count"].sum().nlargest(5).index
        df = df[df["Brand"].isin(top)].sort_values(["Brand","Year"])

        fig = px.line(df,x="Year",y="User_Count",color="Brand",markers=True,title="Top 5 Brand Trend")
        fig.update_xaxes(dtick=1)
        st.plotly_chart(fig,use_container_width=True)

# ---------------- INSURANCE ----------------
    elif option=="Insurance":

        df = ins_df.groupby("Year")["Insurance_Amount"].sum().reset_index()
        df["Year"] = df["Year"].astype(int)

        fig = px.line(df,x="Year",y="Insurance_Amount",markers=True,title="Growth")
        fig.update_xaxes(dtick=1)
        st.plotly_chart(fig,use_container_width=True)

        df = ins_df.groupby("State")["Insurance_Amount"].sum().reset_index().sort_values("Insurance_Amount",ascending=False).head(10)
        st.plotly_chart(px.bar(df,x="Insurance_Amount",y="State",orientation="h",title="Top States"),use_container_width=True)

        df = ins_df.groupby("Quarter")["Insurance_Amount"].sum().reset_index()
        st.plotly_chart(px.bar(df,x="Quarter",y="Insurance_Amount",title="Quarter Trend"),use_container_width=True)

        df = ins_df.groupby("State").agg({"Insurance_Count":"sum","Insurance_Amount":"sum"}).reset_index()
        st.plotly_chart(px.scatter(df,x="Insurance_Count",y="Insurance_Amount",size="Insurance_Amount",title="Count vs Amount"),use_container_width=True)

        df["avg"] = df["Insurance_Amount"]/df["Insurance_Count"]
        df = df.sort_values("avg",ascending=False).head(10)

        st.plotly_chart(px.bar(df,x="avg",y="State",orientation="h",title="Top 10 Avg Ticket Size"),use_container_width=True)
