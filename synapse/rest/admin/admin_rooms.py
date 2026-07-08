from synapse.http.servlet import RestServlet, parse_integer
from synapse.http.server import HttpServer
from synapse.rest.admin._base import (
    admin_patterns,
    assert_requester_is_admin,
)
from synapse.http.site import SynapseRequest
from synapse.event_auth import get_named_level, get_power_level_event


class AdminRoomsServLetV4(RestServlet):
    PATTERNS = admin_patterns("/admin_rooms/(?P<user_id>[^/]*)$", "v4")
    """
    GET /adminrooms/{user_id}/
    """

    def __init__(self, hs: "HomeServer"):
        self.auth = hs.get_auth()
        self.store = hs.get_datastores().main

    async def on_GET(self, request: SynapseRequest, user_id: str):
        await assert_requester_is_admin(self.auth, request)
        limit = parse_integer(request, "limit", default=100)
        if limit == None:
            limit = 100

        room_ids = await self.store.get_rooms_for_user(user_id, limit=limit)
        room_ids = list(room_ids)
        admin_room_ids = await self.store.get_admin_rooms(
            user_id=user_id, rooms=room_ids
        )
        return 200, {"admin_rooms": admin_room_ids, "total": len(admin_room_ids)}

    def register_servlets(hs: "HomeServer", http_server: HttpServer) -> None:
        AccountDataServlet(hs).register(http_server)
