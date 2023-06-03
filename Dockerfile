FROM python:3-buster
ARG seed_dir
ENV SEED_DIR=$seed_dir

WORKDIR /localstripe

COPY . .

RUN pip install -r requirements.txt

EXPOSE 8420

CMD ["python", "-m", "localstripe"]
