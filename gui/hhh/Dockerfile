FROM python:3.10-slim

WORKDIR /app

# Install dependencies first (for better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create a non-root user
RUN useradd -m appuser
USER appuser

# Expose the port
EXPOSE 8000

# Start the application with production settings
ENV PRODUCTION=1
CMD ["python", "-m", "server.run_production"]