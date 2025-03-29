import requests
from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    try:
        res = requests.get("http://service-a:4000/start")
        return f"Frontend received: {res.text}"
    except Exception as e:
        return f"Frontend error: {e}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
