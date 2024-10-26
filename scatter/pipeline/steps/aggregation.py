"""Generate a convenient JSON output file."""
from pathlib import Path

import pandas as pd
import json

ROOT_DIR = Path(__file__).parent.parent.parent.parent
CONFIG_DIR = ROOT_DIR / "scatter" / "pipeline" / "configs"


def create_custom_intro(config, total_sampled_num: int):
    dataset = config['output_dir']
    args_path = f"outputs/{dataset}/args.csv"
    comments = pd.read_csv(f"inputs/{config['input']}.csv")
    result_path = f"outputs/{dataset}/result.json"

    input_count = len(comments)
    args_count = len(pd.read_csv(args_path))

    print(f"Input count: {input_count}")
    print(f"Args count: {args_count}")

    base_custom_intro = """{intro}
分析対象となったデータの件数は{input_count}件で、これらのデータに対してOpenAI APIを用いて{args_count}件の意見（議論）を抽出し、クラスタリングを行った。
"""

    intro = config["intro"]
    custom_intro = base_custom_intro.format(intro=intro, input_count=input_count, args_count=args_count)

    if total_sampled_num < args_count:
        extra_intro = "なお、クラスタ分析には前述の{args_count}件のデータを用いているが、本ページではそのうち{total_sampled_num}件のデータをサンプリングして可視化している。".format(args_count=args_count, total_sampled_num=total_sampled_num)
        custom_intro += extra_intro
    custom_intro += "一部、AIによる分析結果の中で、事実と異なる内容については削除を行った。"
    with open(result_path, "r") as f:
        result = json.load(f)
    result["config"]["intro"] = custom_intro
    with open(result_path, "w") as f:
        json.dump(result, f, indent=2)


def aggregation(config):
    path = f"outputs/{config['output_dir']}/result.json"
    total_sampling_num = config['aggregation']['sampling_num']
    print("total sampling num:", total_sampling_num)

    results = {
        "clusters": [],
        "comments": {"": {}},
        "translations": {},
        "overview": "",
        "config": config,
    }

    arguments = pd.read_csv(f"outputs/{config['output_dir']}/args.csv")
    arguments.set_index('arg-id', inplace=True)

    languages = list(config.get('translation', {}).get('languages', []))
    if len(languages) > 0:
        with open(f"outputs/{config['output_dir']}/translations.json") as f:
            translations = f.read()
        results['translations'] = json.loads(translations)

    clusters = pd.read_csv(f"outputs/{config['output_dir']}/clusters.csv")
    labels = pd.read_csv(f"outputs/{config['output_dir']}/labels.csv")
    takeaways = pd.read_csv(f"outputs/{config['output_dir']}/takeaways.csv")
    takeaways.set_index('cluster-id', inplace=True)

    print("relevant clusters score")
    print(clusters.sort_values(by="probability", ascending=False).head(10))

    clusters["x"] = clusters["x"].astype(float).round(4)
    clusters["y"] = clusters["y"].astype(float).round(4)
    clusters["probability"] = clusters["probability"].astype(float).round(1)

    with open(f"outputs/{config['output_dir']}/overview.txt") as f:
        overview = f.read()
    results['overview'] = overview

    # クラスタ事に可視化するデータをサンプルする
    # 各クラスタの件数の全体での比率をもとにサンプルする
    arguments_num = len(arguments)
    sample_rate = min(total_sampling_num / arguments_num, 1)
    total_sampled_num = 0

    sampled_comment_ids = []
    for _, row in labels.iterrows():
        cid = row['cluster-id']
        label = row['label']
        arg_rows = clusters[clusters['cluster-id'] == cid]
        c_arg_num = len(arg_rows)
        sampling_num = int(c_arg_num * sample_rate)

        if not config["aggregation"]["include_minor"] and sampling_num / total_sampling_num < 0.005:
            continue
        print(f"sampling num: {sampling_num}", c_arg_num, sample_rate)
        total_sampled_num += sampling_num
        arguments_in_cluster = []

        # pickup top 5 for representative comments
        sorted_rows = arg_rows.sort_values(by="probability", ascending=False)
        top_5 = sorted_rows.head(5)
        for _, arg_row in top_5.head(sampling_num).iterrows():
            arg_id = arg_row['arg-id']
            try:
                argument = arguments.loc[arg_id]['argument']
                comment_id = arguments.loc[arg_id]['comment-id']
                x = float(arg_row['x'])
                y = float(arg_row['y'])
                p = float(arg_row['probability'])
                obj = {
                    'arg_id': arg_id,
                    'argument': argument,
                    'comment_id': str(comment_id),
                    'x': x,
                    'y': y,
                    'p': p,
                }
                sampled_comment_ids.append(comment_id)
                arguments_in_cluster.append(obj)
            except:
                print('Error with arg_id:', arg_id)

        results['clusters'].append({
            'cluster': label,
            'cluster_id': str(cid),
            'takeaways': takeaways.loc[cid]['takeaways'],
            'arguments': arguments_in_cluster
        })

        # random sampling
        remaining = sorted_rows.iloc[5:]
        remaining_sample_size = max(0, sampling_num - 5)
        random_sample = remaining.sample(n=min(remaining_sample_size, len(remaining)), random_state=42)

        for _, arg_row in random_sample.iterrows():
            arg_id = arg_row['arg-id']
            try:
                argument = arguments.loc[arg_id]['argument']
                comment_id = arguments.loc[arg_id]['comment-id']
                x = float(arg_row['x'])
                y = float(arg_row['y'])
                p = float(arg_row['probability'])
                obj = {
                    'arg_id': arg_id,
                    'argument': argument,
                    'comment_id': str(comment_id),
                    'x': x,
                    'y': y,
                    'p': p,
                }
                sampled_comment_ids.append(comment_id)
                arguments_in_cluster.append(obj)
            except:
                print('Error with arg_id:', arg_id)

    with open(path, 'w') as file:
        json.dump(results, file, indent=2)

    create_custom_intro(config, total_sampled_num)
