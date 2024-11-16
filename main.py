import asyncio
import json
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from http import HTTPStatus
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.exceptions import HTTPException
from nats.aio.client import Client as NATS
from nats.aio.msg import Msg
from pydantic import BaseModel
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
)

from contexts import AppContexts
from nats_consumer import (
    CONSUMER_CONFIG,
    STREAM_NAME,
    STREAM_SUBJECTS,
    SUBJECT,
    close_nats_connection,
    create_job_consumer_async_task,
)
from settings import get_settings
from src.module import generate_court_decision_summary
from src.utils import get_extraction_db_data, read_pdf_from_uri


class SummarizationRequest(BaseModel):
    extraction_id: str


CONTEXTS = AppContexts()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    global CONTEXTS
    # startup event
    nats_consumer_job_connection = []
    contexts = await CONTEXTS.get_app_contexts()

    num_of_summarizer_consumer_instances = (
        get_settings().nats__num_of_summarizer_consumer_instances
    )
    nats_consumer_job_connection.extend(
        create_job_consumer_async_task(
            nats_client=contexts.nats_client,
            jetstream_client=contexts.jetstream_client,
            consumer_config=CONSUMER_CONFIG,
            processing_func=generate_summary,
            num_of_consumer_instances=num_of_summarizer_consumer_instances,
        )
    )
    yield

    # shutdown event
    for task in nats_consumer_job_connection:
        close_task = asyncio.create_task(close_nats_connection(task))
        await close_task


app = FastAPI(lifespan=lifespan)


async def generate_summary(msg: Msg) -> None:
    global CONTEXTS
    contexts = await CONTEXTS.get_app_contexts()

    data = json.loads(msg.data.decode())
    logging.info(f"processing summarization: {data}")

    extraction_data = get_extraction_db_data(
        extraction_id=data["extraction_id"], db_engine=contexts.db_engine
    )
    logging.info(f"downloading data: {extraction_data.artifact_link}")
    doc_content, max_page = read_pdf_from_uri(extraction_data.artifact_link)
    summary = generate_court_decision_summary(
        doc_content=doc_content, max_page=max_page
    )

    # TODO add english translation and save to db, optional provide HTML conversion
    print(summary)
    await msg.ack()


@app.post(
    "/chat/webhook",
    summary="Route for basecamp chatbot webhook",
)
@retry(
    wait=wait_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_attempt(5),
)
async def submit_summarization_job(
    payload: SummarizationRequest,
    app_contexts: Annotated[AppContexts, Depends(CONTEXTS.get_app_contexts)],
) -> dict:
    try:
        nats_client: NATS = app_contexts.nats_client
        js = nats_client.jetstream()

        await js.add_stream(
            name=STREAM_NAME,
            subjects=[STREAM_SUBJECTS],
        )
        ack = await js.publish(SUBJECT, payload.model_dump_json().encode())
        logging.info(f"submitted for summarization {payload} : {ack}")

    except Exception as e:
        err_msg = f"error processing summarization: {e}; RECEIVED DATA: {payload}"
        logging.error(err_msg)
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST)

    return {"data": "success"}
