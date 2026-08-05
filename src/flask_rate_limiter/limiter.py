from flask import Flask, request, g, jsonify, Request, Blueprint
from functools import wraps
from datetime import datetime, timedelta
from collections import deque
import threading
import time
from dataclasses import dataclass, field
from typing import List, Callable, Dict, Any
import copy
import re

class InvalidLimit(Exception):
    def __init__(
        self, message="Limit is invalid."
    ):
        self.message = message
        super().__init__(self.message)

class InvalidTimeUnit(Exception):
    def __init__(
        self, message="Time unit is invalid."
    ):
        self.message = message
        super().__init__(self.message)

class NoIdentity(Exception):
    def __init__(
        self, message="Identity function is missing."
    ):
        self.message = message
        super().__init__(self.message)

class NoKeyFunc(Exception):
    def __init__(
        self, message="Key function is missing."
    ):
        self.message = message
        super().__init__(self.message)

class NoLimit(Exception):
    def __init__(
        self, message="Limit is missing."
    ):
        self.message = message
        super().__init__(self.message)


class NoWindow(Exception):
    def __init__(
        self, message="Window is missing."
    ):
        self.message = message
        super().__init__(self.message)


class NoOnLimited(Exception):
    def __init__(
        self, message="On limited function is missing."
    ):
        self.message = message
        super().__init__(self.message)

@dataclass
class LimitStatistic:
    retry_after: int | None
    remaining: int | None
    reset_at: datetime | None
    limit: int | None
    window: int | None

class UserPool:
    def __init__(self, shard_count=32):
        self.shards = [
            {"users": {},
                "lock": threading.Lock()}
            for _ in range(shard_count)]
        self.shard_count = shard_count

    def get_shard(self, user_id):
        shard_idx = hash(user_id) % self.shard_count
        return self.shards[shard_idx]

    def update_user_log(self, user_id, route, now, limits) -> tuple[bool, deque[datetime], tuple[int, int] | None, List[LimitStatistic], LimitStatistic, tuple[int, int], tuple[int, int]]:
        shard = self.get_shard(user_id)
        with shard["lock"]:
            user = shard["users"].get(user_id)
            if user is None:
                user = User()
                shard["users"][user_id] = user
            return user.update_log(route, now, limits)

    def purge_stale_data(self, now, purge_db_delay):
        threshold = now - timedelta(seconds=purge_db_delay)
        for shard in self.shards:
            with shard["lock"]:
                for user_id, user in list(shard["users"].items()):
                    if  threshold >= user.latest_stamp:
                        del shard["users"][user_id]
                    else:
                        user.purge_stale_data(now)
                        if not user.logs:
                            del shard["users"][user_id]

@dataclass
class RouteLogs:
    limits:List[tuple[int, int]]
    logs:deque[datetime]
    longest_limit_by_window:tuple[int, int]
    longest_limit_by_limit:tuple[int, int]
    shortest_limit_by_limit:tuple[int, int]

class User:
    def __init__(self):
        self.logs:Dict[str, RouteLogs] = {}
        self.latest_stamp = datetime.now()

    def extract_most_valuable_statistics(self, limit_statistics:List[LimitStatistic]) -> LimitStatistic:
        remaining:int | None = None
        reset_at:datetime | None = None
        for statistic in limit_statistics:
            if statistic.remaining is not None and (remaining is None or statistic.remaining < remaining):
                remaining = statistic.remaining
            if statistic.reset_at is not None and (reset_at is None or statistic.reset_at > reset_at):
                reset_at = statistic.reset_at
        return LimitStatistic(retry_after=None, remaining=remaining, reset_at=reset_at, limit=None, window=None)

    def update_log(self, route, now, limits) -> tuple[bool, deque[datetime], tuple[int, int] | None, List[LimitStatistic], LimitStatistic, tuple[int, int], tuple[int, int]]:
        if route not in self.logs:
            if len(limits) == 0:
                raise ValueError("No limits provided")
            sorted_limits = sorted(limits, key=lambda x: x[1], reverse=True)
            longest_limit_by_limit = max(sorted_limits)
            longest_limit_by_window = max(sorted_limits, key=lambda x: x[1])
            shortest_limit_by_limit = min(sorted_limits)
            self.logs[route] = RouteLogs(sorted_limits, deque(), longest_limit_by_window, longest_limit_by_limit, shortest_limit_by_limit)
        route_data:RouteLogs = self.logs[route]
        if len(route_data.limits) == 0 and not route_data.longest_limit_by_limit:
            raise ValueError("No limits provided")
        longest_limit = route_data.limits[0]
        self.latest_stamp = now
        stale_threshold = now - timedelta(seconds=longest_limit[1])
        logs = route_data.logs
        while logs and logs[0] < stale_threshold:
            logs.popleft()
        limit_statistics:List[LimitStatistic] = []
        logs.append(now)

        copied_logs = deque(logs)
        for limit in route_data.limits:
            target_threshold = now - timedelta(seconds=limit[1])
            while copied_logs and copied_logs[0] <= target_threshold:
                copied_logs.popleft()
            if not copied_logs:
                break
            last_log = copied_logs[0]
            limit_in_check = LimitStatistic(
                retry_after = int(max(((last_log + timedelta(seconds=limit[1]) - now).total_seconds()), 0)),
                remaining=max(0, limit[0] - len(copied_logs)),
                reset_at=(last_log + timedelta(seconds=limit[1])),
                limit=limit[0],
                window=limit[1]
            )

            limit_statistics.append(limit_in_check)
            if len(copied_logs) > limit[0]:
                return (
                    True,
                    logs,
                    limit,
                    limit_statistics,
                    limit_in_check,
                    route_data.longest_limit_by_limit,
                    route_data.longest_limit_by_window
                )
            if not copied_logs:
                break
        return (
            False,
            logs,
            None,
            limit_statistics,
            self.extract_most_valuable_statistics(limit_statistics),
            route_data.longest_limit_by_limit,
            route_data.longest_limit_by_window
        )

    def purge_stale_data(self, now):
        for route in list(self.logs.keys()):
            route_logs = self.logs[route].logs
            old_time = now - timedelta(seconds=self.logs[route].longest_limit_by_window[1])
            while route_logs and route_logs[0] <= old_time:
                route_logs.popleft()
            if not route_logs:
                del self.logs[route]

pool = UserPool()

def cleanup_worker(check_db_delay, purge_db_delay):
    while True:
        time.sleep(check_db_delay)
        pool.purge_stale_data(datetime.now(), purge_db_delay)

TIME_KEYWORDS = {
    "s": 1,
    "m": 60,
    "h": 3600,
    "d": 86400
}

UNIT_MAP = {
    "second": "s",
    "seconds": "s",
    "sec": "s",
    "secs": "s",
    "minute": "m",
    "minutes": "m",
    "min": "m",
    "mins": "m",
    "hour": "h",
    "hours": "h",
    "hr": "h",
    "hrs": "h",
    "day": "d",
    "days": "d",
}

TIME_PATTERN = re.compile(
    '(' + '|'.join(sorted(map(re.escape, UNIT_MAP.keys()), key=len, reverse=True)) + ')',
    flags=re.IGNORECASE
)

def json_on_limited():
    logs = g.logs
    return jsonify({
        "status": 429,
        "error": "Rate Limit Exceeded",
        "retry_after": logs.retry_after,
        "remaining": logs.remaining,
        "reset_at": logs.reset_at.isoformat(),
        "limit": logs.enforced_limit[0] if logs.enforced_limit else logs.longest_limit_by_limit[0],
        "window": logs.enforced_limit[1] if logs.enforced_limit else None,
        "endpoint": logs.endpoint,
        "identity": logs.identity,
    }), 429

@dataclass
class RateLimitInfo:
    enforced_limit: tuple[int, int] | None
    limit_statistics: List[LimitStatistic]
    endpoint: str
    identity: str
    logs: deque[datetime]
    remaining: int | None
    reset_at: datetime | None
    retry_after: int | None
    longest_limit_by_limit: tuple[int, int]
    longest_limit_by_window: tuple[int, int]

@dataclass
class RateLimitRule:
    limits: List[tuple[int, int]]
    bp: Blueprint
    identity:Callable[[Request], Any] | None
    key_gen:Callable[[Any], str] | None
    on_limited:Callable[[], Any] | None
    exempt_when:list[Callable[[Any], bool]] | None

class Limiter:
    def __init__(
        self,
        app:Flask,
        limits:list[str | tuple[int, int]] | None=None,
        identity:Callable[[Request], Any]=lambda request: request.remote_addr,
        key_func:Callable[[Any], str]=lambda user: str(user),
        on_limited:Callable[[], Any]=json_on_limited,
        exempt_when:list[Callable[[Any], bool]] | None=None,
        check_db_delay:int=60,
        purge_db_delay:int=900
    ):
        self.limits:list[tuple[int, int]] = [self.decode(limit) for limit in limits or []]
        self.identity:Callable[[Any], Any] | None = identity
        self.key_gen:Callable[[Any], str] | None = key_func
        self.on_limited:Callable[[], Any] = on_limited
        self.exempt_when:list[Callable[[Any], bool]] = exempt_when or []
        self.app = app
        self.cached_limits:dict[str, list[tuple[int, int]]] = {}
        self.cached_bps = {}
        self.__init_app(app)

        self.cleanup_thread = threading.Thread(
            target=cleanup_worker,
            args=(check_db_delay,purge_db_delay),
            daemon=True
        )

        self.cleanup_thread.start()

    def __init_app(self, app:Flask):
        @app.after_request
        def inject_headers(response):
            if hasattr(g, "logs"):
                logs = g.logs
                response.headers["X-RateLimit-Limit"] = str(logs.enforced_limit[0] if logs.enforced_limit is not None else logs.longest_limit_by_limit[0])
                response.headers["X-RateLimit-Remaining"] = str(logs.remaining)
                response.headers["X-RateLimit-Reset"] = str(int(logs.reset_at.timestamp()) if logs.reset_at is not None else None)
                if logs.remaining == 0:
                    response.headers["Retry-After"] = str(logs.retry_after)
            return response

        @app.before_request
        def apply_defaults():
            if request.endpoint:
                view_func = self.app.view_functions.get(request.endpoint)

                if view_func and getattr(view_func, "_is_guarded", False):
                    return

            bp = self.cached_bps.get(request.blueprint) if request.blueprint else None
            return self.__check_limit(
                getattr(bp, "limits", None) or self.limits,
                getattr(bp, "identity", None) or self.identity,
                getattr(bp, "key_gen", None) or self.key_gen,
                getattr(bp, "on_limited", None) or self.on_limited,
                getattr(bp, "exempt_when", None) or self.exempt_when
            )

        app.extensions["limiter"] = self

    def __check_limit(
        self,
        limits:list[tuple[int, int]],
        identity:Callable[[Request], Any] | None=None,
        key_gen:Callable[[Any], str] | None=None,
        on_limited:Callable[[], Any] | None=None,
        exempt_when:list[Callable[[Any], bool]]=[]
    ):
        identity_func = identity if identity is not None else self.identity
        if not callable(identity_func):
            raise NoIdentity()

        user = identity_func(request)

        exempt_when_funcs = (exempt_when or []) + (self.exempt_when or [])
        for func in exempt_when_funcs:
            if callable(func):
                if func(user):
                    return
        key_gen_func = key_gen if key_gen is not None else self.key_gen
        if not callable(key_gen_func):
            raise NoKeyFunc()
        user_id = key_gen_func(user)

        has_been_limited, logs, enforced_limit, limit_statistics, most_valuable_statistics, longest_limit_by_limit, longest_limit_by_window = pool.update_user_log(
            user_id,
            request.endpoint, datetime.now(),
            limits,
        )

        g.logs = RateLimitInfo(
            enforced_limit=enforced_limit if enforced_limit is not None else None,
            limit_statistics=limit_statistics,
            endpoint=request.endpoint,
            identity=user_id,
            logs=logs,
            retry_after=most_valuable_statistics.retry_after,
            remaining=most_valuable_statistics.remaining,
            reset_at=most_valuable_statistics.reset_at,
            longest_limit_by_limit=longest_limit_by_limit,
            longest_limit_by_window=longest_limit_by_window,
        )

        on_limited_func = on_limited or self.on_limited
        if not callable(on_limited_func):
            raise NoOnLimited()

        if has_been_limited:
            return on_limited_func()

    def guard(
        self,
        limits:list[str | tuple[int, int]],
        identity:Callable[[Request], Any] | None=None,
        key_gen:Callable[[Any], str] | None=None,
        on_limited:Callable[[], Any] | None=None,
        exempt_when:list[Callable[[Any], bool]]=[]
    ):
        def decorator(f:Callable[[], Any]):
            @wraps(f)
            def api_rate_limiter(*args, **kwargs):
                endpoint = request.endpoint
                cleaned_limits:List[tuple[int, int]]
                if endpoint in self.cached_limits:
                    cleaned_limits = self.cached_limits[endpoint]
                elif endpoint is not None:
                    cleaned_limits = [self.decode(limit) for limit in limits]
                    self.cached_limits[endpoint] = cleaned_limits
                else:
                    cleaned_limits = [self.decode(limit) for limit in limits]
                result = self.__check_limit(
                    cleaned_limits,
                    identity,
                    key_gen,
                    on_limited,
                    exempt_when
                )
                if result is not None:
                    return result
                return(f(*args, **kwargs))
            setattr(api_rate_limiter, "_is_guarded", True)
            return api_rate_limiter
        return decorator

    def decode(self, limit: str | tuple[int, int]) -> tuple[int, int]:
        if isinstance(limit, str):
            whitespace_cleaned_limit = re.sub(r'\s+', ' ', limit.replace("/", " per "))
            cleaned_limit = TIME_PATTERN.sub(
                lambda match: UNIT_MAP[match.group(0).lower()],
                whitespace_cleaned_limit
            )
            parts = cleaned_limit.split(" ", 2)
            if len(parts) != 3:
                raise InvalidLimit()

            param1, _, param2 = parts

            cleaned_param2 = re.sub(r"\s+", "", param2)

            if not cleaned_param2:
                raise InvalidTimeUnit()

            time_mult = TIME_KEYWORDS.get(cleaned_param2[-1].lower())
            if time_mult is None:
                raise InvalidTimeUnit()

            window_val = time_mult
            if len(cleaned_param2) > 1:
                window_val_str = cleaned_param2[:-1]
                if not window_val_str.isdigit():
                    raise InvalidTimeUnit()
                window_val = int(window_val_str) * time_mult

            if not param1.isdigit():
                raise InvalidLimit()

            return int(param1), window_val
        if isinstance(limit, tuple):
            if len(limit) != 2 or not all(isinstance(x, int) for x in limit):
                raise InvalidLimit()
            return limit

    def apply(
        self,
        bp:Blueprint,
        limits:list[str | tuple[int, int]],
        identity:Callable[[Request], Any] | None=None,
        key_gen:Callable[[Any], str] | None=None,
        on_limited:Callable[[], Any] | None=None,
        exempt_when:list[Callable[[Any], bool]] | None=None
    ):
        cleaned_limits = [self.decode(limit) for limit in limits]
        self.cached_bps[bp.name] = RateLimitRule(cleaned_limits, bp, identity, key_gen, on_limited, exempt_when)
