import dspy


class CourtDecisionSummarizeSignature(dspy.Signature):
    """
    Given a court decision document, extract the judge
    """

    passage = dspy.InputField(desc="a passage to summarize")
    summary: str = dspy.OutputField(desc="a concise summary of the passage")
