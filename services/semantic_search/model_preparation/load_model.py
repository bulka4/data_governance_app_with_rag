"""
A function for loading a model saved in the ONNX format prepared by the download_model.sh script.
"""


from transformers import AutoTokenizer
import onnxruntime as ort


def load_model(model_path):
    """
    Load a model saved in the ONNX format at the specified path. This function returns the InferenceSession object which can be used
    to generate an output using the model and the tokenizer for this model.
    """
    tokenizer = AutoTokenizer.from_pretrained(model_path)

    session = ort.InferenceSession(
        f"{model_path}/model.onnx"
    )

    return session, tokenizer


def model_output(session, tokenizer, text):
    """
    Generate model output for a given text. Arguments:
        - model, tokenizer - model and its tokenizer to use, prepared using the load_model function
        - text - text which is an input for the model
    """
    
    inputs = tokenizer(
        text,
        return_tensors="np", # return NumPy tensors
    )

    # Use "sentence_embedding" to get only a sentence embedding. To get output vectors for every input token, use "token_embeddings".
    # We can also provide both options: ["sentence_embedding", "token_embeddings"], and then:
    #   - outputs[0] - sentence embedding (of shape ['batch_size', 'embedding_dim'])
    #   - outputs[1] - token embeddings (of shape ['batch_size', 'sequence_length', 'embedding_dim'])
    outputs = session.run(
        ["sentence_embedding"],
        {
            "input_ids": inputs["input_ids"],
            "attention_mask": inputs["attention_mask"],
        },
    )

    # Return sentence embeddings
    return outputs[0]


# model usage
if __name__ == '__main__':
    session, tokenizer = load_model('./models/all-MiniLM-L6-v2')

    text = "Which tables contain customer information?"

    # output is the sentence embedding
    output = model_output(session, tokenizer, text)

    print(output.shape)