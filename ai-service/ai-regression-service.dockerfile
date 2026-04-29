FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir flask numpy pandas scikit-learn requests

COPY app.py .

EXPOSE 5200

CMD ["python", "app.py"]
