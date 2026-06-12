from sklearn.impute import SimpleImputer


def numeric_imputer(strategy: str = "median") -> SimpleImputer:
    return SimpleImputer(strategy=strategy)


def categorical_imputer(strategy: str = "most_frequent") -> SimpleImputer:
    return SimpleImputer(strategy=strategy)
