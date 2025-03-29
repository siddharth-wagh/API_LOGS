# Use official Node.js LTS image
FROM node:18

# Set working directory
WORKDIR /usr/src/app

# Copy package.json and install dependencies
COPY package.json package-lock.json ./
RUN npm install

# Copy app source code
COPY . .

# Expose port (change if needed)
EXPOSE 5002

# Start the service using npm start to ensure proper initialization
CMD ["npm", "start"]
