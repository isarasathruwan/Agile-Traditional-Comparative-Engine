FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app
RUN mkdir -p /var/lib/methodalign/documents

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entrypoint separately so cache invalidates when it changes
COPY entrypoint.sh .

COPY . .
RUN sed -i 's/\r$//' entrypoint.sh
RUN chmod +x entrypoint.sh
RUN chown -R app:app /app /var/lib/methodalign

USER app

EXPOSE 8000

VOLUME ["/var/lib/methodalign/documents"]

ENTRYPOINT ["./entrypoint.sh"]
