 FROM apache/airflow:2.9.1
 
 USER root
 RUN apt-get update \
     && apt-get install -y --no-install-recommends build-essential \
     && apt-get clean \
     && rm -rf /var/lib/apt/lists/*
 
 USER airflow
 RUN pip install --no-cache-dir uv
 COPY requirements.txt /requirements.txt
 RUN uv pip install --system --no-cache-dir -r /requirements.txt
 