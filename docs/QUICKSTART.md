# Quickstart Guide

**NOTE:** Instructions for formatting the rules strings are at the end of the doc.

## 1. Basic Setup (Global Limiter) & Detailed Arguments

Initialize the `Limiter` by passing your Flask application instance along with custom configurations. The default configurations will apply to ALL routes EXCEPT routes with rule limit decorators or routes that are members of blueprints with rule limits applied. Below is an example that demonstrates all available arguments, using mock database calls for custom identities and options:

```python
from flask import Flask, request, jsonify
from flask_rlmt import Limiter

app = Flask(__name__)

# Mock database lookup for demonstration (you can replace this with a function to
# limit the user by their IP, etc)
def get_user_from_db(req):
    token = req.headers.get("Authorization", "")
    return {"user_id": token, "role": "user"}

# Initialize limiter (NOTE: Only the "app" argument is required)
limiter = Limiter(
    app=app,
    rules=["10 per min"],
    identity=get_user_from_db,
    key_func=lambda user: str(user.get("user_id", "anonymous")),
    on_limited=lambda: (jsonify({"error": "Custom Rate Limit Exceeded JSON"}), 429),
    exempt_when=[lambda user: user.get("role") == "admin"],
    check_db_delay=30,
    purge_db_delay=600
)

if __name__ == "__main__":
    app.run(debug=True)
```

### Arguments

* **`app` (`Flask`):** *(Required)* The core Flask application instance.
* **`rules` (`list[str | tuple[int, int]] | None`):** *(Optional)* Global rate limit rules applying to all routes unless overridden. Can be strings (e.g., `"10 per min"`, `"10/1m"`) or tuples representing `(requests, seconds)` (e.g., `(10, 60)`).
* **`identity` (`Callable[[Request], Any]`):** *(Optional)* A function taking the incoming Flask `Request` object and returning an object representing user identity. Defaults to tracking by IP address (`lambda request: request.remote_addr`).
* **`key_func` (`Callable[[Any], str]`):** *(Optional)* A function taking the user identity object and converting it into a unique string ID for logging. Defaults to `lambda user: str(user)`.
* **`on_limited` (`Callable[[], Any]`):** *(Optional)* A callback function executed when a rate limit policy is violated. Defaults to returning a structured 429 JSON response.
* **`exempt_when` (`list[Callable[[Any], bool]] | None`):** *(Optional)* A list of functions taking the user identity object and returning a boolean. If any function returns `True`, rate limiting rules are bypassed for that request.
* **`check_db_delay` (`int`):** *(Optional)* The number of seconds the database should wait before checking for old logs to remove. Defaults to `60`.
* **`purge_db_delay` (`int`):** *(Optional)* The number of seconds of user idling before they are pruned entirely from the database. Defaults to `900`.

---

## 2. Protecting Specific Routes (`@limiter.guard`)

Use the `@limiter.guard` decorator to apply specific rate limits and custom arguments to individual routes:

```python
# (Only the "rules" argument is required)
@app.route("/")
@limiter.guard(
    rules=["5 per min"],
    identity=get_user_from_db,
    key_gen=lambda user: str(user.get("user_id")),
    on_limited=lambda: (jsonify({"error": "Route-specific limit hit"}), 429),
    exempt_when=[lambda user: user.get("role") == "admin"]
)
def home():
    return "Welcome to the home page!"
```

### Arguments

* **`rules` (`list[str | tuple[int, int]]`):** *(Required)* Limit rules specific to this decorated endpoint, overriding global rules.
* **`identity` (`Callable[[Request], Any] | None`):** *(Optional)* Route-specific function to determine user identity from the request.
* **`key_gen` (`Callable[[Any], str] | None`):** *(Optional)* Route-specific function to generate a string key from the user object.
* **`on_limited` (`Callable[[], Any] | None`):** *(Optional)* Route-specific callback triggered on limit violation.
* **`exempt_when` (`list[Callable[[Any], bool]]`):** *(Optional)* Route-specific list of exemption check functions.

---

## 3. Applying Limits to Blueprints (`limiter.apply`)

To rate limit an entire Flask Blueprint collectively, use `limiter.apply`. (**NOTE:** The limit can only be applied at the end of the blueprints declaration and before the blueprints registration):

```python
from flask import Blueprint

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route("/login")
def login():
    return "Login Page"

# Apply rate limits for the blueprint (Only "bp" and "rules" are required)
# The limit can only be applied AFTER the blueprint is defined and before
# the blueprint is registered.
limiter.apply(
    bp=auth_bp,
    rules=["3 per min"],
    identity=lambda req: mock_get_user_from_db(req),
    key_gen=lambda user: str(user.get("user_id")),
    on_limited=lambda: (jsonify({"error": "Auth blueprint rate limit exceeded"}), 429),
    exempt_when=[lambda user: user.get("role") == "admin"]
)

# Register the blueprint with the Flask application
app.register_blueprint(auth_bp)
```

### Arguments

* **`bp` (`Blueprint`):** *(Required)* The target Flask Blueprint instance.
* **`rules` (`list[str | tuple[int, int]]`):** *(Required)* Rate limit rules applied across all routes in the blueprint.
* **`identity` (`Callable[[Request], Any] | None`):** *(Optional)* Blueprint-level user identity extractor.
* **`key_gen` (`Callable[[Any], str] | None`):** *(Optional)* Blueprint-level string key generator.
* **`on_limited` (`Callable[[], Any] | None`):** *(Optional)* Blueprint-level violation callback.
* **`exempt_when` (`list[Callable[[Any], bool]] | None`):** *(Optional)* Blueprint-level exemption conditions.

---

## Rule String Formatting Requirements

When writing rule strings, follow these syntax requirements:
* The string **MUST** start with a number representing the maximum number of requests.
* Followed by either `"/"` or `" per "` (if using `"per"`, it **MUST** be wrapped in spaces, e.g., `" 10 per min "`).
* Extra spacing is allowed (e.g., `" / "` or `"  per  "`).
* Must end with a time denominator (e.g., `"minute"`, `"hr"`, `"d"`), optionally preceded by a number multiplier (e.g., `"10 seconds"` or `"5secs"`).
