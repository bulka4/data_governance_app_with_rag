'''
Another version of the TransformersAnswerModel.py script. Here we use ORTModelForCausalLM instead of onnxruntime.InferenceSession. 

The ORTModelForCausalLM is much easier to use for text generation.
'''

from pathlib import Path
import asyncio
import subprocess

from transformers import AutoTokenizer
from optimum.onnxruntime import ORTModelForCausalLM

from interfaces import AnswerModel


class TransformersAnswerModel(AnswerModel):
    """
    Implementation of the AnswerModel interface representing the model saved in ONNX used for generating text.
    
    Using this class we can download a new model from Hugging Face and save it in the ONNX format or load already saved ONNX model
    and load this model to be ready to use.
    """
    def __init__(
        self,
        download_model: bool = False,
        model_name: str | None = None,
        model_path: str | None = None,
        max_new_tokens: int = 100,
    ):
        """
        Arguments:
            - download_model
                - When set to False, it will load already saved ONNX model
                - When set to True, it will download a new model from Hugging Face if it doesn't exist yet and save it in the ONNX format 
                    using optimum-cli
            - model_name, model_path
                - when download_model = True, then we need to provide both arguments:
                    - model_name - Name of the model to download using transformers.pipeline("text-generation", model=model_name)
                    - model_path - Where to save the downloaded model
                - when download_model = False, then we need to provide only the model_path argument specifying the path of the
                    ONNX model to load
        """

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
                self._download_model()
            else:
                raise Exception(
                    "model_name and model_path must be provided "
                    "when download_model=True"
                )
        else:
            if not self.model_path.exists():
                raise Exception(
                    f"Model path does not exist: {self.model_path}"
                )

        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_path
        )

        self.model = ORTModelForCausalLM.from_pretrained(
            self.model_path,
            provider="CPUExecutionProvider",
            use_cache=False,
        )



    def _download_model(self):
        """
        Download a Hugging Face causal language model and export it to ONNX using optimum-cli.
        """

        self.model_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        subprocess.run(
            [
                "optimum-cli",
                "export",
                "onnx",
                "--model",
                self.model_name,
                # --task text-generation will cause that we will not be using KV caching
                # use --task text-generation-with-past to enable KV caching
                "--task",
                "text-generation",
                self.model_path,
            ],
            check=True,
        )



    async def generate(
        self,
        prompt: str,
        max_new_tokens: int = 300,
    ) -> str:
        """
        Generate text using the ONNX model.
        """

        if max_new_tokens is None:
            max_new_tokens = self.max_new_tokens

        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
        )

        result = await asyncio.to_thread(
            self.model.generate,
            **inputs,
            max_new_tokens=max_new_tokens,
            use_cache=False,
        )

        input_length = inputs["input_ids"].shape[1]
        # result[0] is the answer to the prompt with the prompt itself, of the format: prompt + answer
        # generated_tokens excludes the prompt and contains only the answer to the prompt
        generated_tokens = result[0][input_length:]

        return self.tokenizer.decode(
            generated_tokens,
            skip_special_tokens=True,
        )