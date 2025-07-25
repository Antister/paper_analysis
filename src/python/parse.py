import os
import bs4
import time
import ctypes
import typing
import logging
import lxml.etree
import multiprocessing.pool

# tuple<conference, year, title, authors, url>
paper_t = tuple[str, int, str, list[str], str]


class XMLParser:
    # Typedefs
    ## invokable<paper_t> -> bool
    predict_t = typing.Callable[[paper_t], bool]

    def __init__(self, dblp_file_path: str) -> None:
        self.__dblp_file = dblp_file_path

        self.__logger = logging.getLogger("[XMLParser]")

    # lxml sucks, more memory, less speed
    class parser_impl:
        def __init__(self, dblp_file: str, predict_callback) -> None:
            self.__dblp_file = dblp_file
            self.__predict = predict_callback

            self.__result = []
            self.__init_paper_tuple()

            self.__is_in_title = False

        def __init_paper_tuple(self) -> None:
            # Elements in tuple: paper_t
            self.__paper_conference = ""
            self.__paper_year = 0
            self.__paper_title = ""
            self.__paper_author = []
            self.__paper_url = ""

        def __run(self) -> None:
            ctx = lxml.etree.iterparse(
                self.__dblp_file,
                events=("start", "end"),
                dtd_validation=False,
                load_dtd=True,
                no_network=True,
            )

            _, root = next(ctx)

            is_inproceedings = False
            for event, element in ctx:
                if event == "start":
                    if not is_inproceedings:
                        is_inproceedings = element.tag == "inproceedings"

                    # lxml fails to handle mixing content here, handle it manually
                    if is_inproceedings and element.tag == "title":
                        self.__is_in_title = True

                elif event == "end":
                    if not is_inproceedings:
                        continue

                    # Handle the content of element when ending
                    # Acquire content at start event fails in some scenarios
                    self.__tag_handler(element)

                    if element.tag == "inproceedings":
                        res = (
                            self.__paper_conference,
                            self.__paper_year,
                            self.__paper_title,
                            self.__paper_author,
                            self.__paper_url,
                        )
                        if self.__predict is None or self.__predict(res):
                            self.__result.append(res)

                        is_inproceedings = False
                        self.__init_paper_tuple()

                    # Clear the memory
                    element.clear()
                    root.clear()

            # F*ck python's memory management
            try:
                libc = ctypes.CDLL("libc.so.6")
                libc.malloc_trim(0)
            except:
                logger = logging.getLogger("[ParserWorker]")
                logger.warning("Failed to trim dynamic memory")
                logger.warning("Which may cause high memory consumption")
                logger.warning("It's safe to ignore the warning if don't use glibc")

        def __tag_handler(self, element) -> None:
            if not (element.tag and element.text):
                return

            if text := element.text.strip():
                match element.tag:
                    case "booktitle":
                        self.__paper_conference = text
                    case "year":
                        self.__paper_year = int(text)
                    case "title":
                        self.__is_in_title = False
                        self.__paper_title = (
                            # Handle mixing content, the text in inner label is processed before title
                            f"{text} {self.__paper_title.strip()}".strip()
                        )
                    case "author":
                        self.__paper_author.append(text)
                    case "ee":
                        self.__paper_url = text
                    case _:
                        pass

            if self.__is_in_title:  # Take everything in title label
                self.__paper_title += element.text + (
                    element.tail if element.tail else ""
                )

        def result(self) -> list[paper_t]:
            self.__run()
            return self.__result

    def parse(self, filter: predict_t | None = None) -> list[paper_t]:
        self.__logger.info(f"XML Parsing start, DBLP file: {self.__dblp_file}")
        time_start = time.perf_counter_ns()

        result = self.parser_impl(self.__dblp_file, filter).result()

        time_end = time.perf_counter_ns()
        self.__logger.info(
            f"XML Parsing complete, {len(result)} entries total with {(time_end-time_start)/(10**9)} seconds"
        )

        return result


# pyright: reportCallIssue=false
# pyright: reportIndexIssue=false
# pyright: reportArgumentType=false
# pyright: reportAttributeAccessIssue=false
# Dynamic-type language is a kind of sh*t


class HTMLParser:
    def __init__(self, html_list: list[str]) -> None:
        self.__files = html_list

        self.__logger = logging.getLogger("[HTMLParser]")

    def parse(self) -> list[paper_t]:
        self.__logger.info(f"HTML Parsing start, {len(self.__files)} files to parse")
        time_start = time.perf_counter_ns()

        ret = []
        with multiprocessing.pool.Pool(os.cpu_count()) as pool:
            for i in pool.map_async(self._parser_worker, self.__files).get():
                ret.extend(i)

        time_end = time.perf_counter_ns()
        self.__logger.info(
            f"HTML Parsing complete, {len(ret)} entries total with {(time_end-time_start)/(10**9)} seconds"
        )

        return ret

    @staticmethod
    def _parser_worker(html_file: str) -> list[paper_t]:
        ret = []

        try:
            with open(html_file, "r", encoding="utf-8") as file:
                doc = file.read()
            soup = bs4.BeautifulSoup(doc, "lxml")

            # Infer the conference and year from filename
            _, file_name = os.path.split(html_file)
            conference, year = file_name.split("-")
            conference = conference.upper()
            year = int(year)

            # Use lxml to process html, really slow
            # Skip the first entry since it's the header
            for entry in soup.find_all("cite", class_="data")[1:]:
                title = (
                    title_tag.get_text(strip=False)
                    if (title_tag := entry.find("span", class_="title"))
                    else "Unknown"
                ).strip()

                authors = [
                    author_tag.get_text(strip=True)
                    for author_tag in entry.find_all("span", itemprop="author")
                ]

                url = ee_tag["href"] if (ee_tag := entry.find("a", href=True)) else ""

                ret.append((conference, year, title, authors, url))

        except Exception as e:
            logging.getLogger("[HTMLParserWorker]").error(
                f"Failed to parse {html_file}: {e}"
            )

        finally:
            return ret
