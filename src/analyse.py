import os
import pickle
import time
import parse
import logging
from matplotlib import pyplot
from wordcloud import WordCloud

import freq
from predict import DataPredictor  # type: ignore


class DataAnalyser:
    # Typedefs
    ## tuple<[start_year, end_year), list<conference>>
    config_t = tuple[int, int, list[str]]

    def __init__(self, dblp_path: str, out_dir: str, config: config_t) -> None:
        self.__out_dir = out_dir
        self.__config = config

        # map<conference, map<year, count>>
        self.__conference_count = {
            conferences: {year: 0 for year in range(config[0], config[1])}
            for conferences in config[2]
        }
        self.__logger = logging.getLogger("[Analyser]")

        self.__logger.info("Analysis start")
        if not os.path.exists("cache/dblp.pkl"):
            self.__data = parse.DataParser(dblp_path).parse(self.__dblp_filter)
            with open("cache/dblp.pkl", "wb") as out:
                pickle.dump(self.__data, out)
        else:
            with open("cache/dblp.pkl", "rb") as data:
                self.__data = pickle.loads(data.read())
            for paper in self.__data:
                self.__dblp_filter(paper)
        self.__conference_count = {
            conferences: {
                year: count
                for year, count in self.__conference_count[conferences].items()
                if count
            }
            for conferences in config[2]
        }

        self.__do_visualization()

        #self.__make_wordcloud()

        DataPredictor(self.__conference_count).result()
        self.__logger.info("Analysis complete")

    def __dblp_filter(self, paper: parse.DataParser.paper_t) -> bool:
        if paper[1] not in range(self.__config[0], self.__config[1]):
            return False

        if paper[0] in self.__config[2]:
            self.__conference_count[paper[0]][paper[1]] += 1

        return True

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

        start = time.perf_counter_ns()
        result = freq.compute_word_freq(
            self.__data, list(range(self.__config[0], self.__config[1])), os.cpu_count()
        )
        end = time.perf_counter_ns()
        self.__logger.info(f"Parsing done, {end - start}ns passed")

        for year, data in result.items():
            wc = WordCloud(width=1920, height=1080).generate_from_frequencies(data)

            WC_FILE = os.path.join(self.__out_dir, f"wordcloud-{year}.png")
            os.makedirs(self.__out_dir, 0o755, True)
            wc.to_file(WC_FILE)
            self.__logger.info(f"World cloud saved as {WC_FILE}")
