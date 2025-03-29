const express = require('express');
const app = express();
const port = 5000;

// Middleware to simulate some logging
app.use((req, res, next) => {
  console.log(`[${new Date().toISOString()}] ${req.method} ${req.url}`);
  next();
});

app.get('/ping', (req, res) => {
  console.log('Ping received at service-b');
  res.json({ message: 'pong from service-b' });
});

app.listen(port, () => {
  console.log(`service-b running at http://0.0.0.0:${port}`);
});
