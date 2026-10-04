FROM nginxinc/nginx-unprivileged:1.27-alpine

ARG APP_VERSION=v1
ENV APP_VERSION=${APP_VERSION}

WORKDIR /usr/share/nginx/html
COPY index.html styles.css script.js ./
COPY nginx.conf /etc/nginx/conf.d/default.conf

CMD ["/bin/sh", "-c", "envsubst '$${APP_VERSION}' < /etc/nginx/conf.d/default.conf > /tmp/default.conf && mv /tmp/default.conf /etc/nginx/conf.d/default.conf && envsubst '$${APP_VERSION}' < /usr/share/nginx/html/index.html > /tmp/index.html && mv /tmp/index.html /usr/share/nginx/html/index.html && nginx -g 'daemon off;'"]

USER 101
EXPOSE 8080
