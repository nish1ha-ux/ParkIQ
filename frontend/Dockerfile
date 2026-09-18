# Stage 1: Build the React Application
FROM node:20-alpine AS build

WORKDIR /app

# Copy dependency files first for caching efficiency
COPY package*.json ./
RUN npm ci

# Copy application source and configurations
COPY . .

# Pass build-time environment variable for Vite API configuration
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# Compile application into static production assets
RUN npm run build

# Stage 2: Serve the compiled SPA static files using Nginx
FROM nginx:stable-alpine

# Copy built bundle assets from Stage 1
COPY --from=build /app/dist /usr/share/nginx/html

# Replace default config with our custom SPA routing config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
