from janome.tokenizer import Tokenizer

STOP_WORDS = ['の', 'に', 'は', 'を', 'た', 'が', 'で', 'て', 'と', 'し', 'れ', 'さ', 'ある', 'いる', 'も', 'する', 'から', 'な', 'こと', 'として', 'いく', 'ない']
TOKENIZER = Tokenizer()


def tokenize_japanese(text):
    return [token.surface for token in TOKENIZER.tokenize(text) if token.surface not in STOP_WORDS]