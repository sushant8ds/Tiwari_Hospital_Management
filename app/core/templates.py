"""
Jinja2 template configuration for FastAPI HTML responses
Universally compatible across all Starlette and FastAPI versions
"""

from fastapi.templating import Jinja2Templates
from fastapi import Request
import os
import inspect

templates_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "templates"))


class CompatibleJinja2Templates(Jinja2Templates):
    """
    Template engine wrapper supporting both legacy Starlette (name, context)
    and modern Starlette (request=request, name=name, context=context) calling conventions.
    """
    
    def TemplateResponse(self, *args, **kwargs):
        name = kwargs.get("name")
        request = kwargs.get("request")
        context = kwargs.get("context", {})
        status_code = kwargs.get("status_code", 200)
        headers = kwargs.get("headers")
        media_type = kwargs.get("media_type")
        background = kwargs.get("background")
        
        # Handle positional args if provided
        if args:
            if len(args) == 1 and isinstance(args[0], str):
                name = args[0]
            elif len(args) >= 2:
                if isinstance(args[0], str):
                    name = args[0]
                    context = args[1]
                elif isinstance(args[0], Request):
                    request = args[0]
                    name = args[1]
                    if len(args) >= 3:
                        context = args[2]

        if context is None:
            context = {}
        elif not isinstance(context, dict):
            context = dict(context)
        else:
            context = context.copy()

        # Ensure request is in context
        if request and "request" not in context:
            context["request"] = request
        elif "request" in context and not request:
            request = context["request"]

        # Inspect underlying TemplateResponse method signature
        sig = inspect.signature(super().TemplateResponse)
        if "request" in sig.parameters:
            # Modern Starlette (request as explicit parameter)
            return super().TemplateResponse(
                request=request,
                name=name,
                context=context,
                status_code=status_code,
                headers=headers,
                media_type=media_type,
                background=background
            )
        else:
            # Older Starlette (context dictionary contains request)
            extra_kwargs = {}
            if headers is not None:
                extra_kwargs["headers"] = headers
            if media_type is not None:
                extra_kwargs["media_type"] = media_type
            if background is not None:
                extra_kwargs["background"] = background
                
            return super().TemplateResponse(
                name=name,
                context=context,
                status_code=status_code,
                **extra_kwargs
            )


templates = CompatibleJinja2Templates(directory=templates_dir)
