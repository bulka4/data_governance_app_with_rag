# answer_model.py

import asyncio
from pathlib import Path

from transformers import pipeline

from interfaces import AnswerModel


class TransformersAnswerModel(AnswerModel):
    '''
    Implementation of the AnswerModel interface representing the model saved in ONNX used for generating text.

    Using this class we can download a new model from Hugging Face and save it in the ONNX format or load already saved ONNX model
    and load this model to be ready to use.
    '''
    def __init__(
        self,
        download_model: bool = False,
        model_name: str | None = None,
        model_path: str | None = None,
        max_new_tokens: int = 100,
    ):
        '''
        Arguments:
            - download_model
                - When set to False, it will load already saved ONNX model
                - When set to True, it will download a new model from Hugging Face if it doesn't exist yet and save it in the ONNX format 
                  using optimum-cli
            - model_name, model_path
                - when download_model = True, then we need to provide both arguments:
                    - model_name - Name of the model to download using optimum-cli, e.g. sentence-transformers/all-MiniLM-L6-v2
                    - model_path - Where to save the downloaded model
                - when download_model = False, then we need to provide only the model_path argument specifying the path of the
                  ONNX model to load
        '''
        self.model_name = model_name
        self.model_path = Path(model_path)
        self.max_new_tokens = max_new_tokens

        self._load_model(download_model)



    def _load_model(self, download_model: bool = False):
        '''
        Prepare the self.tokenizer and self.session attributes for using the model.

        - When download_model = False - Load already saved ONNX model
        - When download_model = True - Download a new model from Hugging Face if it doesn't exist yet, save it as ONNX and load it
        '''
        if download_model:
            if self.model_name and self.model_path:
                if not self.model_path.exists():
                    self._download_model()

                self.model = pipeline(
                    "text-generation",
                    model=self.model_path,
                )
            else:
                raise Exception(
                    "model_name and model_path must be provided "
                    "when download_model=True"
                )

        else:
            if self.model_path.exists():
                self.model = pipeline(
                    "text-generation",
                    model=self.model_path,
                )
            else:
                raise Exception(
                    f"Model path does not exist: {self.model_path}"
                )



    def _download_model(self):
        '''
        Download a new model from Hugging Face.
        '''
        model = pipeline(
            "text-generation",
            model=self.model_name,
        )

        self.model_path.mkdir(
            parents=True,
            exist_ok=True,
        )

        model.save_pretrained(self.model_path)



    async def generate(
        self,
        prompt: str,
        max_new_tokens: int = 100,
    ) -> str:
        'Generate an answer to a question.'
        
        result = await asyncio.to_thread(
            self.model,
            prompt,
            max_new_tokens=max_new_tokens,
        )

        return result[0]["generated_text"]