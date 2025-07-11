import os
import time
import typing
import logging
import wordcloud
import multiprocessing.pool
from matplotlib import pyplot

from src.python import parse
from src.python import predict


class DataAnalyser:
    # Typedefs
    ## tuple<[start_year, end_year), list<conference>>
    config_t = tuple[int, int, list[str]]

    def __init__(
        self, out_dir: str, xml_data: list[parse.paper_t], config: config_t
    ) -> None:
        self.__out_dir = out_dir
        self.__data = xml_data
        self.__config = config

        self.__logger = logging.getLogger("[Analyser]")
        self.__conference_count: predict.DataPredictor.paper_statistic_t = {
            conferences: {year: 0 for year in range(config[0], config[1])}
            for conferences in config[2]
        }

    def analyse(self) -> typing.Self:
        self.__logger.info("Analysis start")
        self.__do_paper_count()
        self.__do_visualization()
        self.__make_wordcloud()
        self.__logger.info("Analysis complete")

        return self

    def result(self) -> predict.DataPredictor.paper_statistic_t:
        return self.__conference_count

    def __do_paper_count(self) -> None:
        self.__logger.info("Counting annual publishes of each conference")

        for paper in self.__data:
            if (
                paper[1] in range(self.__config[0], self.__config[1])
                and paper[0] in self.__config[2]
            ):
                self.__conference_count[paper[0]][paper[1]] += 1

        # Strip out the conference with 0 publishes
        self.__conference_count = {
            conferences: {
                year: count
                for year, count in self.__conference_count[conferences].items()
                if count
            }
            for conferences in self.__config[2]
        }

    def __do_visualization(self) -> None:
        self.__logger.info("Visualizing analyse result")

        for con in self.__conference_count.keys():
            pyplot.plot(
                list(self.__conference_count[con].keys()),
                list(self.__conference_count[con].values()),
                label=con,
                marker="o",
            )

        pyplot.title("Annual Publication Trends of Top Conferences")

        pyplot.grid(True)
        pyplot.xlabel("Year")
        pyplot.ylabel("Paper counts")

        pyplot.legend(title="Conference")

        PLOT_FILE = os.path.join(self.__out_dir, "paper_counts.svg")
        os.makedirs(self.__out_dir, 0o755, True)
        pyplot.savefig(PLOT_FILE)
        self.__logger.info(f"Plot saved as {PLOT_FILE}")

    def __make_wordcloud(self) -> None:
        self.__logger.info("Making word cloud")

        import freq  # type: ignore

        start = time.perf_counter_ns()
        result = freq.compute_word_freq(
            self.__data,
            list(range(self.__config[0], self.__config[1])),
            typing.cast(int, os.cpu_count()),
        )
        end = time.perf_counter_ns()
        self.__logger.info(f"Parsing done, {(end - start) / 10**9} seconds elapsed")

        with multiprocessing.pool.Pool(os.cpu_count()) as pool:
            pool.starmap(
                self._wordcloud_worker,
                [(self.__out_dir, year, data) for year, data in result.items()],
            )

    @staticmethod
    def _wordcloud_worker(out_dir: str, year: int, word_freq: dict[str, float]) -> None:
        WC_FILE = os.path.join(out_dir, f"wordcloud-{year}.png")
        os.makedirs(out_dir, 0o755, True)

        wordcloud.WordCloud(
            width=1920,
            height=1080,
            background_color="#1f1e33",
        ).generate_from_frequencies(word_freq).to_file(WC_FILE)

        logging.getLogger("[Analyser]").info(f"World cloud saved as {WC_FILE}")
