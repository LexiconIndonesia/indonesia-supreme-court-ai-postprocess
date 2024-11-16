import typer
from sqlmodel import create_engine

from settings import get_settings
from src.module import generate_court_decision_summary
from src.utils import get_extraction_db_data, read_pdf_from_uri

app = typer.Typer()


def extract_and_reformat_summary(extraction_id: str, contexts: dict) -> tuple[str, str]:
    extraction_data = get_extraction_db_data(
        extraction_id=extraction_id, db_engine=contexts["db"]
    )

    doc_content, max_page = read_pdf_from_uri(extraction_data.artifact_link)
    summary, translated_summary = generate_court_decision_summary(
        doc_content=doc_content, max_page=max_page
    )
    return summary, translated_summary


@app.command()
def cli(extraction_id: str):
    db_engine = create_engine(
        f"postgresql://{get_settings().db_user}:{get_settings().db_pass}@{get_settings().db_addr}/lexicon_bo_crawler"
    )

    contexts = {"db": db_engine}

    summary, translated_summary = extract_and_reformat_summary(
        extraction_id=extraction_id, contexts=contexts
    )
    print(summary)
    print(translated_summary)


if __name__ == "__main__":
    app()
