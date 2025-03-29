const axios = require('axios');

const runLoad = async () => {
  while (true) {
    try {
      const res = await axios.get('http://service-a:4000/test');
      console.log(`[Test] ${new Date().toISOString()} - ${res.data.message}`);
    } catch (err) {
      console.error(`[Error] ${err.message}`);
    }
    await new Promise(resolve => setTimeout(resolve, 2000)); // 2 sec interval
  }
};

runLoad();
