import dspy
from tqdm import tqdm


class CourtDecisionSummarizeSignature(dspy.Signature):
    """
    Given previous processed supreme court decision summary, previous page context
    and current page context from extracted supreme court decision PDF document,
    generate your own understanding of the current page context and generate the concise
    and corrected summary with the new important information.

    - Ensure that any critical important information is not missing
    - Ensure language used is in Bahasa Indonesia
    - ONLY focus on these specific informations:
        - Defendant details
        - Prosecutor's demand
        - Aggravating and mitigating circumstances
        - Supreme court final verdict ( punishment, penalty, etc..)
    - Think carefully and do not mix prosecutor demand with supreme court final verdict

    Write a summary in the style of legal expert in Bahasa Indonesia and it must be
    properly structured in markdown format which conform commonmark style

    """

    current_summary = dspy.InputField(desc="extracted summary from previous pages")
    previous_page_context = dspy.InputField(desc="previous page context")
    current_page_content = dspy.InputField(
        desc=(
            "current page content of the court decision document from PDF, maybe "
            "malformed due to PDF extraction noise"
        )
    )
    current_page_context: str = dspy.OutputField(
        desc=(
            "the current page points of context and it's relation with previous page "
            "context"
        )
    )
    improved_summary: str = dspy.OutputField(
        desc="the final improved supreme court document summary in markdown format"
    )


class CourtDecisionSummarize(dspy.Module):
    def __init__(self):
        self.summarize = dspy.ChainOfThought(CourtDecisionSummarizeSignature)

    def forward(
        self,
        current_summary: str,
        previous_page_context: str,
        current_page_content: str,
    ) -> str:
        summary = self.summarize(
            current_summary=current_summary,
            previous_page_context=previous_page_context,
            current_page_content=current_page_content,
        )
        return summary


def generate_court_decision_summary(doc_content: dict[int, str], max_page=int) -> str:
    lm = dspy.LM("openai/gpt-4o-mini", max_tokens=None)
    dspy.settings.configure(lm=lm)

    summary_generator = CourtDecisionSummarize()
    current_summary = "No summary information yet"
    previous_page_context = "No previous page context yet"
    nrof_batch_pages = 10
    combined_content = ""

    for page_number, content in tqdm(
        doc_content.items(), desc="Iterating pages for summary"
    ):
        combined_content += content + "\n"

        if page_number % nrof_batch_pages == 0 or page_number == max_page:
            generated_summary = summary_generator(
                current_summary=current_summary,
                previous_page_context=previous_page_context,
                current_page_content=combined_content,
            )

            current_summary = generated_summary.improved_summary
            previous_page_context = generated_summary.current_page_context

            combined_content = ""

    return generated_summary.improved_summary
