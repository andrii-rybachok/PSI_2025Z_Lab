FROM python:3.12-slim

WORKDIR /work
COPY app /work/app

ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "app.server", "--max-clients", "5"]
