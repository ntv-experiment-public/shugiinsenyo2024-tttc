
import time
from langchain.embeddings import OpenAIEmbeddings
from langchain_openai import AzureOpenAIEmbeddings
import pandas as pd
from tqdm import tqdm

import os

from dotenv import load_dotenv
load_dotenv("../../.env")

EMBEDDING_MODEL = "text-embedding-3-large"


def embed_by_openai(args):
    if os.getenv("USE_AZURE"):
        embeds = AzureOpenAIEmbeddings(
            model=EMBEDDING_MODEL,
            azure_endpoint=os.getenv("AZURE_EMBEDDING_ENDPOINT"),
        ).embed_documents(args)
    else:
        embeds = OpenAIEmbeddings(model=EMBEDDING_MODEL).embed_documents(args)
    return embeds


def embedding(config):
    dataset = config['output_dir']
    path = f"outputs/{dataset}/embeddings.pkl"
    arguments = pd.read_csv(f"outputs/{dataset}/args.csv")
    embeddings = []
    batch_size = 1000
    for i in tqdm(range(0, len(arguments), batch_size)):
        args = arguments["argument"].tolist()[i: i + batch_size]
        embeds = embed_by_openai(args)
        embeddings.extend(embeds)
    df = pd.DataFrame(
        [
            {"arg-id": arguments.iloc[i]["arg-id"], "embedding": e}
            for i, e in enumerate(embeddings)
        ]
    )
    df.to_pickle(path)
