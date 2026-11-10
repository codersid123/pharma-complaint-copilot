# Stage 1: build the React app into static files (HTML, JS, CSS).
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: serve those files with nginx. Node isn't needed at run time,
# so the final image is small and only contains the built site.
FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
