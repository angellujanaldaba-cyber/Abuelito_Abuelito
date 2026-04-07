# ---------- deps ----------
    FROM node:20-alpine AS deps
    WORKDIR /app
    
    # Si usas npm:
     COPY package.json package-lock.json* ./
     COPY prisma ./prisma
     RUN npm ci
    
    
    # ---------- builder ----------
    FROM node:20-alpine AS builder
    WORKDIR /app
    COPY --from=deps /app/node_modules ./node_modules
    COPY . .
    
    # Build de Next (genera .next/standalone si tienes output:"standalone")
    RUN npm run build
    
    # ---------- runner ----------
    FROM node:20-alpine AS runner
    WORKDIR /app
    ENV NODE_ENV=production
    ENV PORT=3000
    ENV HOSTNAME=0.0.0.0
    
    # Copiamos el servidor standalone y estáticos
    COPY --from=builder /app/public ./public
    COPY --from=builder /app/.next/static ./.next/static
    COPY --from=builder /app/.next/standalone ./
    
    EXPOSE 3000
    
    # El standalone trae server.js en la raíz del contenido copiado
    CMD ["node", "server.js"]
    