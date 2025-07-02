import os
import gzip
import logging
import urllib.request


class DataFetcher:
    FILES = {
        "dblp.xml.gz": "https://dblp.org/xml/dblp.xml.gz",
        "dblp.dtd": "https://dblp.org/xml/dblp.dtd",
    }
    CACHE_DIR_NAME = "cache"

    def __init__(self) -> None:
        self.__logger = logging.getLogger("[DataFetcher]")

    def fetch(self) -> None:
        try:
            self.__do_net_fetch(self.FILES)
            self.__do_unzip(list(self.FILES.keys())[0])
        except Exception as e:
            self.__logger.error(f'Fetch task failed with "{e}"')

    def __do_net_fetch(self, url_file_map: dict[str, str]) -> None:
        self.__logger.info(f"Try to download all files: {list(url_file_map.keys())}")

        for filename, url in url_file_map.items():
            full_filename = os.path.join(self.CACHE_DIR_NAME, filename)
            if not os.path.exists(full_filename):
                self.__logger.info(f"Fetching: {full_filename}, {url}")

                with urllib.request.urlopen(url=url, timeout=90.0) as response:
                    os.makedirs(self.CACHE_DIR_NAME, 0o755, True)
                    with open(full_filename, "wb+") as file:
                        file.write(response.read())

    def __do_unzip(self, zip_filename: str) -> None:
        final_filename, ext = os.path.splitext(zip_filename)
        if ext not in [".gz", ".tgz"]:
            raise RuntimeError(f"Compression format: {ext} is not supported")

        if not os.path.exists(os.path.join(self.CACHE_DIR_NAME, final_filename)):
            self.__logger.info("Unzipping files")

            with gzip.open(os.path.join(self.CACHE_DIR_NAME, zip_filename)) as source:
                with open(
                    os.path.join(self.CACHE_DIR_NAME, final_filename), "wb"
                ) as dest:
                    dest.write(source.read())
