# Dockerfile for creating an image for semantic search, that is:
#   - Downloading a model from Hugging Face and saving it in the ONNX format
#   - Loading and using the saved ONNX model in a Python script
#   - Running FastAPI routes
#   - Running a MCP server
#   - Interacting with Milvus

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install wget which is used in the liveness and readiness probes in the RayService CR which we use to deploy Ray Serve app 
# (the `services/semantic_search/routes/routes.py` script)
RUN apt-get update && \
    apt-get install -y wget && \
    rm -rf /var/lib/apt/lists/*

# Copy all the files from the build directory
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt