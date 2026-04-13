# ---------- deps ----------
    FROM node:20-alpine AS deps
    WORKDIR /app
    
    COPY package.json package-lock.json* ./
    COPY prisma ./prisma
    RUN npm ci
    
    # ---------- builder ----------
    FROM node:20-alpine AS builder
    WORKDIR /app
    
    COPY --from=deps /app/node_modules ./node_modules
    COPY . .
    
    ARG APP_VERSION=unknown
    ENV NEXT_PUBLIC_VERSION=$APP_VERSION
    
    RUN npm run build
    
    # ---------- runner ----------
    FROM node:20-alpine AS runner
    WORKDIR /app
    
    ENV NODE_ENV=production
    ENV PORT=3000
    ENV HOSTNAME=0.0.0.0
    
    ARG APP_VERSION=unknown
    ENV NEXT_PUBLIC_VERSION=$APP_VERSION
    
    COPY --from=builder /app/public ./public
    COPY --from=builder /app/.next/static ./.next/static
    COPY --from=builder /app/.next/standalone ./
    
    EXPOSE 3000
    
    CMD ["node", "server.js"]
    