import asyncio

import typer

from contexts import AppContexts
from src.io import write_summary_to_db
from src.summarization import extract_and_reformat_summary

app = typer.Typer()

CONTEXTS = AppContexts()


@app.command()
def cli(extraction_id: str):
    contexts = asyncio.run(CONTEXTS.get_app_contexts(init_nats=False))

    summary, translated_summary, decision_number = extract_and_reformat_summary(
        extraction_id=extraction_id,
        crawler_db_engine=contexts.crawler_db_engine,
        case_db_engine=contexts.case_db_engine,
    )

    write_summary_to_db(
        case_db_engine=contexts.case_db_engine,
        decision_number=decision_number,
        summary=summary,
        translated_summary=translated_summary,
    )


if __name__ == "__main__":
    app()
