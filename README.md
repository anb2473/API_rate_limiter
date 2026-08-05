# Flask RLMT (Flask Rate Limiter)

## About
This project is a rate limiter for Flask, and allows you to apply rate limit rules to routes, blueprints, or apply global limits that affect all routes.

## Current Stratagies
* Sliding window

## Installation
This project is registered with PyPi, and can be installed with
```bash
pip install flask_rlmt
```

## How to use
1. Import flask_rlmt
```python
import flask_rlmt
```
2. Create a new limiter
```python
app = Flask(__name__)

limiter = Limiter(
    app=app,
    rules=[
        "10 per minute",
        "100 per hour"
    ]
)
```
3. Add rules to an individual route
```python
@app.route("/")
@limiter.guard(rules=["1000/d"])
def home():
```
4. Apply rules to an entire blueprint
```python
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

limiter.apply(auth_bp, rules=["2 per 10s"])

app.register_blueprint(auth_bp)
```

## Detailed Instructions
For further questions on how to interact with the API, please refer to the [docs/QUICKSTART.md](docs/QUICKSTART.md).
