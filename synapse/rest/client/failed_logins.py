from synapse.http.server import respond_with_json
from synapse.http.servlet import RestServlet
from twisted.web.server import Request
from synapse.http.server import HttpServer

from synapse.rest.client._base import client_patterns
from synapse.types import JsonDict, UserID
from synapse.api.errors import SynapseError, Codes, NotFoundError
from http import HTTPStatus

from synapse.http.servlet import (
    assert_params_in_dict,
    parse_bytes_from_args,
    parse_json_object_from_request,
    parse_string,
)

from .utils import authorize_user_request

class AllFailedLoginsServlet(RestServlet):
    PATTERNS = client_patterns("/failed_logins")

    def __init__(self, hs):
        self.hs = hs
        self.auth = hs.get_auth()
        self.store = hs.get_datastores().main
        super().__init__()

    async def on_GET(self, request: Request):
        is_admin, requester_user = await authorize_user_request(self.store, self.auth, request)

        if not is_admin:
            raise SynapseError(
                HTTPStatus.FORBIDDEN,
                "You are not allowed to access thid data",
                Codes.FORBIDDEN,
            )

        limit = parse_string(request, "limit", required = False)
        user_id = parse_string(request, "user_id", required = False)

        if limit == None:
            limit = 100
        ret = await self.store.get_all_failed_logins(limit = limit, user_id = user_id)
        return 200, ret


class FailedLoginsServlet(RestServlet):
    PATTERNS = client_patterns("/failed_logins/(?P<user_id>[^/]*)")

    def __init__(self, hs):
        self.hs = hs
        self.auth = hs.get_auth()
        self.store = hs.get_datastores().main
        super().__init__()

    async def on_GET(self, request: Request, user_id: str):
        is_admin, requester_user = await authorize_user_request(self.store, self.auth, request, user_id)

        if not is_admin:
            if requester_user.to_string() != user_id:
                raise SynapseError(
                    HTTPStatus.FORBIDDEN,
                    "You are not allowed to access this user's data",
                    Codes.FORBIDDEN,
                )

        ret = await self.store.get_failed_logins(user_id)
        return 200, ret

    async def on_DELETE(self, request: Request, user_id: str):
        is_admin, _ = await authorize_user_request(self.store, self.auth, request, user_id)

        if not is_admin:
            raise SynapseError(
                HTTPStatus.FORBIDDEN,
                "You are not allowed to access this user's data",
                Codes.FORBIDDEN,
            )

        await self.store.delete_failed_logins(user_id)
        return 200, {"result": "success", "message": f"All failed login attempts for {user_id} deleted."}



def register_servlets(hs: "HomeServer", http_server: HttpServer) -> None:
    FailedLoginsServlet(hs).register(http_server)
    AllFailedLoginsServlet(hs).register(http_server)                                                    
    
    
