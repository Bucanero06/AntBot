FROM python:3.9

COPY . .
RUN pip install --no-cache-dir --upgrade h2o-wave
EXPOSE 10101
CMD ["wave", "run", "dashboard", "--no-reload"]
