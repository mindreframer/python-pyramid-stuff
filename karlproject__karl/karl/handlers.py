from paste.response import has_header

def add_no_cache_headers(event):
    """ Add no-cache headers if this response doesnt already have a
    Cache-Control header"""
    response = event.response
    if response is not None:
        if not has_header(response.headerlist, 'Cache-Control'):
            response.headerlist.append(
                ('Cache-Control',
                 'private, must-revalidate'))
