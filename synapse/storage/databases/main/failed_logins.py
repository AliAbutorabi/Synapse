from synapse.storage.database import DatabasePool, LoggingTransaction
from synapse.storage.databases.main.cache import CacheInvalidationWorkerStore
from synapse.types import JsonDict
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from synapse.http.site import RequestInfo


if TYPE_CHECKING:
    from synapse.server import HomeServer


class FailedLoginsWorkerStore(CacheInvalidationWorkerStore):
    def __init__(
        self,
        database: DatabasePool,
        db_conn,
        hs: "HomeServer",
    ):
        self.db_pool = database
        self.hs = hs
        super().__init__(database, db_conn, hs)

    async def store_failed_login(
        self,
        user_id: str,
        request_info: RequestInfo,
    ) -> None:
        """
        Store a failed login record for a user.

        Args:
            user_id: User ID (e.g. @user:example.com)
            ip_address: Client IP address
            user_agent: Client browser/application
            failure_time: Timestamp of the failed login (ISO 8601 string preferred)
        """
        failure_time = self.hs.get_clock().time_msec()
        ip_address = request_info.ip
        user_agent = request_info.user_agent
        await self.db_pool.runInteraction(
            "store_failed_login",
            self._store_failed_login_txn,
            user_id,
            ip_address,
            user_agent,
            failure_time,
        )

    def _store_failed_login_txn(
        self,
        txn: LoggingTransaction,
        user_id: str,
        ip_address: str,
        user_agent: Optional[str],
        failure_time: str,
    ) -> None:
        sql = """
            INSERT INTO failed_logins (user_id, ip_address, user_agent, failure_time)
            VALUES (?, ?, ?, ?)
        """
        txn.execute(sql, (user_id, ip_address, user_agent, failure_time))

    async def get_all_failed_logins(self, limit: int = 100, user_id: str = None):
        return await self.db_pool.runInteraction(
            "get_all_failed_logins", self._get_all_failed_logins, limit, user_id
        )

    def _get_all_failed_logins(
        self,
        txn: LoggingTransaction,
        limit: int,
        user_id: str = None,
    ):
        sql = """
            SELECT user_id, ip_address, user_agent, failure_time
            FROM failed_logins
        """

        args = []

        if user_id is not None:
            sql += " WHERE user_id = ?"
            args.append(user_id)

        sql += """
            ORDER BY failure_time DESC
            LIMIT ?
        """
        args.append(limit)

        txn.execute(sql, args)
        rows = txn.fetchall()

        return {
            "failed_logins": [
                {
                    "user_id": row[0],
                    "ip_address": row[1],
                    "user_agent": row[2],
                    "failure_time": row[3],
                }
                for row in rows
            ]
        }
        
    async def get_failed_logins(self, user_id: str) -> List[JsonDict]:
        """
        Retrieve the list of failed login records for a specific user.

        Args:
            user_id: User ID

        Returns:
            A list of dictionaries containing failed login information.
        """
        return await self.db_pool.runInteraction(
            "get_failed_logins", self._get_failed_logins_txn, user_id
        )

    def _get_failed_logins_txn(
        self, txn: LoggingTransaction, user_id: str
    ) -> List[JsonDict]:
        sql = """
            SELECT ip_address, user_agent, failure_time
            FROM failed_logins
            WHERE user_id = ?
            ORDER BY failure_time DESC
            LIMIT 100
        """
        txn.execute(sql, (user_id,))
        rows = txn.fetchall()
        return {
            "failed_logins":
            [
            {
                "ip_address": row[0],
                "user_agent": row[1],
                "failure_time": row[2],
            }
            for row in rows
            ]
        }

    async def delete_failed_logins(self, user_id: str) -> None:
        """
        Delete all failed login records for a specific user.

        Args:
            user_id: User ID
        """
        await self.db_pool.runInteraction(
            "delete_failed_logins",
            self._delete_failed_logins_txn,
            user_id,
        )

    def _delete_failed_logins_txn(self, txn: LoggingTransaction, user_id: str) -> None:
        sql = "DELETE FROM failed_logins WHERE user_id = ?"
        txn.execute(sql, (user_id,))