"""Presentation-only overlay for four HTML pages; APIs and access checks pass through."""
import re
PAGES = {"/docs": "pug-docs-page", "/redoc": "pug-docs-page", "/explorer/ui": "pug-explorer-page", "/webhooks/monitor/ui": "pug-monitor-page"}
BRAND_IMAGES = b"https://api.tifirmo.io/visitor/public/docusign-logo.svg https://api.tifirmo.io/visitor/public/python-purple.png https://api.tifirmo.io/visitor/public/fastapi-logo.svg https://api.tifirmo.io/favicon.ico https://api.tifirmo.io/api/classification/catalog/assets/pug-transparent.png https://api.tifirmo.io/api/classification/catalog/assets/docusign-developers.svg"
HEAD = b'<link rel="icon" type="image/x-icon" href="/favicon.ico?v=pug-20261103-2"><link rel="stylesheet" href="/api/classification/catalog/human.css"><script src="/api/classification/catalog/human.js" defer></script>'

class PresentationMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        page = PAGES.get(scope.get("path"))
        if scope["type"] != "http" or scope.get("method") != "GET" or not page:
            return await self.app(scope, receive, send)
        start = None
        chunks = []
        active = False

        async def themed_send(message):
            nonlocal start, active
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))
                active = message["status"] == 200 and headers.get(b"content-type", b"").startswith(b"text/html") and not headers.get(b"content-encoding")
                if active:
                    start = message
                    return
            if active and message["type"] == "http.response.body":
                chunks.append(message.get("body", b""))
                if message.get("more_body", False):
                    return
                body = b"".join(chunks)
                body = re.sub(rb'<link\b[^>]*>', lambda match: b'' if re.search(rb'\brel\s*=\s*["\'][^"\']*icon[^"\']*["\']', match[0], re.I) else match[0], body, flags=re.I)
                if b"</head>" in body and b"<body>" in body:
                    body = body.replace(b"</head>", HEAD + b"</head>", 1).replace(b"<body>", ('<body class="' + page + '">').encode(), 1)
                headers = [(k, v) for k, v in start["headers"] if k not in (b"content-length", b"etag")]
                if page == "pug-explorer-page":
                    # Keep the explorer's restrictive policy; permit only the fixed local brand and navigation files.
                    headers = [(k, v + b"; img-src " + BRAND_IMAGES if k == b"content-security-policy" and b"img-src" not in v else v) for k, v in headers]
                headers.append((b"content-length", str(len(body)).encode()))
                await send({**start, "headers": headers})
                await send({**message, "body": body})
                return
            await send(message)
        await self.app(scope, receive, themed_send)
