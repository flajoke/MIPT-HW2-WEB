FROM node:20-alpine

WORKDIR /app

ENV NODE_ENV=development
ENV NPM_CONFIG_AUDIT=false
ENV NPM_CONFIG_FUND=false

COPY package.json package-lock.json* ./

RUN npm install --no-audit --no-fund

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]