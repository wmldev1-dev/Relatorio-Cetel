FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./frontend/requirements.txt
RUN pip install --no-cache-dir -r frontend/requirements.txt

COPY app.py ./frontend/app.py
COPY pages ./frontend/pages
COPY services ./frontend/services
COPY components ./frontend/components
COPY utils ./frontend/utils
COPY assets ./frontend/assets
COPY .streamlit ./frontend/.streamlit

EXPOSE 8501

WORKDIR /app/frontend

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
