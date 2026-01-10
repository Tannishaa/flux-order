import time
import os
import boto3
import redis
import sys
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

# Cloud Credentials
REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')
SQS_QUEUE_URL = os.getenv('SQS_QUEUE_URL')
AWS_REGION = os.getenv('AWS_REGION', 'ap-south-1')
DYNAMODB_TABLE = os.getenv('DYNAMODB_TABLE')

# --- CONNECTIONS ---
console = Console()

# 1. Redis Connection (Upstash)
try:
    # Logic: If host is 'redis' or 'localhost', we are Local (No SSL).
    # If host looks like 'us1-flying-whale...', we are Cloud (SSL=True).
    use_ssl = (REDIS_HOST not in ['redis', 'localhost', '127.0.0.1'])
    
    print(f"🔌 Connecting to Redis: {REDIS_HOST} (SSL={use_ssl})...")
    
    r = redis.Redis(
        host=REDIS_HOST, 
        port=REDIS_PORT, 
        password=REDIS_PASSWORD,
        decode_responses=True, 
        ssl=use_ssl, 
        ssl_cert_reqs=None,
        socket_connect_timeout=5  # <--- CRITICAL FIX: Fail fast if network is bad
    )
    r.ping()
    print("Redis Connected!")
    redis_status = "[bold green]ONLINE[/]"
except Exception as e:
    print(f"Redis Connection Error: {e}")
    print("Check your .env file! REDIS_HOST should be the Upstash URL.")
    # We don't exit, so the dashboard still loads (just shows OFFLINE)
    redis_status = "[bold red]OFFLINE[/]"
    time.sleep(2) # Let user read the error

# 2. AWS Connection
try:
    sqs = boto3.client('sqs', region_name=AWS_REGION)
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    table = dynamodb.Table(DYNAMODB_TABLE)
    aws_status = "[bold green]ONLINE[/]"
except Exception as e:
    aws_status = "[bold red]OFFLINE[/]"

# --- DATA FETCHING ---
def get_metrics():
    try:
        # Queue Stats
        q = sqs.get_queue_attributes(
            QueueUrl=SQS_QUEUE_URL, 
            AttributeNames=['ApproximateNumberOfMessages', 'ApproximateNumberOfMessagesNotVisible']
        )
        waiting = int(q['Attributes']['ApproximateNumberOfMessages'])
        processing = int(q['Attributes']['ApproximateNumberOfMessagesNotVisible'])
        
        # Sales Stats (Scan is okay for small demos)
        # Scan simulates counting rows in the DB
        scan = table.scan(Select='COUNT')
        sold = scan['Count']
        
        return waiting, processing, sold
    except:
        return 0, 0, 0

def get_recent_logs():
    try:
        # Get last 8 items for the UI
        response = table.scan(Limit=8) 
        items = response.get('Items', [])
        # Sort by timestamp descending if possible, otherwise just return
        return items
    except:
        return []

# --- LAYOUT ---
def make_layout():
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="stats", size=8),
        Layout(name="visual", size=4),
        Layout(name="logs")
    )
    
    layout["stats"].split_row(
        Layout(name="health"),
        Layout(name="revenue")
    )
    return layout

def generate_dashboard(layout):
    waiting, processing, sold = get_metrics()
    logs = get_recent_logs()
    
    # 1. HEADER
    time_str = datetime.now().strftime("%H:%M:%S")
    layout["header"].update(Panel(
        Align.center(f"[bold white]FLUX MISSION CONTROL[/] | {time_str}"),
        style="on blue"
    ))
    
    # 2. HEALTH PANEL
    health_table = Table(show_header=False, box=None, expand=True)
    health_table.add_row("AWS SQS", aws_status)
    health_table.add_row("Redis Cache", redis_status)
    health_table.add_row("Worker Status", f"[yellow]{processing} active[/]" if processing > 0 else "[dim]Idle[/]")
    health_table.add_row("Queue Depth", f"[red bold]{waiting}[/] waiting" if waiting > 0 else "[green]Clear[/]")
    
    layout["health"].update(Panel(
        health_table, title="System Vitals", border_style="cyan"
    ))

    # 3. REVENUE PANEL
    revenue = sold * 100
    layout["revenue"].update(Panel(
        Align.center(f"\n[bold gold1]${revenue:,}[/]\n[dim]Total Sales[/]"),
        title="Revenue", border_style="green"
    ))

    # 4. VISUAL PROGRESS (Inventory)
    total_seats = 16 # A1-A4, B1-B4, C1-C4, D1-D4
    sold_percent = min((sold / total_seats) * 100, 100)
    
    bar_width = 40
    filled = int((sold / total_seats) * bar_width)
    bar = "█" * filled + "░" * (bar_width - filled)
    
    layout["visual"].update(Panel(
        Align.center(f"[magenta]{bar}[/] [bold]{int(sold_percent)}%[/]"),
        title="Cinema Capacity", border_style="magenta"
    ))

    # 5. LOGS TABLE
    log_table = Table(expand=True, border_style="dim", box=None)
    log_table.add_column("User", style="cyan")
    log_table.add_column("Seat", style="bold white")
    log_table.add_column("Time", style="dim")
    
    # Show items
    for item in logs:
        # Convert timestamp to time string if available
        ts = item.get('timestamp', '')
        if ts:
            try:
                dt_obj = datetime.fromtimestamp(float(ts))
                time_display = dt_obj.strftime("%H:%M:%S")
            except:
                time_display = "-"
        else:
            time_display = "-"

        log_table.add_row(
            item.get('user_id', '?'),
            item.get('item_id', '?'),
            time_display
        )
        
    layout["logs"].update(Panel(
        log_table, title="Recent Transactions (DynamoDB)", border_style="white"
    ))
    
    return layout

# --- MAIN ---
if __name__ == "__main__":
    layout = make_layout()
    print("[bold yellow]Initializing Satellite Link...[/]")
    
    # Brief pause to let the user see the connection status messages
    time.sleep(1)

    with Live(layout, refresh_per_second=2, screen=True):
        while True:
            generate_dashboard(layout)
            time.sleep(0.5)