"""
Functions to be used in the routes.py script
"""

from transformers import AutoTokenizer
import onnxruntime as ort
from pathlib import Path
import subprocess
import numpy as np


class EmbeddingModel():
    def __init__(
        self,
        download_model: bool = False,
        model_name: str = None,
        model_path: str = None,
        batch_size: int = 32,
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
            - batch_size - Batch size for the model - i.e. for how many texts to generate emebddings at once.
        '''
        self.batch_size = batch_size
        self.model_name = model_name
        self.model_path = Path(model_path)

        self._load_model(download_model)


    def _load_model(
        self
        ,download_model: bool = False
    ):
        '''
        Prepare the self.tokenizer and self.session attributes for using the model.

        - When download_model = False - Load already saved ONNX model
        - When download_model = True - Download a new model from Hugging Face if it doesn't exist yet, save it as ONNX and load it
        '''
        if download_model:
            if self.model_name and self.model_path:
                # Download a model if it doesn't exist yet
                if not Path(self.model_path).exists():
                    self._download_model()

                self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
                self.session = ort.InferenceSession(str(self.model_path / "model.onnx"))
            else:
                raise Exception('You need to provide the name of the model to download and the path where to save it')
        else:
            if Path(self.model_path).exists():
                # Load a saved ONNX model
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
                self.session = ort.InferenceSession(str(self.model_path / "model.onnx"))
            else:
                raise Exception(f'There is no model saved at {self.model_path}')
            


    def _download_model(self):
        '''
        Download a new model from Hugging Face if it doesn't exist yet and save it in the ONNX format.
        To use the optimum-cli CLI tool, we need to have the "optimum-onnx" pip package installed
        '''
        subprocess.run(
            [
                "optimum-cli",
                "export",
                "onnx",
                "--model",
                self.model_name,
                "--library-name",
                "sentence_transformers",
                self.model_path
            ]
            ,check=True
        )


    def run(self, text: str) -> np.array:
        """
        Run the model to generate an embedding for a given text.
        """
        inputs = self.tokenizer(
            text,
            return_tensors="np", # return NumPy tensors
        )

        # Use "sentence_embedding" to get only a sentence embedding. To get output vectors for every input token, use "token_embeddings".
        # We can also provide both options: ["sentence_embedding", "token_embeddings"], and then:
        #   - outputs[0] - sentence embedding (of shape ['batch_size', 'embedding_dim'])
        #   - outputs[1] - token embeddings (of shape ['batch_size', 'sequence_length', 'embedding_dim'])
        outputs = self.session.run(
            ["sentence_embedding"],
            {
                "input_ids": inputs["input_ids"],
                "attention_mask": inputs["attention_mask"],
            },
        )

        # Return sentence embeddings
        return outputs[0]