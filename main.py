from flask import Flask
from limiter import limit, limit_reset
app = Flask(__name__)

@app.route('/')# быстрый роут для тестов
@limit(100, 1, 5)
def fast():
    return 'I love dogs'

@app.route('/slow')
@limit(100, 60, 90)
def slow():
    return 'I love dogs too'

@app.route('/rs')
def rs():
    if limit_reset():
        return "reseted"
    else:
        return Response("{'err':'header error'}", status=401, mimetype='application/json')
if __name__ == '__main__':
    app.run()