import logging

from numpy import reshape
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures


class DataPredictor:
    def __init__(self, data: dict[str, dict[int, int]]) -> None:
        self.__data = data

        self.__logger = logging.getLogger("[DataPredictor]")

    def result(self) -> None:  # dict[str, int]:
        for con in self.__data.keys():
            model = make_pipeline(PolynomialFeatures(2), LinearRegression()).fit(
                reshape(list(self.__data[con].keys()), (-1, 1)),
                list(self.__data[con].values()),
            )
            print(
                f"{con} will have {model.predict([[max(self.__data[con].keys())+1]])} submit next year"
            )
