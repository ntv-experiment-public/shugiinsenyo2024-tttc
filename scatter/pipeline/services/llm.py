import os

import openai
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv("../../.env")


def request_to_openai(
    messages: list[dict],
    model: str = "gpt-4",
    is_json: bool = False,
) -> dict:
    openai.api_type = "openai" 
    response_format = {"type": "json_object"} if is_json else None
    response = openai.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0,
        n=1,
        seed=0,
        response_format=response_format,
        timeout=30
    )
    return response.choices[0].message.content


def request_to_azure_openai(
    messages: list[dict],
    model: str = "gpt-4",
    is_json: bool = False,
) -> dict:
    # Azure OpenAI設定
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version="2024-02-01",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )

    if is_json:
        response_format = {"type": "json_object"}
    else:
        response_format = None

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0,
        n=1,
        seed=0,
        response_format=response_format,
        timeout=30
    )

    return response.choices[0].message.content


def request_to_chat_openai(
    messages: list[dict],
    model: str = "gpt-4o",
    is_json: bool = False,
) -> dict:
    use_azure = os.getenv("USE_AZURE")
    if use_azure:
        model = os.getenv("AZURE_OPENAI_MODEL")
        return request_to_azure_openai(messages, model, is_json)
    else:
        return request_to_openai(messages, model, is_json)
