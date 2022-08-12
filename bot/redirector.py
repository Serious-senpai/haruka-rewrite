from aiohttp import web

from env import HOST


routes = web.RouteTableDef()


@routes.get(r"/{path:.*}")
async def _global_handler(request: web.Request):
    if HOST == "https://haruka39-clone.herokuapp.com":
        url = request.url.with_host("haruka39.herokuapp.com")
    else:
        url = request.url.with_host("haruka39-clone.herokuapp.com")

    raise web.HTTPFound(url)


app = web.Application()
app.add_routes(routes)
