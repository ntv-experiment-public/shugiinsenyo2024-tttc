from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage

BASE_SELECTION_PROMPT = """クラスタにつけられたラベル名と、紐づくデータ点のテキストを与えるので、
ラベル名と関連度のテキストのidを5つ出力してください

# 指示
* ラベルと各データ点のテキストを確認した上で、関連度の高いidを出力してください
* 出力はカンマ区切りで、スペースを含めずに5つのidを出力して下さい
* 出力結果は人間が閲覧するので、人間が解釈しやすいテキストを選定してください
    * 出力結果はWeb上で公開されるため、過激な発言やあまりにも侮辱的な発言や閲覧者が不快な気分になるようなテキストは選定しないでください
* 今回のクラスタ分析は、衆院選における意見分析を行うために実施しているため、衆院選と関連性の低いテキストは選定しないでください
    * データソースはツイッターから取得したツイートであり、ハッシュタグのみを含むツイート等も含まれるため、これらは除外してください

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
    arg_rows = cluster_args[cluster_args['cluster-id'] == cid].sort_values(by="probability", ascending=False)
    # hdbscanのクラスタにおける所属確率(probability)が高い順にsampling_num件取得し、代表コメントの候補とする
    top_rows = arg_rows.head(sampling_num)
    args_text = "\n".join([f"{row['arg-id']}: {row['argument']}" for _, (_, row) in enumerate(top_rows.iterrows())])
    prompt = BASE_SELECTION_PROMPT.format(label=label, args_text=args_text)
    selected_ids = select_relevant_ids_by_llm(prompt, model)
    return selected_ids
