from fastapi import Request
from typing import Optional

def get_full_url(request: Request, path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    if path.startswith(('http://', 'https://', 'data:')):
        return path
    
    # Get base URL from request, remove trailing slash
    base_url = str(request.base_url).rstrip('/')
    # Ensure path starts with slash
    path = path if path.startswith('/') else '/' + path
    return f"{base_url}{path}"
