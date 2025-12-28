# 1. The Foundation: Start with a lightweight version of Linux + Python
# "Slim" means we stripped out junk to make it fast/small.
FROM python:3.11-slim

# 2. The Workbench: Create a folder inside the container called /app
WORKDIR /app

# 3. The Strategy (Layer Caching):
# We copy ONLY the requirements file first.
# Why? Docker remembers steps. If you change your code tomorrow but NOT your libraries,
# Docker skips Step 4 (installing) and saves you 2 minutes of waiting.
COPY requirements.txt .

# 4. The Setup: Install the libraries (Flask, Boto3, Redis) inside the container
# --no-cache-dir keeps the container small by removing temporary download files.
RUN pip install --no-cache-dir -r requirements.txt

# 5. The Code: Now copy all your python files (api.py, worker.py) into the box
COPY . .

# 6. The Start Button: By default, run the API
CMD ["python", "api.py"]