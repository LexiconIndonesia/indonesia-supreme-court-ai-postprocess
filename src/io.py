import tempfile

import aiofiles
from httpx import AsyncClient
from sqlalchemy.engine.base import Engine
from sqlmodel import Column, Field, Session, SQLModel, String, select
from tenacity import (
    retry,
    retry_if_not_exception_type,
    stop_after_attempt,
    wait_exponential,
)
from unstructured.documents.elements import Footer, Header
from unstructured.partition.pdf import partition_pdf

from settings import get_settings


class Extraction(SQLModel, table=True):
    id: str = Field(primary_key=True)
    artifact_link: str
    raw_page_link: str
    metadata_: str | None = Field(
        sa_column=Column("metadata", String, default=None)
    )  # somehow this converted to dict already


class Cases(SQLModel, table=True):
    id: str = Field(primary_key=True)
    decision_number: str
    summary: str | None
    summary_en: str | None
    summary_formatted: str | None
    summary_formatted_en: str | None


@retry(
    wait=wait_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_attempt(5),
    reraise=True,
    retry=retry_if_not_exception_type((ValueError, NotImplementedError)),
)
def get_extraction_db_data_and_validate(
    extraction_id: str, crawler_db_engine: Engine, case_db_engine: Engine
) -> tuple[Extraction, Cases]:
    with Session(crawler_db_engine) as session:
        crawler_meta = session.get(Extraction, extraction_id)

    if not crawler_meta:
        raise ValueError(f"extraction id {extraction_id} not found")

    if not crawler_meta.raw_page_link.startswith(
        "https://putusan3.mahkamahagung.go.id"
    ):
        raise NotImplementedError("only support supreme court document")

    decision_number = crawler_meta.metadata_.get("number", None)
    if decision_number is None:
        raise ValueError(
            "case number identifier not found in `extraction` table : "
            f"{crawler_meta.metadata_}"
        )

    with Session(case_db_engine) as session:
        case_meta = [
            result
            for result in session.exec(
                select(Cases).where(Cases.decision_number == decision_number)
            )
        ]

    if not case_meta:
        raise ValueError(
            "case number identifier not found in `cases` table : "
            f"{crawler_meta.metadata_}"
        )

    return crawler_meta, case_meta[0]


@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    stop=stop_after_attempt(5),
    reraise=True,
)
async def read_pdf_from_uri(uri_path: str) -> tuple[dict[int, str], int]:
    print(f"downloading file from {uri_path}")
    with tempfile.NamedTemporaryFile(delete=True) as temp_file:
        async with AsyncClient(
            timeout=get_settings().async_http_request_timeout
        ) as client:
            response = await client.get(uri_path)

        async with aiofiles.open(temp_file.name, "wb") as afp:
            await afp.write(response.content)
            await afp.flush()

        elements = partition_pdf(temp_file.name)

    contents = {}
    for el in elements:
        if type(el) in [Header, Footer]:
            continue

        current_page = el.metadata.page_number
        current_content = contents.get(current_page, "")
        current_content += "\n" + str(el)
        contents[current_page] = current_content

    max_page = current_page

    return contents, max_page


def write_summary_to_db(
    case_db_engine: Engine,
    decision_number: str,
    summary: str,
    summary_text: str,
    translated_summary: str,
    translated_summary_text: str,
):
    with Session(case_db_engine) as session:
        statement = select(Cases).where(Cases.decision_number == decision_number)
        results = session.exec(statement)
        case = results.one()

        case.summary = summary_text
        case.summary_en = translated_summary_text
        case.summary_formatted = summary
        case.summary_formatted_en = translated_summary
        session.add(case)
        session.commit()
        session.refresh(case)

    print(f"updated summary decision number {decision_number}")
