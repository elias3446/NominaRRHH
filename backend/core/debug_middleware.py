import logging

logger = logging.getLogger(__name__)

class DebugRequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        cookies_in = list(request.COOKIES.keys())
        logger.info(f">>> REQ {request.method} {request.path} | IN-Cookies: {cookies_in}")
        response = self.get_response(request)
        # Capturar todos los headers Set-Cookie del response
        set_cookie_headers = response.cookies
        cookie_summary = {k: f"value={'[SET]' if v.value else '[EMPTY]'}, path={v['path']}, samesite={v['samesite']}, secure={v['secure']}, httponly={v['httponly']}" 
                         for k, v in set_cookie_headers.items()}
        logger.info(f"<<< RES {response.status_code} {request.path} | SET-Cookies: {cookie_summary}")
        return response
