FROM python:3.10

COPY . .
#RUN pip install --upgrade aioredis
#RUN pip install --no-cache-dir --upgrade requests
#RUN pip install  --upgrade pydantic
RUN pip install -r requirements.txt
RUN pip install --upgrade h2o-wave


EXPOSE 10101
CMD ["wave", "run", "dashboard", "--no-reload"]
