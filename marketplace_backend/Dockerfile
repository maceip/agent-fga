FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# The port will be specified in the docker-compose command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--reload"]