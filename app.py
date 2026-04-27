import streamlit as st
import pandas as pd
import plotly.express as px
import json

st.set_page_config(layout="wide", page_title="PhonePe Analytics")

# ================= LOAD DATA =================
txn_df = pd.read_csv("aggregated_transaction.csv", sep=";")
user_df = pd.read_csv("aggregated_user.csv", sep=";")
ins_df = pd.read_csv("aggregated_insurance.csv", sep=";")

def clean_cols(df):
    df.columns = df.columns.str.replace('"', '').str.strip()
    return df

txn_df = clean_cols(txn_df)
user_df = clean_cols(user_df)
ins_df = clean_cols(ins_df)

# ✅ FIX TYPES (NO .5 VALUES)
txn_df["Year"] = txn_df["Year"].astype(int)
txn_df["Quarter"] = txn_df["Quarter"].astype(int)

user_df["Year"] = user_df["Year"].astype(int)

ins_df["Year"] = ins_df["Year"].astype(int)
ins_df["Quarter"] = ins_df["Quarter"].astype(int)

# ================= GEO =================
with open("india_states.geojson") as f:
    geo = json.load(f)

# ================= STATE MAP =================
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
    return state_map.get(str(s).lower(), None)

# ================= UI =================
st.title("📊 PhonePe Analytics Dashboard")
st.caption("Transactions • Users • Insurance Insights Across India")
st.markdown("---")

# ================= SIDEBAR =================
years = sorted(txn_df["Year"].unique())
year = st.sidebar.selectbox("📅 Year", years)

state_list = sorted(txn_df["State"].unique())
selected_state = st.sidebar.selectbox("📍 Select State", state_list)

dark_mode = st.sidebar.toggle("🌙 Dark Mode")
template = "plotly_dark" if dark_mode else "plotly"

page = st.sidebar.selectbox("Navigation", ["🏠 Home","📊 Analysis"])

# ================= KPI =================
def growth(curr, prev):
    return 0 if prev == 0 else ((curr - prev) / prev) * 100

txn = txn_df[txn_df["Year"] == year]["Transaction_Amount"].sum()
usr = user_df[user_df["Year"] == year]["User_Count"].sum()
ins = ins_df[ins_df["Year"] == year]["Insurance_Amount"].sum()

prev = year - 1
txn_prev = txn_df[txn_df["Year"] == prev]["Transaction_Amount"].sum()
usr_prev = user_df[user_df["Year"] == prev]["User_Count"].sum()
ins_prev = ins_df[ins_df["Year"] == prev]["Insurance_Amount"].sum()

c1,c2,c3 = st.columns(3)
c1.metric("💰 Transactions", f"₹ {txn/1e7:.2f} Cr", f"{growth(txn,txn_prev):.1f}% YoY")
c2.metric("👥 Users", f"{usr/1e6:.2f} M", f"{growth(usr,usr_prev):.1f}% YoY")
c3.metric("🛡️ Insurance", f"₹ {ins/1e7:.2f} Cr", f"{growth(ins,ins_prev):.1f}% YoY")

# ================= INSIGHTS =================
def insight_txn(df):
    top = df.iloc[0]
    share = (top["Transaction_Amount"] / df["Transaction_Amount"].sum()) * 100
    st.success(f"🔍 {top['State']} contributes {share:.1f}% of total transactions.")

def insight_user(df):
    top = df.iloc[0]
    st.success(f"🔍 {top['Brand']} leads user adoption.")

def insight_ins(df):
    top = df.iloc[0]
    st.success(f"🔍 {top['State']} dominates insurance value.")

# ================= HOME =================
if page == "🏠 Home":

    df = txn_df[txn_df["Year"] == year]
    df = df.groupby("State")["Transaction_Amount"].sum().reset_index()
    df["State_clean"] = df["State"].apply(map_state)
    df = df.dropna()

    fig = px.choropleth(df, geojson=geo,
                        featureidkey="properties.NAME_1",
                        locations="State_clean",
                        color="Transaction_Amount",
                        color_continuous_scale="Blues")
    fig.update_layout(template=template)
    fig.update_geos(fitbounds="locations", visible=False)
    st.plotly_chart(fig, use_container_width=True)

    # ===== DRILLDOWN =====
    st.markdown("### 📍 State Deep Dive")

    state_df = txn_df[(txn_df["State"] == selected_state)]

    col1,col2 = st.columns(2)

    df = state_df.groupby("Transaction_Type")["Transaction_Amount"].sum().reset_index()
    fig = px.pie(df, names="Transaction_Type", values="Transaction_Amount", hole=0.4)
    fig.update_layout(template=template)
    col1.plotly_chart(fig, use_container_width=True)

    df = state_df.groupby("Quarter")["Transaction_Amount"].sum().reset_index()
    df["Quarter"] = df["Quarter"].astype(int)  # 🔥 FIX
    fig = px.bar(df, x="Quarter", y="Transaction_Amount")
    fig.update_xaxes(dtick=1)
    fig.update_layout(template=template)
    col2.plotly_chart(fig, use_container_width=True)

# ================= ANALYSIS =================
else:

    option = st.selectbox("Choose Analysis", ["Transactions","Users","Insurance"])

# ---------- TRANSACTIONS ----------
    if option=="Transactions":

        df = txn_df.groupby("Year")["Transaction_Amount"].sum().reset_index()

        fig = px.line(df,x="Year",y="Transaction_Amount",markers=True)
        fig.update_xaxes(dtick=1)
        fig.update_layout(template=template)
        st.plotly_chart(fig,use_container_width=True)

        df["Growth %"] = df["Transaction_Amount"].pct_change()*100
        fig = px.bar(df,x="Year",y="Growth %")
        fig.update_layout(template=template)
        st.plotly_chart(fig,use_container_width=True)

        df = txn_df.groupby("State")["Transaction_Amount"].sum().reset_index()\
            .sort_values("Transaction_Amount",ascending=False).head(10)

        fig = px.bar(df,x="Transaction_Amount",y="State",orientation="h")
        fig.update_layout(template=template)
        st.plotly_chart(fig,use_container_width=True)

        insight_txn(df)

# ---------- USERS ----------
    elif option=="Users":

        df = user_df.groupby("Year")["User_Count"].sum().reset_index()

        fig = px.line(df,x="Year",y="User_Count",markers=True)
        fig.update_xaxes(dtick=1)
        fig.update_layout(template=template)
        st.plotly_chart(fig,use_container_width=True)

        df = user_df.groupby("Brand")["User_Count"].sum().reset_index()\
            .sort_values("User_Count",ascending=False).head(10)

        fig = px.bar(df,x="Brand",y="User_Count")
        fig.update_layout(template=template)
        st.plotly_chart(fig,use_container_width=True)

        insight_user(df)

# ---------- INSURANCE ----------
    elif option=="Insurance":

        df = ins_df.groupby("Year")["Insurance_Amount"].sum().reset_index()

        fig = px.line(df,x="Year",y="Insurance_Amount",markers=True)
        fig.update_xaxes(dtick=1)
        fig.update_layout(template=template)
        st.plotly_chart(fig,use_container_width=True)

        df = ins_df.groupby("State")["Insurance_Amount"].sum().reset_index()\
            .sort_values("Insurance_Amount",ascending=False).head(10)

        fig = px.bar(df,x="Insurance_Amount",y="State",orientation="h")
        fig.update_layout(template=template)
        st.plotly_chart(fig,use_container_width=True)

        insight_ins(df)

# ================= DOWNLOAD =================
st.markdown("### 📥 Export Data")
st.download_button("Download Transactions CSV",
                   txn_df.to_csv(index=False),
                   file_name="transactions.csv")
