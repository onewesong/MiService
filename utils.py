from requests.utils import cookiejar_from_dict


from http.cookies import SimpleCookie
from requests.utils import cookiejar_from_dict

### HELP FUNCTION ###
def parse_cookie_string(cookie_string):
    cookie = SimpleCookie()
    cookie.load(cookie_string)
    cookies_dict = {}
    cookiejar = None
    for k, m in cookie.items():
        cookies_dict[k] = m.value
        cookiejar = cookiejar_from_dict(cookies_dict,
                                        cookiejar=None,
                                        overwrite=True)
    return cookiejar

