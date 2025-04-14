# ========================
# Stage 1: Build Vue App
# ========================
FROM node:20-alpine as build-stage

WORKDIR /app
COPY . .
RUN npm install
RUN npm run build

# ========================
# Stage 2: Serve with Nginx
# ========================
FROM nginx:stable-alpine

# คัดลอกไฟล์ build Vue ไปยัง nginx web root
COPY --from=build-stage /app/dist /usr/share/nginx/html

# คัดลอก nginx config ไปใช้
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
