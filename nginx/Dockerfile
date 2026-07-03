FROM node:20-alpine AS builder

WORKDIR /app

# Build student frontend
COPY frontend/package*.json ./student/
COPY frontend/ ./student/
RUN cd student && npm install && npm run build

# Build staff frontend
COPY frontend-staff/package*.json ./staff/
COPY frontend-staff/ ./staff/
RUN cd staff && npm install && npm run build

FROM nginx:alpine
COPY --from=builder /app/student/dist /usr/share/nginx/html
COPY --from=builder /app/staff/dist /usr/share/nginx/html/staff
COPY nginx/nginx.conf /etc/nginx/nginx.conf
