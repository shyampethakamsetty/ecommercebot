
FROM node:18-alpine
ENV APP_USER=frontenduser
RUN addgroup --system $APP_USER && adduser --system --ingroup $APP_USER $APP_USER || true
RUN mkdir -p /home/$APP_USER && chown -R $APP_USER:$APP_USER /home/$APP_USER || true

# Create and set ownership of the app directory
RUN mkdir -p /app && chown -R $APP_USER:$APP_USER /app

WORKDIR /app
USER $APP_USER

COPY --chown=$APP_USER:$APP_USER package.json package-lock.json* ./
RUN npm install

COPY --chown=$APP_USER:$APP_USER . .

CMD ["npm","run","dev"]
