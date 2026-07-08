from synapse.storage.database import DatabasePool, LoggingTransaction
from synapse.storage.databases.main.cache import CacheInvalidationWorkerStore
from synapse.types import JsonDict
from typing import List, Dict, Any, Optional, TYPE_CHECKING
import json
if TYPE_CHECKING:
    from synapse.server import HomeServer

class AdminRoomsWorkerStore(CacheInvalidationWorkerStore):
    def __init__(
        self,
        database: DatabasePool,
        db_conn,
        hs: "HomeServer",
    ):
        self.db_pool = database
        self.hs = hs
        super().__init__(database, db_conn, hs)

    async def get_admin_rooms(self, user_id: str, rooms: List[str]) -> List[str]:
        return await self.db_pool.runInteraction(
        "find_admin_rooms", self._get_admin_rooms_txn, rooms, user_id
        )

    def _get_admin_rooms_txn(
        self, txn: LoggingTransaction, rooms: List[str], user_id: str
        ) -> List[str]:
        admin_rooms = []
        for room_id in rooms:
            sql = """
            SELECT ej.json
            FROM events e
            JOIN event_json ej ON e.event_id = ej.event_id
            WHERE e.type = 'm.room.power_levels' AND e.room_id = ?
            ORDER BY e.origin_server_ts DESC
            LIMIT 1;
            """
            txn.execute(sql, (room_id,))
            row = txn.fetchone()
            if not row:
                continue
            try:
                content = json.loads(row[0])["content"]
                users = content.get("users", {})
                user_power = users.get(user_id,
                content.get("users_default", 0))
                if user_power >= 100:
                    admin_rooms.append(room_id)
            except Exception:
                continue
        return admin_rooms
