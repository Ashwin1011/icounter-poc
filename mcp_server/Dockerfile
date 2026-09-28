FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    && rm -rf /var/lib/apt/lists/*

COPY mcp_server/requirements.txt /app/mcp_server/requirements.txt
RUN pip install --no-cache-dir -r /app/mcp_server/requirements.txt

COPY mcp_server /app/mcp_server
COPY scripts /app/scripts
COPY data /app/data
COPY company /app/knowledge/company
COPY teams /app/knowledge/teams
COPY services /app/knowledge/services
COPY products /app/knowledge/products
COPY projects /app/knowledge/projects
COPY customers /app/knowledge/customers
COPY incidents /app/knowledge/incidents
COPY runbooks /app/knowledge/runbooks
COPY policies /app/knowledge/policies
COPY architecture /app/knowledge/architecture
COPY security /app/knowledge/security
COPY manifest.json /app/knowledge/manifest.json

ENV PYTHONPATH=/app
ENV FASTEMBED_CACHE_PATH=/app/data/runtime/fastembed

EXPOSE 8000

CMD ["python", "-m", "mcp_server.server"]
