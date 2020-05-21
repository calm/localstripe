FROM python:3-buster

WORKDIR /localstripe

COPY . .

RUN pip install -r requirements.txt

EXPOSE 8420

CMD ["python", "-m", "localstripe"]
