FROM python:3.12-slim

WORKDIR /app

COPY docker/piper/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY docker/piper/server.py /app/server.py
COPY docker/piper/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENV PIPER_HOST=0.0.0.0 \
    PIPER_PORT=5000 \
    PIPER_VOICE=ko-KR-SunHiNeural

EXPOSE 5000

ENTRYPOINT ["/app/entrypoint.sh"]
