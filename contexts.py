from sqlmodel import create_engine

from nats_consumer import (
    generate_nats_stream_configs,
    initialize_jetstream_client,
    initialize_nats,
)
from settings import get_settings


class AppContexts:
    def __init__(self):
        self.nats_client = None
        self.jetstream_client = None
        self.db_engine = create_engine(
            f"postgresql://{get_settings().db_user}:{get_settings().db_pass}@{get_settings().db_addr}/lexicon_bo_crawler"
        )

    async def get_app_contexts(self) -> "AppContexts":
        if self.nats_client is None:
            self.nats_client = await initialize_nats()
        if self.jetstream_client is None:
            stream_configs = generate_nats_stream_configs()
            self.jetstream_client = await initialize_jetstream_client(
                nats_client=self.nats_client,
                stream_configs=stream_configs,
            )

        return self
