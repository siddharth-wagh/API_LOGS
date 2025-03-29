const axios = require('axios');

// Function to send a test log to Logstash
async function sendTestLog() {
  try {
    const response = await axios.post('http://localhost:8086', {
      message: 'Test log message',
      service: 'test-script',
      timestamp: new Date().toISOString(),
      event: 'test_event',
      some_metric: Math.random() * 100,
      tags: ['test', 'example', 'elk-setup']
    });
    
    console.log('Log sent successfully:', response.status);
  } catch (error) {
    console.error('Failed to send log:', error.message);
  }
}

// Send a test log every 5 seconds
console.log('Starting to send test logs to ELK...');
setInterval(sendTestLog, 5000);
sendTestLog(); // Send one immediately 