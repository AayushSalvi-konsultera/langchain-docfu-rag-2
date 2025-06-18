# # Use official Python image
# FROM python:3.11-slim

# # Set working directory
# WORKDIR /app

# # Copy project files
# COPY . .

# # Install dependencies
# RUN pip install -r requirements.txt

# # Expose port (Cloud Run listens on $PORT)
# ENV PORT=8080
# EXPOSE 8080

# # Run the FastAPI server with uvicorn on $PORT env var
# CMD ["uvicorn", "service:app", "--host", "0.0.0.0", "--port", "8080"]


# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy only necessary files (better practice)
COPY requirements.txt .
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Use PORT environment variable (Cloud Run provides this automatically)
ENV PORT=8080
EXPOSE $PORT

# Critical fix: Use shell form to evaluate PORT variable
CMD ["sh", "-c", "uvicorn mcp_client.service:app --host 0.0.0.0 --port ${PORT}"]