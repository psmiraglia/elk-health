FROM python:3
WORKDIR /opt/elkhealth
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY elkhealth.py .
RUN chmod +x elkhealth.py

ENV PYTHONUNBUFFERED=1
CMD ["./elkhealth.py"]

