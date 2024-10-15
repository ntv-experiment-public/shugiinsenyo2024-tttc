"""Create labels for the clusters."""

from tqdm import tqdm
import numpy as np
import pandas as pd
from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage

from utils import messages, update_progress


BASE_SELECTION_PROMPT = """クラスタにつけられたラベル名と、紐づくデータ点のテキストを与えるので、
ラベル名と関連度の高いテキストのidを5つ出力してください

# 指示
* ラベルと各データ点のテキストを確認した上で、関連度の高いidを出力してください
* 出力はカンマ区切りで、スペースを含めずに5つのidを出力して下さい
* 出力結果は人間が閲覧するので、人間が解釈しやすいテキストを選定してください
    * 出力はWebで公開されるため過激な発言や余りにも侮辱的な発言等の閲覧者が不快感を覚えるものは選定しないでください
* 今回の分析は衆院選における意見分析を行うために実施しているため衆院選と関連性の低いものは選定しないでください
    * データソースはツイートであり、ハッシュタグのみのツイート等も含まれるため、それらは選定しないでください

# 出力例
A199_0,A308_0,A134_2,A134_1,A123_0

# ラベル名
{label}

# 各データ点のテキスト
{args_text}
"""


def select_relevant_ids_by_llm(prompt, model="gpt-4o"):
    llm = ChatOpenAI(model_name=model, temperature=0.0)
    try:
        response = llm([SystemMessage(content=prompt)])
        selected_ids = response.content.strip().split(',')
        return [id_str.strip() for id_str in selected_ids]
    except Exception as e:
        print(e)
        return []


def select_representative_args(cluster_args, label, cid, model="gpt-4o", sampling_num=50):
    arg_rows = cluster_args[
        cluster_args['cluster-id'] == cid
        ].sort_values(
            by="probability", ascending=False
        )
    # hdbscanのクラスタにおける所属確率(probability)が高い順に取得し、代表コメントの候補とする
    top_rows = arg_rows.head(sampling_num)
    args_text = "\n".join([
        f"{row['arg-id']}: {row['argument']}"
        for _, (_, row) in enumerate(top_rows.iterrows())]
    )
    prompt = BASE_SELECTION_PROMPT.format(label=label, args_text=args_text)
    selected_ids = select_relevant_ids_by_llm(prompt, model)
    return selected_ids


def update_cluster_probability(config, arguments, clusters, labels):
    cluster_args = arguments.merge(clusters, on="arg-id", how="left")
    for _, row in labels.iterrows():
        cid = row['cluster-id']
        label = row['label']
        selected_ids = select_representative_args(cluster_args, label, cid)
        for id in selected_ids:
            mask = cluster_args['arg-id'] == id
            clusters.loc[mask, 'probability'] += 100
    clusters.to_csv(f"outputs/{config['output_dir']}/clusters.csv", index=False)


def labelling(config):
    dataset = config['output_dir']
    path = f"outputs/{dataset}/labels.csv"

    arguments = pd.read_csv(f"outputs/{dataset}/args.csv")
    clusters = pd.read_csv(f"outputs/{dataset}/clusters.csv")

    results = pd.DataFrame()

    sample_size = config['labelling']['sample_size']
    prompt = config['labelling']['prompt']
    model = config['labelling']['model']

    question = config['question']
    cluster_ids = clusters['cluster-id'].unique()

    update_progress(config, total=len(cluster_ids))

    for _, cluster_id in tqdm(enumerate(cluster_ids), total=len(cluster_ids)):
        args_ids = clusters[clusters['cluster-id']
                            == cluster_id]['arg-id'].values
        args_ids = np.random.choice(args_ids, size=min(
            len(args_ids), sample_size), replace=False)
        args_sample = arguments[arguments['arg-id']
                                .isin(args_ids)]['argument'].values

        args_ids_outside = clusters[clusters['cluster-id']
                                    != cluster_id]['arg-id'].values
        args_ids_outside = np.random.choice(args_ids_outside, size=min(
            len(args_ids_outside), sample_size), replace=False)
        args_sample_outside = arguments[arguments['arg-id']
                                        .isin(args_ids_outside)]['argument'].values

        label = generate_label(question, args_sample,
                               args_sample_outside, prompt, model)
        results = pd.concat([results, pd.DataFrame(
            [{'cluster-id': cluster_id, 'label': label}])], ignore_index=True)
        update_progress(config, incr=1)

    results.to_csv(path, index=False)
    update_cluster_probability(config, arguments, clusters, results)


def generate_label(question, args_sample, args_sample_outside, prompt, model):
    llm = ChatOpenAI(model_name=model, temperature=0.0)
    outside = '\n * ' + '\n * '.join(args_sample_outside)
    inside = '\n * ' + '\n * '.join(args_sample)
    input = f"Question of the consultation:{question}\n\n" + \
        f"Examples of arguments OUTSIDE the cluster:\n {outside}" + \
        f"Examples of arguments INSIDE the cluster:\n {inside}"
    response = llm(messages=messages(prompt, input)).content.strip()
    return response
