FROM python:3.12-slim

WORKDIR /app

COPY client.py gen_file.py run_client.sh /app/

RUN chmod +x /app/run_client.sh

CMD ["./run_client.sh"]
