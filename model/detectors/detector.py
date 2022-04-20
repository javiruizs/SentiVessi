"""Module for the definition of a Detector."""
import os
from abc import ABC, abstractmethod

import pandas as pd

import utils


class Detector(ABC):
    """Detector class. Defines common attributes for each independent detector."""

    def __init__(self,
                 subset: str,
                 src_bands: str = "",
                 out_dir: str = "",
                 detec_dir: str = "",
                 proc_dir: str = "",
                 steps: bool = False,
                 verbose: bool = True):

        self.subset = subset
        self.src_bands = src_bands
        self.out_dir = out_dir
        self.detect_dir = os.path.join(out_dir, detec_dir)
        self.proc_dir = os.path.join(out_dir, proc_dir)
        self.steps = steps
        self.verbose = verbose

        # Create folder structure
        if not os.path.isdir(out_dir):
            os.mkdir(out_dir)

        if not os.path.isdir(self.proc_dir):
            os.mkdir(self.proc_dir)

        if not os.path.isdir(self.detect_dir):
            os.mkdir(self.detect_dir)

    @abstractmethod
    def detect(self):
        """
        Launches main functionality.
        :return: None.
        """
        pass

    @staticmethod
    def order_by_name(*products) -> pd.DataFrame:
        """
        Creates a DataFrame from the given product names and orders them by sensing date, ascendingly.
        :param products: str. Series of products.
        :return: DataFrame.
        """
        data = {}
        for prod in set(products):
            basename = os.path.splitext(os.path.basename(prod))[0]
            info = utils.extract_name_info(basename)
            info["abspath"] = prod
            data[basename] = info

        df = pd.DataFrame.from_dict(data, orient="index")
        df["start"] = pd.to_datetime(df["start"])
        df["stop"] = pd.to_datetime(df["stop"])

        return df.sort_values(by="start")
