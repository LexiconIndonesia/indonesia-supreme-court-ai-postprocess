import tempfile

import requests
from sqlmodel import Field, Session, SQLModel
from unstructured.documents.elements import Footer, Header
from unstructured.partition.pdf import partition_pdf


class Extraction(SQLModel, table=True):
    id: str = Field(primary_key=True)
    artifact_link: str
    raw_page_link: str


def get_artifact_and_url_from_db(extraction_id: str, contexts: dict) -> Extraction:
    db_engine = contexts["db"]

    with Session(db_engine) as session:
        result = session.get(Extraction, extraction_id)

    return result


def read_pdf_from_uri(uri_path: str):
    with tempfile.NamedTemporaryFile(delete=True) as temp_file:
        response = requests.get(uri_path)
        temp_file.write(response.content)
        temp_file.flush()

        elements = partition_pdf(temp_file.name)

    elements = [str(el) for el in elements if type(el) not in [Header, Footer]]

    return "\n\n".join(elements)
