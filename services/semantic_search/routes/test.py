from interface_implementations.TransformersAnswerModel import TransformersAnswerModel
import asyncio


download_answer_model = "False"
answer_model_name = "sshleifer/tiny-gpt2"
answer_model_path = "/app/ml_models/answer/tiny-gpt2"


# Object for using a model for generating an answer
answer_model = TransformersAnswerModel(
    download_model=download_answer_model,
    model_name=answer_model_name,
    model_path=answer_model_path,
)

result = asyncio.run(answer_model.generate(
    prompt='which table contains customer data',
))

print(result)