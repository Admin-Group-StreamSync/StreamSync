# ---- Build stage ----
FROM node:20-alpine AS builder
WORKDIR /app
COPY package-lock.json ./
RUN npm install --omit=dev

# ---- Runtime stage ----
FROM node:20-alpine AS runtime
WORKDIR /app
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
COPY --from=builder /app/node_modules ./node_modules
COPY .. .
RUN chown -R appuser:appgroup /app
USER appuser
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://localhost:8080/health || exit 1
CMD ["node", "src/index.js"]