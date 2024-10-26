import os
import json
from tqdm import tqdm
import pandas as pd
from langchain.chat_models import ChatOpenAI
from utils import messages, update_progress
import concurrent.futures
from services.llm import request_to_chat_openai
import re
import logging

COMMA_AND_SPACE_AND_RIGHT_BRACKET = re.compile(r',\s*(\])')

def extraction(config):
    dataset = config['output_dir']
    path = f"outputs/{dataset}/args.csv"
    comments = pd.read_csv(f"inputs/{config['input']}.csv")

    model = config['extraction']['model']
    prompt = config['extraction']['prompt']
    workers = config['extraction']['workers']
    limit = config['extraction']['limit']

    comment_ids = (comments['comment-id'].values)[:limit]
    comments.set_index('comment-id', inplace=True)
    results = pd.DataFrame()
    update_progress(config, total=len(comment_ids))

    existing_arguments = set()

    for i in tqdm(range(0, len(comment_ids), workers)):
        batch = comment_ids[i: i + workers]
        batch_inputs = [comments.loc[id]['comment-body'] for id in batch]
        batch_results = extract_batch(batch_inputs, prompt, model, workers)
        for comment_id, extracted_args in zip(batch, batch_results):
            for j, arg in enumerate(extracted_args):
                if arg not in existing_arguments:
                    new_row = {"arg-id": f"A{comment_id}_{j}",
                               "comment-id": int(comment_id), "argument": arg}
                    results = pd.concat(
                        [results, pd.DataFrame([new_row])], ignore_index=True)
                    existing_arguments.add(arg)
        update_progress(config, incr=len(batch))
    results.to_csv(path, index=False)


logging.basicConfig(level=logging.ERROR)

def extract_batch(batch, prompt, model, workers):
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(
            extract_arguments, input, prompt, model) for input in list(batch)]

        done, not_done = concurrent.futures.wait(futures, timeout=30)

        results = []

        for future in not_done:
            if not future.cancelled():
                future.cancel()
            results.append([])

        for future in done:
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logging.error(f"Task {future} failed with error: {e}")
                results.append([])

        return results

def extract_by_llm(input, prompt, model):
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": input}
    ]
    response = request_to_chat_openai(messages=messages, model=model)
    return response



def extract_arguments(input, prompt, model, retries=1):

    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": input}
    ]
    try:
        response = request_to_chat_openai(messages=messages, model=model, is_json=False)
        response = COMMA_AND_SPACE_AND_RIGHT_BRACKET.sub(r'\1', response).replace("```json", "").replace("```", "")
        obj = json.loads(response)
        # LLM sometimes returns valid JSON string
        if isinstance(obj, str):
            obj = [obj]
        try:
            items = [a.strip() for a in obj]
        except Exception as e:
            print("Error:", e)
            print("Input was:", input)
            print("Response was:", response)
            print("JSON was:", obj)
            print("skip")
            items = []
        items = filter(None, items)  # omit empty strings
        return items
    except json.decoder.JSONDecodeError as e:
        print("JSON error:", e)
        print("Input was:", input)
        print("Response was:", response)
        print("Silently giving up on trying to generate valid list.")
        return []
