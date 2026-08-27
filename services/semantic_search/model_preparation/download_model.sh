# Download a model from a Hugging Face for creating embeddings and save it in the onnx format on the local machine.
# To use the optimum-cli tool, we need to install the "optimum-onnx" pip package (it is included in the requirements.txt file)

optimum-cli export onnx \
    --model sentence-transformers/all-MiniLM-L6-v2 \
    --library-name sentence_transformers \
    ./models/all-MiniLM-L6-v2