FROM python:3.9.10
WORKDIR /app
COPY . .
RUN pip3.9 install -r requirements.txt
EXPOSE 8080
CMD ["python3.9", "bot/main.py"]
