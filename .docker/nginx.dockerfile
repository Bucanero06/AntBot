FROM nginx:1.23.4-alpine

COPY h2o_dashboard/nginx.conf /etc/nginx/nginx.conf
COPY h2o_dashboard/site.conf /etc/nginx/conf.d/default.conf
