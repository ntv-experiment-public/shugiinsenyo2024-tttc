
from langchain.embeddings import OpenAIEmbeddings
import pandas as pd
from tqdm import tqdm

EMBEDDING_MODEL = "text-embedding-3-large"

def embedding(config):
    dataset = config['output_dir']
    path = f"outputs/{dataset}/embeddings.pkl"
    arguments = pd.read_csv(f"outputs/{dataset}/args.csv")
    embeddings = []
    for i in tqdm(range(0, len(arguments), 1000)):
        args = arguments["argument"].tolist()[i: i + 1000]
        embeds = OpenAIEmbeddings(model=EMBEDDING_MODEL).embed_documents(args)
        embeddings.extend(embeds)
    df = pd.DataFrame(
        [
            {"arg-id": arguments.iloc[i]["arg-id"], "embedding": e}
            for i, e in enumerate(embeddings)
        ]
    )
    df.to_pickle(path)
