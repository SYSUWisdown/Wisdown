FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y plantuml graphviz && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY chat.py .
COPY plugin-md.py .
COPY plugin-uml.py .
COPY plugin-reasoner.py .
COPY plugin-vectorizer.py .
COPY plugin-infoagent.py .

EXPOSE 8000
CMD ["uvicorn", "chat:app", "--host", "0.0.0.0", "--port", "8000"]