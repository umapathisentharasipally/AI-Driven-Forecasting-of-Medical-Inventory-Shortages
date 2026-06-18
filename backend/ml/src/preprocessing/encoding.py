from sklearn.preprocessing import OneHotEncoder


def one_hot_encoder() -> OneHotEncoder:
    return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
