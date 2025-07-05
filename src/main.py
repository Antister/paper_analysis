import logging
import analyse
import fetch


def main() -> None:
    logging.basicConfig(level=logging.INFO)

    fetch.DataFetcher("cache").fetch()

    analyse.DataAnalyser(
        "cache/dblp.xml",
        "out",
        (2010, 2025, ["AAAI", "CVPR", "ICML", "ICCV", "IJCAI"]),
    )


if __name__ == "__main__":
    main()
