import numpy
import logging
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures


class DataPredictor:
    # Typedefs
    ## map<conference, map<year, count>>
    paper_statistic_t = dict[str, dict[int, int]]
    ## map<conference, count>
    predict_result_t = dict[str, int]

    def __init__(self, data: paper_statistic_t) -> None:
        self.__data = data

        self.__logger = logging.getLogger("[DataPredictor]")

    def result(self) -> predict_result_t:
        self.__logger.info("Training start, using polynomial")

        ret: DataPredictor.predict_result_t = {}

        for con in self.__data.keys():
            model = make_pipeline(PolynomialFeatures(2), LinearRegression()).fit(
                numpy.reshape(list(self.__data[con].keys()), (-1, 1)),
                list(self.__data[con].values()),
            )

            last_year = max(self.__data[con].keys())
            future = model.predict([[last_year + 1]])
            ret[con] = int(future[0])

        self.__logger.info("Prediction complete")

        return ret
