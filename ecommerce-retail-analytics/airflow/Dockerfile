FROM apache/airflow:2.9.3-python3.12

USER root

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow

# Copy and install Python dependencies
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

# Note: Scripts are mounted via docker-compose volume (-  ../scripts:/opt/airflow/scripts)
ENV PYTHONPATH="${PYTHONPATH}:/opt/airflow"
