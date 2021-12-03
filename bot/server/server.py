import os

from aiohttp import web


if not os.path.exists("./server"):
    os.mkdir("./server")


if not os.path.exists("./server/image"):
    os.mkdir("./server/image")


with open("./bot/server/index.html", "r") as f:
    index: str = f.read()


routes: web.RouteTableDef = web.RouteTableDef()


@routes.get("/")
async def _main_page(request: web.Request) -> web.Response:
    return web.Response(
        text=index,
        status=200,
        content_type="text/html",
    )


@routes.get("/image")
async def _image(request: web.Request) -> web.Response:
    raise web.HTTPFound("/")


routes.static("/image", "./server/image")
routes.static("/asset", "./bot/assets/server")


app: web.Application = web.Application()
app.add_routes(routes)
web.run_app(app, port=int(os.environ.get("PORT", 8080)))
