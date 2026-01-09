import time
import os
import boto3
from dotenv import load_dotenv
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.console import Console
from rich.align import Align
from datetime import datetime

# --- CONFIGURATION ---
load_dotenv()
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
QUEUE_URL = os.getenv("SQS_QUEUE_URL")
TABLE_NAME = os.getenv("DYNAMODB_TABLE")

# Setup AWS (Persistent Connection)
sqs = boto3.client('sqs', region_name=AWS_REGION)
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
table = dynamodb.Table(TABLE_NAME)

def get_metrics():
    """Fetch current system state from AWS"""
    try:
        # 1. Get Queue Depth
        q = sqs.get_queue_attributes(
            QueueUrl=QUEUE_URL, 
            AttributeNames=['ApproximateNumberOfMessages', 'ApproximateNumberOfMessagesNotVisible']
        )
        waiting = int(q['Attributes']['ApproximateNumberOfMessages'])
        processing = int(q['Attributes']['ApproximateNumberOfMessagesNotVisible'])
        
        # 2. Get Sales Count
        # In a real app, don't Scan. For this demo, it's fine.
        scan = table.scan(Select='COUNT')
        sold = scan['Count']
        
        return waiting, processing, sold
    except Exception as e:
        return -1, -1, -1

def get_recent_logs():
    """Fetch last 8 sales"""
    try:
        response = table.scan(Limit=8)
        items = response.get('Items', [])
        # Sort by timestamp if available, else random
        return items
    except:
        return []

def make_layout():
    """Define the grid structure"""
    layout = Layout()
    
    # Split into Top (Header), Middle (Stats), Bottom (Logs)
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="stats", size=10),
        Layout(name="logs")
    )
    
    # Split stats into 3 columns
    layout["stats"].split_row(
        Layout(name="queue"),
        Layout(name="workers"),
        Layout(name="db")
    )
    return layout

def generate_dashboard(layout):
    """Update the content of the layout"""
    waiting, processing, sold = get_metrics()
    
    # 1. HEADER
    time_str = datetime.now().strftime("%H:%M:%S")
    header_text = Text(f"FLUX MISSION CONTROL | {AWS_REGION} | {time_str}", style="bold white on blue", justify="center")
    layout["header"].update(header_text)
    
    # 2. STATS PANELS
    # Queue Panel
    q_color = "green" if waiting < 10 else "red"
    layout["queue"].update(Panel(
        Align.center(f"[bold {q_color}]{waiting}[/]\n\n[white]Waiting Messages[/]"),
        title="[bold blue]SQS Queue[/]",
        border_style="blue"
    ))
    
    # Worker Panel
    w_color = "yellow" if processing > 0 else "dim white"
    layout["workers"].update(Panel(
        Align.center(f"[bold {w_color}]{processing}[/]\n\n[white]Active Workers[/]"),
        title="[bold yellow]Processing[/]",
        border_style="yellow"
    ))
    
    # Database Panel
    layout["db"].update(Panel(
        Align.center(f"[bold green]{sold}[/]\n\n[white]Confirmed Sales[/]"),
        title="[bold green]DynamoDB[/]",
        border_style="green"
    ))
    
    # 3. LOGS TABLE
    logs = get_recent_logs()
    table_ui = Table(expand=True, border_style="dim")
    table_ui.add_column("User ID", style="cyan")
    table_ui.add_column("Item", style="magenta")
    table_ui.add_column("Status", style="green")
    
    for item in logs:
        table_ui.add_row(
            item.get('user_id', '???'), 
            item.get('item_id', '???'), 
            "[bold]SOLD[/]"
        )
        
    layout["logs"].update(Panel(
        table_ui, 
        title="Live Transaction Log",
        border_style="white"
    ))
    
    return layout

# --- MAIN LOOP ---
console = Console()
layout = make_layout()

print("Connecting to AWS...")
with Live(layout, refresh_per_second=4, screen=True):
    while True:
        generate_dashboard(layout)
        time.sleep(0.5)