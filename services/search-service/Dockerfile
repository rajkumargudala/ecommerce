FROM python:3.13-alpine3.24

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apk upgrade --no-cache && apk add --no-cache ca-certificates

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt wheel==0.46.2 jaraco.context==6.1.0 \
    && rm -rf /usr/local/lib/python3.13/site-packages/pip* \
        /usr/local/lib/python3.13/site-packages/setuptools* \
        /usr/local/lib/python3.13/ensurepip \
        /usr/local/bin/pip* /usr/local/bin/easy_install*
COPY app.py .

RUN adduser -D -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8092
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8092"]
