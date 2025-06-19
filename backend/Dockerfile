FROM python:3.10-slim

WORKDIR /app

COPY chat.py .
COPY plugin-md.py .
COPY plugin-uml.py .

RUN pip install --no-cache-dir fastapi uvicorn requests python-dotenv

EXPOSE 8000
CMD ["uvicorn", "chat:app", "--host", "0.0.0.0", "--port", "8000"] 