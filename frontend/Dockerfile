
FROM node:18-alpine
ENV APP_USER=frontenduser
RUN addgroup --system $APP_USER && adduser --system --ingroup $APP_USER $APP_USER || true
RUN mkdir -p /home/$APP_USER && chown -R $APP_USER:$APP_USER /home/$APP_USER || true
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install && chown -R $APP_USER:$APP_USER /app || true
COPY . .
CMD ["npm","run","dev"]
USER $APP_USER
