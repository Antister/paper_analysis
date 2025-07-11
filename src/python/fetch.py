import os
import gzip
import logging
import hashlib
import urllib.request


class XMLFetcher:
    FILES = {
        "dblp.xml.gz": "https://dblp.org/xml/dblp.xml.gz",
        "dblp.xml.gz.md5": "https://dblp.org/xml/dblp.xml.gz.md5",
        "dblp.dtd": "https://dblp.org/xml/dblp.dtd",
    }

    def __init__(self, cache_dir: str) -> None:
        self.__cache_dir = cache_dir

        self.__logger = logging.getLogger("[XMLFetcher]")

    def fetch(self) -> list[str]:
        files = list(self.FILES.keys())

        try:
            self.__do_net_fetch(self.FILES)

            if not self.__do_integrity_check(files[0], files[1]):
                self.__logger.error(
                    f'MD5 checksum mismatch between "{files[0]}" and "{files[1]}"'
                )
                raise RuntimeError(f"Corrupted file: {files[0]}")

            self.__do_unzip(files[0])
        except Exception as e:
            err = f'Fetch task failed with "{e}"'
            self.__logger.error(err)
            raise RuntimeError(err)

        return [os.path.join(self.__cache_dir, os.path.splitext(files[0])[0])]

    def __do_net_fetch(self, url_file_map: dict[str, str]) -> None:
        self.__logger.info(f"Try to download all files: {list(url_file_map.keys())}")

        for filename, url in url_file_map.items():
            full_filename = os.path.join(self.__cache_dir, filename)
            if not os.path.exists(full_filename):
                self.__logger.info(f"Fetching: {full_filename}, {url}")

                with urllib.request.urlopen(url=url, timeout=90.0) as response:
                    os.makedirs(self.__cache_dir, 0o755, True)
                    with open(full_filename, "wb") as file:
                        file.write(response.read())

    def __do_integrity_check(self, filename: str, md5_filename: str) -> bool:
        self.__logger.info(f"Validating download file: {filename}")

        hasher = hashlib.md5()
        with open(os.path.join(self.__cache_dir, filename), "rb") as file:
            while data := file.read(2**20):
                hasher.update(data)

        with open(os.path.join(self.__cache_dir, md5_filename), "r") as file:
            checksum = file.read()
            checksum = checksum.split()[0]
            return checksum == hasher.hexdigest()

    def __do_unzip(self, zip_filename: str) -> None:
        final_filename, ext = os.path.splitext(zip_filename)
        if ext not in [".gz", ".tgz"]:
            raise RuntimeError(f"Compression format: {ext} is not supported")

        if not os.path.exists(os.path.join(self.__cache_dir, final_filename)):
            self.__logger.info(f"Unzipping file: {zip_filename}")

            with gzip.open(os.path.join(self.__cache_dir, zip_filename)) as source:
                with open(os.path.join(self.__cache_dir, final_filename), "wb") as dest:
                    dest.write(source.read())


class HTMLFetcher:
    def __init__(self, cache_dir: str) -> None:
        self.__cache_dir = cache_dir

        self.__logger = logging.getLogger("[HTMLFetcher]")

    def fetch(self, start: int, end: int, conferences: list[str]) -> list[str]:
        self.__logger.info(f"Try to fetch pages from dblp.org for {conferences}")

        ret = []

        for con in [i.lower() for i in conferences]:
            for year in range(start, end + 1):
                req_url = f"https://dblp.org/db/conf/{con}/{con}{year}.html"

                # Construct filename for parse: {conference}-{year}
                file_path = os.path.join(self.__cache_dir, f"{con}-{year}")
                if not os.path.exists(file_path):
                    self.__logger.info(f"Downloading page of {con.upper()}-{year}")

                    with urllib.request.urlopen(url=req_url, timeout=90.0) as response:
                        os.makedirs(self.__cache_dir, 0o755, True)
                        with open(file_path, "wb") as cache_file:
                            cache_file.write(response.read())

                ret.append(file_path)

        return ret
