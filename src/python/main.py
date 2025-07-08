import pickle
from src.python import fetch
from src.python import parse
from src.python import analyse
from src.python import predict


CACHE_DIR = ".cache"
OUTPUT_DIR = "out"


def __validate_html_data(
    html_data: list[parse.paper_t], xml_data: list[parse.paper_t]
) -> bool:
    is_match = False
    ret = True

    for phtml in html_data:
        for pxml in xml_data:
            if phtml[2] == pxml[2]:
                is_match = True
                break

        if is_match:
            is_match = False
        else:
            print(f"Dismatch detected!\nHTML:{phtml}")
            ret = False

    return ret


def main() -> None:
    html_paths = fetch.HTMLFetcher(CACHE_DIR).fetch()
    xml_path = fetch.XMLFetcher(CACHE_DIR).fetch()[0]

    html_data = parse.HTMLParser(html_paths).parse()
    if 0:
        xml_data = parse.XMLParser(xml_path).parse(
            lambda paper: paper[1] in range(2010, 2025)
        )
        with open(".cache/dblp.pkl", "wb") as data:
            pickle.dump(xml_data, data)
    else:
        with open(".cache/dblp.pkl", "rb") as data:
            xml_data = pickle.loads(data.read())

    assert __validate_html_data(html_data, xml_data)

    res = (
        analyse.DataAnalyser(
            OUTPUT_DIR,
            xml_data,
            (2010, 2025, ["AAAI", "CVPR", "ICML", "ICCV", "IJCAI"]),
        )
        .analyse()
        .result()
    )

    print(predict.DataPredictor(res).result())
