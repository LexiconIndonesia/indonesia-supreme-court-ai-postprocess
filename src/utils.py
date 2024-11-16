import tempfile

import requests
from sqlalchemy.engine.base import Engine
from sqlmodel import Field, Session, SQLModel
from unstructured.documents.elements import Footer, Header
from unstructured.partition.pdf import partition_pdf


class Extraction(SQLModel, table=True):
    id: str = Field(primary_key=True)
    site_content: str
    artifact_link: str
    raw_page_link: str


def get_extraction_db_data(extraction_id: str, db_engine: Engine) -> Extraction:
    with Session(db_engine) as session:
        result = session.get(Extraction, extraction_id)

    return result


def read_pdf_from_uri(uri_path: str) -> tuple[dict[int, str], int]:
    with tempfile.NamedTemporaryFile(delete=True) as temp_file:
        response = requests.get(uri_path)
        temp_file.write(response.content)
        temp_file.flush()

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
