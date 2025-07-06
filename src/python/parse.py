import time
import typing
import logging
import xml.sax
import xml.sax.handler


class DataParser:
    # Typedefs
    ## tuple<conference, year, title, authors, url>
    paper_t = tuple[str, int, str, list[str], str]
    ## invokable<paper_t> -> bool
    predict_t = typing.Callable[[paper_t], bool]

    class DBLP_XML_SAX_Handler(xml.sax.ContentHandler):
        def __init__(self, predict_callback) -> None:
            super().__init__()

            self.__predict = predict_callback

            self.__is_inproceedings = False
            self.__current_tag = ""

            self.__result: list[DataParser.paper_t] = []
            self.__init_paper_t()

        def __init_paper_t(self) -> None:
            # Elements in tuple: paper_t
            self.__paper_conference = ""
            self.__paper_year = 0
            self.__paper_title = ""
            self.__paper_author = []
            self.__paper_url = ""

        def startElement(self, name: str, attrs) -> None:
            self.__current_tag = name
            if not self.__is_inproceedings:
                self.__is_inproceedings = name == "inproceedings"

        def characters(self, content: str) -> None:
            if not self.__is_inproceedings:
                return

            match self.__current_tag:
                case "booktitle":
                    if con := content.strip("\n"):
                        self.__paper_conference = con
                case "year":
                    if year := content.strip("\n"):
                        self.__paper_year = int(year)
                case "title":
                    if title := content.strip("\n"):
                        self.__paper_title = title
                case "author":
                    if author := content.strip("\n"):
                        self.__paper_author.append(author)
                case "ee":
                    if url := content.strip("\n"):
                        self.__paper_url = url
                case _:
                    pass

        def endElement(self, name: str) -> None:
            if self.__is_inproceedings:
                self.__is_inproceedings = name != "inproceedings"
                if not self.__is_inproceedings:
                    res = (
                        self.__paper_conference,
                        self.__paper_year,
                        self.__paper_title,
                        self.__paper_author,
                        self.__paper_url,
                    )
                    if self.__predict is None or self.__predict(res):
                        self.__result.append(res)

                    self.__init_paper_t()

        def getResult(self):
            return self.__result

    def __init__(self, dblp_file_path: str) -> None:
        self.__dblp_file = dblp_file_path

        self.__logger = logging.getLogger("[DataParser]")

    def parse(self, filter: predict_t | None = None) -> list[paper_t]:
        self.__logger.info(f"Parsing start, DBLP file: {self.__dblp_file}")
        time_start = time.perf_counter_ns()

        paser = xml.sax.make_parser()
        paser.setFeature(xml.sax.handler.feature_namespaces, False)

        dblp_handler = DataParser.DBLP_XML_SAX_Handler(filter)
        paser.setContentHandler(dblp_handler)

        paser.parse(self.__dblp_file)
        result = dblp_handler.getResult()

        time_end = time.perf_counter_ns()
        self.__logger.info(
            f"Parsing complete, {len(result)} entries total with {(time_end-time_start)/(10**9)} seconds"
        )

        return result
