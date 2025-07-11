import os
import time
import typing
import logging

from src.python import fetch
from src.python import parse
from src.python import analyse
from src.python import predict


CACHE_DIR = ".cache"
OUTPUT_DIR = "out"


def __do_validation(
    html_data: list[parse.paper_t], xml_data: list[parse.paper_t]
) -> None:
    import check  # type: ignore

    logger = logging.getLogger("[Main]")
    logger.info("Validating HTML data against XML data")

    start = time.perf_counter_ns()
    result = check.validate_html_data(
        html_data, xml_data, typing.cast(int, os.cpu_count()) * 2
    )
    end = time.perf_counter_ns()

    logger.warning(
        "Following titles are mismatched, which could not be precisely matched in XML data"
    )
    for i in result:
        logger.warning(html_data[i][0:3])
    logger.info(f"Validation done, {(end - start) / 10**9} seconds elapsed")


def main() -> None:
    FETCH_RANGE = (2020, 2024)
    ANALYSE_RANGE = (2010, 2025)
    FETCH_CONFERENCE = ["AAAI", "CVPR", "ICSE"]
    ANALYSE_CONFERENCE = ["AAAI", "CVPR", "ICML", "ICCV", "IJCAI", "ICSE"]

    # Fetch data from internet
    xml_path = fetch.XMLFetcher(CACHE_DIR).fetch()[0]
    html_paths = fetch.HTMLFetcher(CACHE_DIR).fetch(
        FETCH_RANGE[0],
        FETCH_RANGE[1],
        FETCH_CONFERENCE,
    )

    # Parsing content into structured data
    html_data = parse.HTMLParser(html_paths).parse()
    xml_data = parse.XMLParser(xml_path).parse(
        lambda paper: paper[1] in range(ANALYSE_RANGE[0], ANALYSE_RANGE[1])
    )

    # Validate html content with dblp.xml
    __do_validation(html_data, xml_data)

    # Analyse the data
    analyse_result = (
        analyse.DataAnalyser(
            OUTPUT_DIR,
            xml_data,
            (ANALYSE_RANGE[0], ANALYSE_RANGE[1], ANALYSE_CONFERENCE),
        )
        .analyse()
        .result()
    )

    # Predict next year
    for conference, count in predict.DataPredictor(analyse_result).result().items():
        logging.getLogger("[Main]").info(
            f"{conference} will have {count} papers next year"
        )
