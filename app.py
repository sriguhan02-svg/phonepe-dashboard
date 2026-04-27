import streamlit as st
import pandas as pd
import plotly.express as px
import json

st.set_page_config(layout="wide", page_title="PhonePe Analytics")

# ================= UI POLISH =================
st.markdown("""
<style>
.block-container {padding-top: 1rem; padding-bottom: 1rem;}
h1, h2, h3 {font-weight: 600;}
[data-testid="metric-container"] {
    background: #111;
    padding: 15px;
    border-radius: 12px;
    border: 1px solid #333;
}
</style>
""", unsafe_allow_html=True)

# ================= LOAD DATA =================
txn_df = pd.read_csv("aggregated_transaction.csv", sep=";")
user_df = pd.read_csv("aggregated_user.csv", sep=";")
ins_df = pd.read_csv("aggregated_insurance.csv", sep=";")

def clean(df):
    df.columns = df.columns.str.replace('"','').str.strip()
    return df

txn_df, user_df, ins_df = clean(txn_df), clean(user_df), clean(ins_df)


txn_df["Year"] = txn_df["Year"].astype(int)
txn_df["Quarter"] = txn_df["Quarter"].astype(int)
user_df["Year"] = user_df["Year"].astype(int)
ins_df["Year"] = ins_df["Year"].astype(int)
ins_df["Quarter"] = ins_df["Quarter"].astype(int)

# ================= GEO =================
with open("india_states.geojson") as f:
    geo = json.load(f)

state_map = {
    'andaman-&-nicobar-islands':'Andaman and Nicobar',
    'andhra-pradesh':'Andhra Pradesh','arunachal-pradesh':'Arunachal Pradesh',
    'assam':'Assam','bihar':'Bihar','chandigarh':'Chandigarh',
    'chhattisgarh':'Chhattisgarh',
    'dadra-&-nagar-haveli-&-daman-&-diu':'Dadra and Nagar Haveli and Daman and Diu',
    'delhi':'Delhi','goa':'Goa','gujarat':'Gujarat','haryana':'Haryana',
    'himachal-pradesh':'Himachal Pradesh','jammu-&-kashmir':'Jammu and Kashmir',
    'jharkhand':'Jharkhand','karnataka':'Karnataka','kerala':'Kerala',
    'ladakh':'Ladakh','lakshadweep':'Lakshadweep','madhya-pradesh':'Madhya Pradesh',
    'maharashtra':'Maharashtra','manipur':'Manipur','meghalaya':'Meghalaya',
    'mizoram':'Mizoram','nagaland':'Nagaland','odisha':'Odisha',
    'puducherry':'Puducherry','punjab':'Punjab','rajasthan':'Rajasthan',
    'sikkim':'Sikkim','tamil-nadu':'Tamil Nadu','telangana':'Telangana',
    'tripura':'Tripura','uttar-pradesh':'Uttar Pradesh',
    'uttarakhand':'Uttarakhand','west-bengal':'West Bengal'
}

def map_state(s):
    return state_map.get(str(s).lower(), None)

# ================= HEADER =================
st.markdown("## 📊 PhonePe Analytics Dashboard")
st.caption("Insights on Transactions, Users & Insurance across India")
st.markdown("---")

# ================= SIDEBAR =================
year = st.sidebar.selectbox("📅 Year", sorted(txn_df["Year"].unique()))
state = st.sidebar.selectbox("📍 State", sorted(txn_df["State"].unique()))
page = st.sidebar.selectbox("Navigation", ["🏠 Home","📊 Analysis"])
dark = st.sidebar.toggle("🌙 Dark Mode")
template = "plotly_dark" if dark else "plotly"

# ================= KPI =================
def growth(c,p): return 0 if p==0 else (c-p)/p*100

txn = txn_df[txn_df["Year"]==year]["Transaction_Amount"].sum()
usr = user_df[user_df["Year"]==year]["User_Count"].sum()
ins = ins_df[ins_df["Year"]==year]["Insurance_Amount"].sum()

prev = year-1
txn_p = txn_df[txn_df["Year"]==prev]["Transaction_Amount"].sum()
usr_p = user_df[user_df["Year"]==prev]["User_Count"].sum()
ins_p = ins_df[ins_df["Year"]==prev]["Insurance_Amount"].sum()

c1,c2,c3 = st.columns(3)
c1.metric("💰 Transactions", f"₹ {txn/1e7:.2f} Cr", f"{growth(txn,txn_p):.1f}%")
c2.metric("👥 Users", f"{usr/1e6:.2f} M", f"{growth(usr,usr_p):.1f}%")
c3.metric("🛡️ Insurance", f"₹ {ins/1e7:.2f} Cr", f"{growth(ins,ins_p):.1f}%")

# ================= HOME =================
if page=="🏠 Home":

File "/mount/src/phonepe-dashboard/app.py", line 99
  def clean_state(name):
  ^
IndentationError: expected an indented block after 'if' statement on line 95
    
    st.markdown("### 📍 State Drilldown")

    s_df = txn_df[txn_df["State"]==state]

    col1,col2 = st.columns(2)

    # Pie
    df = s_df.groupby("Transaction_Type")["Transaction_Amount"].sum().reset_index()
    fig = px.pie(df, names="Transaction_Type", values="Transaction_Amount", hole=0.5)
    fig.update_traces(textinfo='percent+label')
    fig.update_layout(template=template)
    col1.plotly_chart(fig, use_container_width=True)

    # Quarter
    df = s_df.groupby("Quarter")["Transaction_Amount"].sum().reset_index()
    df["Quarter"] = df["Quarter"].astype(int)

    fig = px.bar(df, x="Quarter", y="Transaction_Amount")
    fig.update_xaxes(tickvals=[1,2,3,4], ticktext=['Q1','Q2','Q3','Q4'])
    fig.update_layout(template=template)
    col2.plotly_chart(fig, use_container_width=True)

# ================= ANALYSIS =================
else:

    opt = st.selectbox("Choose", ["Transactions","Users","Insurance"])

# -------- TRANSACTIONS --------
    if opt=="Transactions":

        df = txn_df.groupby("Year")["Transaction_Amount"].sum().reset_index()

        fig = px.line(df, x="Year", y="Transaction_Amount", markers=True)
        fig.update_traces(line=dict(width=3))
        fig.update_xaxes(dtick=1)
        fig.update_layout(template=template)
        st.plotly_chart(fig, use_container_width=True)

        # Growth
        df["Growth %"] = df["Transaction_Amount"].pct_change()*100
        df["Growth %"] = df["Growth %"].fillna(0)

        fig = px.bar(df, x="Year", y="Growth %", text="Growth %")
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig.update_xaxes(dtick=1)
        fig.update_layout(template=template)
        st.plotly_chart(fig, use_container_width=True)

        # Top states
        df = txn_df.groupby("State")["Transaction_Amount"].sum().reset_index()\
            .sort_values("Transaction_Amount",ascending=False).head(10)

        fig = px.bar(df, x="Transaction_Amount", y="State", orientation="h", text_auto=".2s")
        fig.update_layout(template=template)
        st.plotly_chart(fig, use_container_width=True)

        st.info("📌 Insight: Top states dominate digital transaction volume.")

# -------- USERS --------
    elif opt=="Users":

        df = user_df.groupby("Year")["User_Count"].sum().reset_index()

        fig = px.line(df, x="Year", y="User_Count", markers=True)
        fig.update_traces(line=dict(width=3))
        fig.update_xaxes(dtick=1)
        fig.update_layout(template=template)
        st.plotly_chart(fig, use_container_width=True)

        df = user_df.groupby("Brand")["User_Count"].sum().reset_index()\
            .sort_values("User_Count",ascending=False).head(10)

        fig = px.bar(df, x="Brand", y="User_Count", text_auto=".2s")
        fig.update_layout(template=template)
        st.plotly_chart(fig, use_container_width=True)

        st.info("📌 Insight: Few brands dominate user adoption.")

# -------- INSURANCE --------
    else:

        df = ins_df.groupby("Year")["Insurance_Amount"].sum().reset_index()

        fig = px.line(df, x="Year", y="Insurance_Amount", markers=True)
        fig.update_traces(line=dict(width=3))
        fig.update_xaxes(dtick=1)
        fig.update_layout(template=template)
        st.plotly_chart(fig, use_container_width=True)

        df = ins_df.groupby("State")["Insurance_Amount"].sum().reset_index()\
            .sort_values("Insurance_Amount",ascending=False).head(10)

        fig = px.bar(df, x="Insurance_Amount", y="State", orientation="h", text_auto=".2s")
        fig.update_layout(template=template)
        st.plotly_chart(fig, use_container_width=True)

        st.info("📌 Insight: Insurance adoption is concentrated in key states.")

# ================= DOWNLOAD =================
st.markdown("### 📥 Download Data")
st.download_button("Download Transactions CSV",
                   txn_df.to_csv(index=False),
                   "transactions.csv")
