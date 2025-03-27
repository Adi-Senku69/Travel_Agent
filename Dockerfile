# Use official Python image
FROM python:3.10

# Set working directory inside the container
WORKDIR /app

# Copy files to the container
COPY requirements.txt .
COPY upload.py .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create the upload directory
RUN mkdir -p /app/data
RUN mkdir -p /app/data/summary

# Expose FastAPI port
EXPOSE 9000

# Start the FastAPI application
CMD ["uvicorn", "upload:app", "--host", "0.0.0.0", "--port", "9000"]
