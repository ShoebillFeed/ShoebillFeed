FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# nginx's stable branch, which is what upstream recommends for production.
# Pinning a minor line (this was 1.27) left the one network-facing
# container in the stack on Alpine 3.21 while everything else had moved
# to 3.23/3.24; `stable-alpine` tracks the current Alpine and keeps
# picking up patches without needing a bump here every few months.
FROM nginx:stable-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
