from pathlib import Path
import subprocess
import numpy as np
import onnxruntime as ort
from transformers import AutoTokenizer

from .EmbeddingModel import EmbeddingModel

class ONNXEmbeddingModel(EmbeddingModel):
    '''
    Implementation of the EmbeddingModel interface representing the model saved in ONNX used for generating vector embeddings.

    Using this class we can download a new model from Hugging Face and save it in the ONNX format or load already saved ONNX model
    and load this model to be ready to use.
    '''
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
        Download a new model from Hugging Face if it doesn't exist yet and save it in the ONNX format
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



    def embed(self, texts: list[str]) -> np.ndarray:
        'Generate embeddings using the loaded ONNX model.'
        if not texts:
            return np.empty((0, 0), dtype=np.float32)

        all_embeddings = []

        for start in range(
            0,
            len(texts),
            self.batch_size
        ):
            batch = texts[start : start + self.batch_size]
            embeddings = self._model_output(batch)
            all_embeddings.append(embeddings)

        return np.vstack(all_embeddings)



    def _model_output(
        self,
        texts: list[str]
    ) -> np.ndarray:
        '''
        Use the loaded model to generate embeddings for the specified texts.
        '''
        inputs = self.tokenizer(
            texts,
            return_tensors="np",
            padding=True,
            truncation=True
        )

        outputs = self.session.run(
            ["sentence_embedding"],
            {
                "input_ids": inputs["input_ids"],
                "attention_mask": inputs["attention_mask"]
            }
        )

        embeddings = outputs[0]

        return embeddings.astype(np.float32)