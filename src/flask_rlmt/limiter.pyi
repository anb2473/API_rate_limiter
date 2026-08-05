from typing import Callable, Any
from flask import Request, Blueprint, Flask

class Limiter:
    def __init__(
        self,
        app:Flask,
        rules:list[str | tuple[int, int]] | None=None,
        identity:Callable[[Request], Any]=...,
        key_func:Callable[[Any], str]=...,
        on_limited:Callable[[], Any]=...,
        exempt_when:list[Callable[[Any], bool]] | None=None,
        check_db_delay:int=60,
        purge_db_delay:int=900
    ) -> None:
        """Creates a new Limiter.

        Creates a new limiter and accepts global defaults which will apply to
        all defined routes EXCEPT for routes rule limit decorators or the routes
        in a blueprint with rate limiting applied.

        Args:
            app: The Flask app
            rules: A list of rate limit rules. Each limit can be formed as a string
                (e.g, "10 per min" or "10/1m") or tuples (e.g., (10, 60)). Further
                details on allowed strings are at the end of this doc.
            identity: A functions which takes the incoming Flask Request object and
                returns a object representing the users identity (e.g., the default
                "lambda request: request.remote_addr" identifies users by their IP)
            key_func: A function which takes the object representing the user
                and converts it into a string ID to which the users logs can be
                assigned.(e.g., the default "lambda user: str(user)" simply
                takes the given user object and converts it to a string)
            on_limited: A function which defines what should be returned if the
                rate limit policy is violated. (The default returns a 429, and is pasted
                at the end of this doc)
            exempt_when: A list of functions which takes the user object from the identity
                function and returns a boolean determining whether the rate limiting rules
                should apply to the given user
            check_db_delay: An integer for how many seconds the database should wait before
                checking for old logs to remove.
            purge_db_delay: An integer for many seconds of idling before a user should be
                pruned from the database.

        Further details:
            rule string formatting requirements:
                - String MUST start with a number (the number of requests)
                - Following the number of requests must be either "/" or " per "
                  (If using "per", you MUST wrap the symbol in spaces)
                - Extra spaces are allowed (e.g., " / " or "  per  ")
                - Lastly a time denominator (e.g., "minute", "hr", "d", etc)
                  must be included. A number may also be added before the denominator.
                  (e.g., "10 seconds" or "5secs")
            default on_limited:
                def json_on_limited():
                    (
                        enforced_limit, limit_statistics,
                        endpoint,
                        identity,
                        logs,
                        retry_after,
                        remaining,
                        reset_at,
                        longest_limit_by_limit,
                        longest_limit_by_window
                    ) = g.logs
                    return jsonify({
                        "status": 429,
                        "error": "Rate Limit Exceeded",
                        "retry_after": retry_after,
                        "remaining": remaining,
                        "reset_at": reset_at.isoformat(),
                        "limit": enforced_limit[0] if enforced_limit else longest_limit_by_limit[0],
                        "window": enforced_limit[1] if enforced_limit else None,
                        "endpoint": endpoint,
                        "identity": identity,
                    }), 429
        """

    def guard(
        self,
        rules:list[str | tuple[int, int]],
        identity:Callable[[Request], Any] | None=None,
        key_gen:Callable[[Any], str] | None=None,
        on_limited:Callable[[], Any] | None=None,
        exempt_when:list[Callable[[Any], bool]]=[]
    ) -> Callable[..., Any]:
        """Apply rate limit rules to a route.

        This is a decorator which intercepts the incoming requests for a given
        endpoint and applies the given rate limit rules. The rules set for the blueprint
        will override all global rule limits along with any rate limits for blueprint it is
        a part of.

        Args:
            rules: A list of rate limit rules. Each limit can be formed as a string
                (e.g, "10 per min" or "10/1m") or tuples (e.g., (10, 60)). Further
                details on allowed strings are at the end of this doc.
            identity: A functions which takes the incoming Flask Request object and
                returns a object representing the users identity (e.g., the default
                "lambda request: request.remote_addr" identifies users by their IP)
            key_func: A function which takes the object representing the user
                and converts it into a string ID to which the users logs can be
                assigned.(e.g., the default "lambda user: str(user)" simply
                takes the given user object and converts it to a string)
            on_limited: A function which defines what should be returned if the
                rate limit policy is violated. (The default returns a 429, and is pasted
                at the end of this doc)
            exempt_when: A list of functions which takes the user object from the identity
                function and returns a boolean determining whether the rate limiting rules
                should apply to the given user

        Returns:
            A decorator function that wraps the target route.

        Further details:
            rule string formatting requirements:
                - String MUST start with a number (the number of requests)
                - Following the number of requests must be either "/" or " per "
                  (If using "per", you MUST wrap the symbol in spaces)
                - Extra spaces are allowed (e.g., " / " or "  per  ")
                - Lastly a time denominator (e.g., "minute", "hr", "d", etc)
                  must be included. A number may also be added before the denominator.
                  (e.g., "10 seconds" or "5secs")
            default on_limited:
                def json_on_limited():
                    (
                        enforced_limit, limit_statistics,
                        endpoint,
                        identity,
                        logs,
                        retry_after,
                        remaining,
                        reset_at,
                        longest_limit_by_limit,
                        longest_limit_by_window
                    ) = g.logs
                    return jsonify({
                        "status": 429,
                        "error": "Rate Limit Exceeded",
                        "retry_after": retry_after,
                        "remaining": remaining,
                        "reset_at": reset_at.isoformat(),
                        "limit": enforced_limit[0] if enforced_limit else longest_limit_by_limit[0],
                        "window": enforced_limit[1] if enforced_limit else None,
                        "endpoint": endpoint,
                        "identity": identity,
                    }), 429
        """

    def apply(
        self,
        bp:Blueprint,
        rules:list[str | tuple[int, int]],
        identity:Callable[[Request], Any] | None=None,
        key_gen:Callable[[Any], str] | None=None,
        on_limited:Callable[[], Any] | None=None,
        exempt_when:list[Callable[[Any], bool]] | None=None
    ) -> None:
        """Applies rate limit rules to a blueprint.

        Applies rate limit rules to all routes within a specific blueprint EXCEPT the routes with
        rule limit decorators. The rules set for the blueprint will override all global
        rules. (NOTE: Apply must be called directly before the blueprint is registered)

        Args:
            bp: The blueprint upon which the rules should be applied.
            rules: A list of rate limit rules. Each limit can be formed as a string
                (e.g, "10 per min" or "10/1m") or tuples (e.g., (10, 60)). Further
                details on allowed strings are at the end of this doc.
            identity: A functions which takes the incoming Flask Request object and
                returns a object representing the users identity (e.g., the default
                "lambda request: request.remote_addr" identifies users by their IP)
            key_func: A function which takes the object representing the user
                and converts it into a string ID to which the users logs can be
                assigned.(e.g., the default "lambda user: str(user)" simply
                takes the given user object and converts it to a string)
            on_limited: A function which defines what should be returned if the
                rate limit policy is violated. (The default returns a 429, and is pasted
                at the end of this doc)
            exempt_when: A list of functions which takes the user object from the identity
                function and returns a boolean determining whether the rate limiting rules
                should apply to the given user

        Further details:
            rule string formatting requirements:
                - String MUST start with a number (the number of requests)
                - Following the number of requests must be either "/" or " per "
                  (If using "per", you MUST wrap the symbol in spaces)
                - Extra spaces are allowed (e.g., " / " or "  per  ")
                - Lastly a time denominator (e.g., "minute", "hr", "d", etc)
                  must be included. A number may also be added before the denominator.
                  (e.g., "10 seconds" or "5secs")
            default on_limited:
                def json_on_limited():
                    (
                        enforced_limit, limit_statistics,
                        endpoint,
                        identity,
                        logs,
                        retry_after,
                        remaining,
                        reset_at,
                        longest_limit_by_limit,
                        longest_limit_by_window
                    ) = g.logs
                    return jsonify({
                        "status": 429,
                        "error": "Rate Limit Exceeded",
                        "retry_after": retry_after,
                        "remaining": remaining,
                        "reset_at": reset_at.isoformat(),
                        "limit": enforced_limit[0] if enforced_limit else longest_limit_by_limit[0],
                        "window": enforced_limit[1] if enforced_limit else None,
                        "endpoint": endpoint,
                        "identity": identity,
                    }), 429
        """
