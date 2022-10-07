import asyncio
from json import JSONDecodeError
import logging
from aiohttp import WSMessage, WSMsgType, web
from aiohttp_apispec import docs, request_schema, setup_aiohttp_apispec
from marshmallow import ValidationError

from schemas import MessageSchema
from services import send_message, redis_listener
routes = web.RouteTableDef()

logger = logging.getLogger(__name__)


@routes.get("/ws")
async def websockets(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    asyncio.ensure_future((redis_listener(ws)))

    async for msg in ws:  # type: WSMessage
        if msg.type == WSMsgType.TEXT:
            if msg.data == "/close":
                await ws.close()
            else:
                await send_message(msg.data)
        elif msg.type == WSMsgType.ERROR:
            logger.error(f"WS connection closed with exception {request.app.ws.exception()}")
    return ws


@docs(
    tags=["telegram"],
    summary="Send message API",
    description="This end-point sends message to telegram",
)
@request_schema(MessageSchema())
@routes.post("/")
async def index_post(request: web.Request) -> web.Response:
    try:
        payload = await request.json()
    except JSONDecodeError:
        return web.json_response({"status": "Request data is invalid"})

    try:
        schema = MessageSchema()
        data = schema.load(payload)
    except ValidationError as e:
        return web.json_response({"status": "Validation Error", "error": e.messages})

    await send_message(data.get("message"))




if __name__ == "__main__":
    app = web.Application()
    setup_aiohttp_apispec(
        app=app, title="Domoed Bot documentation", version="v1.0",
        url="/api/docs/swagger.json", swagger_path="/api/docs",
    )
    app.add_routes(routes)
    web.run_app(app, port=5000)