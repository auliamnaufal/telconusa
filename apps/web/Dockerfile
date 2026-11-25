FROM node:20-alpine

WORKDIR /app

COPY package.json ./
RUN npm install --no-audit --no-fund --fetch-retries=5 --fetch-retry-mintimeout=15000

COPY . .

EXPOSE 3000
CMD ["npm", "run", "dev"]
