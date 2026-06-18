from sklearn.ensemble import IsolationForest


def build_isolation_forest(contamination: float = 0.03, random_state: int = 42) -> IsolationForest:
    return IsolationForest(n_estimators=300, contamination=contamination, random_state=random_state, n_jobs=-1)
