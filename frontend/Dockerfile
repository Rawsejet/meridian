FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package.json pnpm-lock.yaml ./

# Install dependencies
RUN corepack enable pnpm && pnpm install --frozen-lockfile

# Copy application code
COPY src/ ./src/
COPY public/ ./public/
COPY vite.config.ts tsconfig.json tailwind.config.ts ./

# Build
RUN pnpm build

# Expose port
EXPOSE 3000

# Serve
CMD ["pnpm", "preview", "--host", "0.0.0.0", "--port", "3000"]