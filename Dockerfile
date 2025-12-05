# ==========================
# 1. DEPS STAGE
# ==========================
FROM node:20-slim AS deps
WORKDIR /app

# Copiar package.json y lock
COPY package*.json ./
COPY prisma ./prisma

# Instalar dependencias
RUN npm install

# Generar cliente Prisma
RUN npx prisma generate


# ==========================
# 2. BUILDER STAGE
# ==========================
FROM node:20-slim AS builder
WORKDIR /app

# Copiamos el resto del código
COPY . .

# Copiamos node_modules desde deps
COPY --from=deps /app/node_modules ./node_modules

# Construimos Next.js
RUN npm run build


# ==========================
# 3. RUNNER STAGE (PRODUCCIÓN)
# ==========================
FROM node:20-slim AS runner
WORKDIR /app

ENV NODE_ENV=production

# Copiamos la salida standalone de Next.js
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

# Copiamos public
COPY --from=builder /app/public ./public

# Puerto donde correrá Next.js en ECS
EXPOSE 3000

# Comando de arranque
CMD ["node", "server.js"]

