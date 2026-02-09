# Use lightweight Python image for faster pulls
FROM python:3.11-slim

WORKDIR /app

# Set Python environment variables for optimal performance
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy requirements first for better layer caching
# This ensures dependency installation is cached unless requirements.txt changes
COPY requirements.txt .

# Install dependencies with no cache dir to reduce image size
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download embedding model during build phase
# This moves the ~3-5 min model download from runtime to build time
# The model is cached by Docker layer caching for subsequent builds
RUN python -c "from fastembed import TextEmbedding; TextEmbedding('sentence-transformers/all-MiniLM-L6-v2')"

# Copy application code
# This layer changes frequently, so it's last to maximize cache reuse
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
