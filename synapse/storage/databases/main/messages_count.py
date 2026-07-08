from .cache import CacheInvalidationWorkerStore

class MessaggesCountWorkerStore(CacheInvalidationWorkerStore):
    def __init__(
        self,
        database: DatabasePool,
        db_conn,
        hs: "HomeServer",
    ):
        self.db_pool = database
        self.hs = hs
        super().__init__(database, db_conn, hs)

    async def store_messages_count(self, user_id: str) -> List[JsonDict]:
        return await self.db_pool.runInteraction(
            "add_message_count", self._store_messages_count, user_id
        )

    def _store_messages_count(
        self, txn: LoggingTransaction, user_id: str
    ) -> List[JsonDict]:
        sql = """
        UPDATE users
        SET message_count = message_count + 1
        WHERE name = ?;
        """
        txn.execute(sql, (user_id,))