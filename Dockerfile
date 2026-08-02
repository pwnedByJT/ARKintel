FROM python:3.11-slim-bookworm

WORKDIR /app

# Install dependencies first — separate layer so rebuilds are fast
# when only source code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source tree (see .dockerignore for exclusions)
COPY . .

CMD ["python", "ARK.py"]
