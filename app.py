import streamlit as st
import mysql.connector
import pandas as pd
import plotly.express as px
import json

st.set_page_config(layout="wide", page_title="PhonePe Analytics")

# ---------------- DB ----------------
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Guhan@8940",
    database="Phonepe_project"
)

def run(q):
    return pd.read_sql(q, conn)

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
years = run("SELECT DISTINCT Year FROM aggregated_transaction ORDER BY Year")["Year"].tolist()
quarters = [1,2,3,4]

year = st.sidebar.selectbox("📅 Year", years)
quarter = st.sidebar.selectbox("📊 Quarter", quarters)

# ---------------- KPI ----------------
def get_val(q):
    return run(q)["v"][0] or 0

txn = get_val(f"SELECT SUM(Transaction_Amount) v FROM aggregated_transaction WHERE Year={year}")
usr = get_val(f"SELECT SUM(User_Count) v FROM aggregated_user WHERE Year={year}")
ins = get_val(f"SELECT SUM(Insurance_Amount) v FROM aggregated_insurance WHERE Year={year}")

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

    df = run(f"""
        SELECT State, SUM(Transaction_Amount) total
        FROM aggregated_transaction
        WHERE Year={year} AND Quarter={quarter}
        GROUP BY State
    """)

    df["State_clean"] = df["State"].apply(map_state)
    df = df.dropna()

    fig = px.choropleth(
        df,
        geojson=geo,
        featureidkey="properties.NAME_1",
        locations="State_clean",
        color="total",
        hover_data={"total":":,.0f"},
        color_continuous_scale="Blues"
    )

    fig.update_geos(fitbounds="locations", visible=False)
    st.plotly_chart(fig, use_container_width=True)

    st.success("Insight: Southern and Western states dominate digital transactions, indicating higher adoption.")

# =================================================
# 📊 ANALYSIS
# =================================================
else:

    option = st.selectbox("Choose Analysis", ["Transactions","Users","Insurance"])

# ================= TRANSACTIONS =================
    if option=="Transactions":

        st.subheader("📊 Transaction Analysis")

        # Year trend
        df = run("SELECT Year,SUM(Transaction_Amount) total FROM aggregated_transaction GROUP BY Year ORDER BY Year")
        df["Year"] = df["Year"].astype(int)

        fig = px.line(df,x="Year",y="total",markers=True,title="Yearly Growth")
        fig.update_xaxes(dtick=1)
        st.plotly_chart(fig,use_container_width=True)

        # Quarter
        df = run("SELECT Quarter,SUM(Transaction_Amount) total FROM aggregated_transaction GROUP BY Quarter")
        st.plotly_chart(px.bar(df,x="Quarter",y="total",title="Quarter Trend"),use_container_width=True)

        # Top states
        df = run("SELECT State,SUM(Transaction_Amount) total FROM aggregated_transaction GROUP BY State ORDER BY total DESC LIMIT 10")
        st.plotly_chart(px.bar(df.sort_values("total"),x="total",y="State",orientation="h",title="Top States"),use_container_width=True)

        # Type split
        df = run("SELECT Transaction_Type,SUM(Transaction_Amount) total FROM aggregated_transaction GROUP BY Transaction_Type")
        st.plotly_chart(px.pie(df,names="Transaction_Type",values="total",hole=0.4,title="Transaction Split"),use_container_width=True)

        # Heatmap (fixed)
        df = run("""
            SELECT State,Transaction_Type,SUM(Transaction_Amount) total
            FROM aggregated_transaction
            GROUP BY State,Transaction_Type
        """)
        top = df.groupby("State")["total"].sum().nlargest(10).index
        df = df[df["State"].isin(top)]
        pivot = df.pivot(index="State",columns="Transaction_Type",values="total").fillna(0)

        st.plotly_chart(px.imshow(pivot,title="Top 10 States vs Type"),use_container_width=True)

        st.info("Insight: Peer-to-peer transactions dominate across all high-performing states.")

# ================= USERS =================
    elif option=="Users":

        st.subheader("👥 User Analysis")

        df = run("SELECT Year,SUM(User_Count) total FROM aggregated_user GROUP BY Year ORDER BY Year")
        df["Year"] = df["Year"].astype(int)

        fig = px.line(df,x="Year",y="total",markers=True,title="User Growth")
        fig.update_xaxes(dtick=1)
        st.plotly_chart(fig,use_container_width=True)

        df = run("SELECT Brand,SUM(User_Count) total FROM aggregated_user GROUP BY Brand ORDER BY total DESC LIMIT 10")
        st.plotly_chart(px.bar(df,x="Brand",y="total",title="Top Brands"),use_container_width=True)

        df = run("SELECT Brand,AVG(User_Percentage) share FROM aggregated_user GROUP BY Brand")
        st.plotly_chart(px.pie(df,names="Brand",values="share",hole=0.4,title="Brand Share"),use_container_width=True)

        # Brand trend FIXED
        df = run("""
            SELECT Year,Brand,SUM(User_Count) total
            FROM aggregated_user
            GROUP BY Year,Brand
        """)
        df["Year"] = df["Year"].astype(int)

        top = df.groupby("Brand")["total"].sum().nlargest(5).index
        df = df[df["Brand"].isin(top)]
        df = df.sort_values(["Brand","Year"])

        fig = px.line(df,x="Year",y="total",color="Brand",markers=True,title="Top 5 Brand Trend")
        fig.update_xaxes(dtick=1)
        st.plotly_chart(fig,use_container_width=True)

        st.info("Insight: A few dominant brands capture the majority of the user base.")

# ================= INSURANCE =================
    elif option=="Insurance":

        st.subheader("🛡️ Insurance Analysis")

        df = run("SELECT Year,SUM(Insurance_Amount) total FROM aggregated_insurance GROUP BY Year ORDER BY Year")
        df["Year"] = df["Year"].astype(int)

        fig = px.line(df,x="Year",y="total",markers=True,title="Growth")
        fig.update_xaxes(dtick=1)
        st.plotly_chart(fig,use_container_width=True)

        df = run("SELECT State,SUM(Insurance_Amount) total FROM aggregated_insurance GROUP BY State ORDER BY total DESC LIMIT 10")
        st.plotly_chart(px.bar(df.sort_values("total"),x="total",y="State",orientation="h",title="Top States"),use_container_width=True)

        df = run("SELECT Quarter,SUM(Insurance_Amount) total FROM aggregated_insurance GROUP BY Quarter")
        st.plotly_chart(px.bar(df,x="Quarter",y="total",title="Quarter Trend"),use_container_width=True)

        df = run("""
            SELECT State,SUM(Insurance_Count) count,SUM(Insurance_Amount) amount
            FROM aggregated_insurance GROUP BY State
        """)
        st.plotly_chart(px.scatter(df,x="count",y="amount",size="amount",title="Count vs Amount"),use_container_width=True)

        df["avg"] = df["amount"]/df["count"]
        df = df.sort_values("avg",ascending=False).head(10)

        st.plotly_chart(px.bar(df,x="avg",y="State",orientation="h",title="Top 10 Avg Ticket Size"),use_container_width=True)

        st.info("Insight: Higher ticket sizes are concentrated in fewer states, indicating premium adoption pockets.")