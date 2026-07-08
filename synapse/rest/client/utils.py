from synapse.api.errors import SynapseError, Codes, NotFoundError
from http import HTTPStatus
from synapse.types import UserID


async def authorize_user_request(store, auth, request, user_id = None):
    if user_id:
        if not UserID.is_valid(user_id):
            raise SynapseError(
                HTTPStatus.BAD_REQUEST, "Invalid user id", Codes.INVALID_PARAM
            )

        if not await store.get_user_by_id(user_id):
            raise NotFoundError("User not found")

    requester = await auth.get_user_by_req(request)
    requester_user = requester.user

    is_admin = await store.is_server_admin(requester_user.to_string())

    return is_admin, requester_user                                             

