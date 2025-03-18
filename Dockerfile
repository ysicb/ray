# Use the official Ray base image with Python
FROM rayproject/ray:latest

# Set the working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY app.py /app/app.py
COPY .env /app/.env

# Expose ports (important for Ray Dashboard)
EXPOSE 6379 8265 10001 8000 8080

# Start Ray, Ray Dashboard, and FastAPI with Serve
CMD ray start --head --dashboard-host 0.0.0.0 && \
    python -c "from app import classifier" && \
    uvicorn app:app --host 0.0.0.0 --port 8080