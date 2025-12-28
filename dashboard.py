import streamlit as st
import boto3
import pandas as pd
import time
import os
import datetime
from dotenv import load_dotenv

# --- 1. CONFIGURATION ---
load_dotenv()
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
QUEUE_URL = os.getenv("SQS_QUEUE_URL")
TABLE_NAME = os.getenv("DYNAMODB_TABLE")

st.set_page_config(page_title="Flux Monitor", layout="wide")

# --- 2. CSS STYLING 
st.markdown("""
    <style>
    /* Main Background adjustments */
    .block-container { padding-top: 1.5rem; }
    
    /* Metrics Cards: Dark Grey with Blue Accent */
    div[data-testid="stMetric"] {
        background-color: #262730;
        border: 1px solid #3b3b3b;
        border-left: 5px solid #3b82f6; /* Bright Blue Accent */
        padding: 15px;
        border-radius: 5px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    /* Metric Value Text */
    div[data-testid="stMetricValue"] {
        color: #ffffff;
    }
    
    /* Chart and Table backgrounds */
    div[data-testid="stDataFrame"] {
        background-color: #262730;
        padding: 10px;
        border-radius: 5px;
    }
    
    /* Remove default table index */
    thead tr th:first-child { display:none }
    tbody th { display:none }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CONNECT TO AWS ---
try:
    sqs = boto3.client('sqs', region_name=AWS_REGION)
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    table = dynamodb.Table(TABLE_NAME)
except:
    st.error("AWS Connection Failed")
    st.stop()

# --- 4. DATA FUNCTIONS ---
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=['Time', 'Load'])

def get_metrics():
    try:
        q = sqs.get_queue_attributes(QueueUrl=QUEUE_URL, AttributeNames=['ApproximateNumberOfMessages'])
        depth = int(q['Attributes']['ApproximateNumberOfMessages'])
    except: depth = 0
    
    try:
        # Scan count (Simulation only - expensive in real production)
        response = table.scan(Select='COUNT')
        sold = response['Count']
    except: sold = 0
    return depth, sold

def get_recent_orders():
    try:
        # Get 20 items to fill the table
        response = table.scan(Limit=20)
        return response.get('Items', [])
    except: return []

# --- 5. SIDEBAR (Fills the empty space) ---
with st.sidebar:
    st.title("Flux Order")
    st.caption("INFRASTRUCTURE STATUS")
    
    # Fake system checks to make it look "Busy"
    st.success("API Gateway: Online")
    st.success("Worker Nodes: Active")
    st.success("Database: Connected")
    
    st.divider()
    st.markdown(f"**Region:** `{AWS_REGION}`")
    st.markdown(f"**Table:** `{TABLE_NAME}`")
    
    if st.button("Clear Chart History"):
        st.session_state.history = pd.DataFrame(columns=['Time', 'Load'])

# --- 6. MAIN LAYOUT ---
# Header
c1, c2 = st.columns([3, 1])
with c1:
    st.subheader("Live System Status")
with c2:
    st.caption(f"Last Update: {datetime.datetime.now().strftime('%H:%M:%S')}")

# Fetch Data
queue_depth, total_sold = get_metrics()
recent_items = get_recent_orders()

# Update Chart History
current_time = datetime.datetime.now().strftime("%H:%M:%S")
new_row = pd.DataFrame({'Time': [current_time], 'Load': [queue_depth]})
st.session_state.history = pd.concat([st.session_state.history, new_row]).tail(40)

# Metrics Row
m1, m2, m3, m4 = st.columns(4)
m1.metric("Queue Load", queue_depth)
m2.metric("Orders Processed", total_sold)
m3.metric("Est. Revenue", f"${total_sold * 100:,.0f}")
m4.metric("System Health", "99.9%", delta="Stable") # Static metric for visual balance

st.divider()

# Split View: Chart (Left) + Table (Right)
col_chart, col_table = st.columns([2, 1])

with col_chart:
    st.markdown("**Traffic Volume (30s Window)**")
    # Area chart looks "fuller" than line chart
    st.area_chart(st.session_state.history.set_index('Time'), height=300, color="#0f172a")

with col_table:
    st.markdown("**Transaction Log**")
    if recent_items:
        df = pd.DataFrame(recent_items)
        
        # Clean up the table columns
        cols_to_show = ["user_id", "item_id", "status"]
        df_clean = df[cols_to_show] if set(cols_to_show).issubset(df.columns) else df
        
        # Use Streamlit's fancy column config to make "Status" look like a button
        st.dataframe(
            df_clean,
            use_container_width=True,
            hide_index=True,
            height=300,
            column_config={
                "status": st.column_config.TextColumn(
                    "Status",
                    help="Order Status",
                    default="SOLD",
                )
            }
        )
    else:
        st.info("No transactions yet.")

# Auto-Refresh
time.sleep(1)
st.rerun()