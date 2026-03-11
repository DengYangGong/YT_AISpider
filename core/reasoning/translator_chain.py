from transformers import pipeline
from langchain_community.llms import HuggingFacePipeline

from .prompt_templates import TRANSLATION_PROMPT


class TranslatorChain:

    def __init__(self, model_path):

        pipe = pipeline(
            "text-generation",
            model=model_path,
            device=0,
            max_new_tokens=200,
        )

        self.llm = HuggingFacePipeline(pipeline=pipe)

        self.chain = TRANSLATION_PROMPT | self.llm

    def translate(self, text, context="", knowledge=""):

        result = self.chain.invoke({
            "text": text,
            "context": context,
            "knowledge": knowledge
        })

        return result