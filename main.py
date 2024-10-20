import typer
from sqlmodel import create_engine

from settings import get_settings
from src.utils import get_artifact_and_url_from_db, read_pdf_from_uri

app = typer.Typer()


@app.command()
def extract_summary(extraction_id: str):
    db_engine = create_engine(
        f"postgresql://{get_settings().db_user}:{get_settings().db_pass}@{get_settings().db_addr}/lexicon_bo_crawler"
    )

    contexts = {"db": db_engine}

    extraction_data = get_artifact_and_url_from_db(
        extraction_id=extraction_id, contexts=contexts
    )
    doc_content = read_pdf_from_uri(extraction_data.artifact_link)
    print(doc_content)


if __name__ == "__main__":
    app()
