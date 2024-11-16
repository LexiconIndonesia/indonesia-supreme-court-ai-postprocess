import typer
from sqlmodel import create_engine

from settings import get_settings
from src.module import generate_court_decision_summary
from src.utils import get_extraction_db_data, read_pdf_from_uri

app = typer.Typer()


def extract_and_reformat_summary(extraction_id: str, contexts: dict) -> str:
    extraction_data = get_extraction_db_data(
        extraction_id=extraction_id, contexts=contexts
    )
    doc_content, max_page = read_pdf_from_uri(extraction_data.artifact_link)
    summary = generate_court_decision_summary(
        doc_content=doc_content, max_page=max_page
    )
    return summary


@app.command()
def cli(extraction_id: str):
    db_engine = create_engine(
        f"postgresql://{get_settings().db_user}:{get_settings().db_pass}@{get_settings().db_addr}/lexicon_bo_crawler"
    )

    contexts = {"db": db_engine}

    summary = extract_and_reformat_summary(
        extraction_id=extraction_id, contexts=contexts
    )
    print(summary)


if __name__ == "__main__":
    app()
