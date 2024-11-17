from sqlalchemy.engine.base import Engine

from src.io import get_extraction_db_data_and_validate, read_pdf_from_uri
from src.module import generate_court_decision_summary


def extract_and_reformat_summary(
    extraction_id: str, crawler_db_engine: Engine, case_db_engine: Engine
) -> tuple[str, str]:
    crawler_meta, case_meta = get_extraction_db_data_and_validate(
        extraction_id=extraction_id,
        crawler_db_engine=crawler_db_engine,
        case_db_engine=case_db_engine,
    )

    doc_content, max_page = read_pdf_from_uri(crawler_meta.artifact_link)
    summary, translated_summary = generate_court_decision_summary(
        doc_content=doc_content, max_page=max_page
    )
    return summary, translated_summary, case_meta.decision_number
