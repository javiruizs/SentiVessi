"""Module dedicated for scheduled and prolongued observation scenarios."""
import configparser as cfgp

from model import Downloader, ChangeDetector, VesselDetector


class Scheduler:
    """A scheduler class to automatize the download of new available products and the vessel detection procedure,
    as well as the change detection.
    """

    def __init__(self):
        self.downloader: Downloader = None
        self.change_detector: ChangeDetector = None
        self.vessel_detector: VesselDetector = None
        self.dl_dir = "."
        self.dled_prods = []
        self.start = ""
        self.counter = 0

    @classmethod
    def from_cfg_file(cls, file_path: str):
        """
        Initiates a scheduler from a ini file.
        :param file_path: str. Path to the file.
        :return: Configured scheduler.
        """
        parser = cfgp.ConfigParser(interpolation=cfgp.ExtendedInterpolation)
        parser.read(file_path)

        scheduler = cls()

        return scheduler
