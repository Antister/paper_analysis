import os

from src.python import fetch
from src.python import analyse
from src.python import predict


CACHE_DIR = ".cache"
OUTPUT_DIR = "out"


def main() -> None:
    fetch.DataFetcher(CACHE_DIR).fetch()

    res = analyse.DataAnalyser(
        os.path.join(CACHE_DIR, "dblp.xml"),
        OUTPUT_DIR,
        (2010, 2025, ["AAAI", "CVPR", "ICML", "ICCV", "IJCAI"]),
    ).result()

    print(predict.DataPredictor(res[1]).result())
