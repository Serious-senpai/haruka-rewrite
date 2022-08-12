from aiohttp import web

from env import HOST


routes = web.RouteTableDef()


@routes.get("")
async def _global_handler(request: web.Request):
    url = request.url
    if HOST == "https://haruka39-clone.herokuapp.com":
        url.host = "https://haruka39.herokuapp.com"
    else:
        url.host = "https://haruka39_clone.herokuapp.com"

    raise web.HTTPFound(url)


app = web.Application()
app.add_routes(routes)
