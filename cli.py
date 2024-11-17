import asyncio

import typer

from contexts import AppContexts
from src.io import write_summary_to_db
from src.summarization import extract_and_reformat_summary, sanitize_markdown_symbol

app = typer.Typer()

CONTEXTS = AppContexts()


@app.command()
def cli(extraction_id: str):
    contexts = asyncio.run(CONTEXTS.get_app_contexts(init_nats=False))

    summary, translated_summary, decision_number = asyncio.run(
        extract_and_reformat_summary(
            extraction_id=extraction_id,
            crawler_db_engine=contexts.crawler_db_engine,
            case_db_engine=contexts.case_db_engine,
        )
    )

    summary_text = sanitize_markdown_symbol(summary)
    translated_summary_text = sanitize_markdown_symbol(translated_summary)

    write_summary_to_db(
        case_db_engine=contexts.case_db_engine,
        decision_number=decision_number,
        summary=summary,
        summary_text=summary_text,
        translated_summary=translated_summary,
        translated_summary_text=translated_summary_text,
    )


if __name__ == "__main__":
    app()
