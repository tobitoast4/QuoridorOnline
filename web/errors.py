"""This module cares of occuring exceptions. There are 2 'types' the are handled:

1. Exceptions occuring within api views (methods with @api_view decorator) -> custom_exception_handler
   We use these exceptions (error code 599; see also yart/web/static/js/fetch_api.js) to get better
   details of what failed during processing the api request.

2. Exceptions occuring within the rest of the views (those for rendering the pages) -> ErrorProcessingMiddleware
   This middleware is registered in yart/conf/settings.py.
   By default, these exceptions lead to the default (light-yellow) django error page.
"""

import traceback

from django.contrib import messages
from django.shortcuts import redirect
from rest_framework.response import Response
from rest_framework.views import exception_handler


class QuoridorOnlineGameError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __repr__(self):
        return self.msg


def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)
    if response is None:
        return Response(
            {
                "type": exc.__class__.__name__,
                "error": str(exc),
            },
            599,
        )
    return response


class ErrorProcessingMiddleware:
    # Middleware for setting hooks into Django’s request/response processing
    # See https://docs.djangoproject.com/en/3.0/topics/http/middleware/
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        response = self.get_response(request)
        # Code to be executed for each request/response after
        # the view is called.
        if response.status_code == 404:
            if (
                hasattr(response, "path")
                and ".well-known/appspecific/com.chrome.devtools.json" in response.path
            ):
                # Path requested by Chrome. If we dont pass the response here, 404 appears often in the Notify.
                return response
            messages.add_message(
                request,
                messages.ERROR,
                "The requested resource was not found on this server.",
                extra_tags="404 Not Found",
            )
            return redirect("home")
        return response

    def process_exception(self, request, exception):
        # Process exceptions in requests.
        # See https://docs.djangoproject.com/en/3.0/topics/http/middleware/#process-exception
        messages.add_message(
            request, messages.ERROR, exception, extra_tags=str(type(exception).__name__)
        )
        if "HTTP_REFERER" in request.META:
            return redirect(request.META["HTTP_REFERER"])
        return redirect("home")
