"""Module for downloading, querying and filtering products."""
import configparser
import configparser as cfgp
import copy
import json
import os.path
import re
from xml.dom import minidom

import pandas as pd
import sentinelsat
import shapely.wkt
from pandas import DataFrame
from geopandas import GeoDataFrame
from sentinelsat import SentinelAPI

import utils

pd.options.mode.chained_assignment = None


class Downloader(SentinelAPI):
    """Downloader, filterer and queryer for Sentinel products."""

    def query(self, aoi=None, start="", end="", platformname="Sentinel-1", producttype="GRD",
              relative_orbit: int = None, area_relation="Intersects", **kwargs):
        """
        Reimplemented query function where many default parameters have been set. Returns products ordered in ascending
        beginposition.
        :param aoi: str. AoI WKT string.
        :param start: str. Start date in format: YYYYMMDD
        :param end: str. End date in format: YYYYMMDD
        :param platformname: str. Sentinel mission. Defaults to Sentinel-1.
        :param producttype: str. Product type. Defaults to GRD.
        :param relative_orbit: int. Relative orbit number.
        :param area_relation: str. Determins how products are retrieved. Possible values are: Intersects, Contains and IsWhithin.
        :param kwargs: Other keyword args accepted by the Open Access Hub.
        :return: dict with following structure: { uuid: product_values, ... }
        """

        if relative_orbit:
            return super().query(aoi, (start, end), order_by="+beginposition", area_relation=area_relation,
                                 relativeorbitnumber=relative_orbit, platformname=platformname, producttype=producttype,
                                 **kwargs)
        else:
            return super().query(aoi, (start, end), order_by="+beginposition", area_relation=area_relation,
                                 platformname=platformname, producttype=producttype, **kwargs)

    def filter_by_aoi_pct(self, res: dict, aoi: str, aoi_pct: int = 0, same_datatake: bool = True):
        """
        Filtering the returned results by the aoi coverage pct.
        :param res: Results dict.
        :param aoi: AoI WKT string.
        :param aoi_pct: Percent of AoI coverage
        :param same_datatake: If set to True, aoi_pct will take into account the other products of the same datatake.
        :return: Filtered dict.
        """

        results = copy.deepcopy(res)  # Copy so that source is not modified

        # Filter by aoi_pcnt
        aoi = shapely.wkt.loads(aoi)  # Converts the WKT string
        missiondatatakes = {}  # Dictionary where the aoi coverages per mission datatake are stored.
        uuids = []  # List of uuids in iorder

        # Iterate over the {uuid: properties}
        for uuid, properties in results.items():
            properties["satellite"] = properties["identifier"][:3]  # Extract the satellite who took the product
            footprint = shapely.wkt.loads(properties["footprint"])  # Compile the footprint into WKT
            properties["geometry"] = footprint  # Add it to the properties

            # Remove info that is not needed
            del properties["footprint"]
            del properties["gmlfootprint"]


            # Calculate the aoi coverage pct as an int
            properties["aoicoverage"] = int(round(footprint.intersection(aoi).area / aoi.area * 100, 0))

            # Check the access status
            properties["access"] = "online" if self.is_online(uuid) else "offline"

            if same_datatake:  # If same datatake should be taken into account
                try:  # Add the uuids
                    missiondatatakes[properties["missiondatatakeid"]]["uuids"].append(uuid)
                    missiondatatakes[properties["missiondatatakeid"]]["pcts"].append(properties["aoicoverage"])
                except KeyError:
                    missiondatatakes[properties["missiondatatakeid"]] = {"uuids": [uuid],
                                                                         "pcts": [properties["aoicoverage"]]}

            else:  # If individual count
                if properties["aoicoverage"] >= aoi_pct:
                    uuids.append(uuid)

        for uuid, properties in missiondatatakes.items():  # If not same_datatake, this dict will be empty
            if sum(properties["pcts"]) >= aoi_pct:
                uuids += properties["uuids"]

        # Convert filtered results to dataframe manually
        if len(uuids) > 0:
            df = self.to_dataframe({k: results[k] for k in uuids})  # First to DataFrame
            gdf = GeoDataFrame(df, crs="EPSG:4326", geometry="geometry")  # Convert to geodataframe
        else:
            gdf = GeoDataFrame(crs=crs, geometry=[])

        return gdf

    @classmethod
    def from_file(cls, config_file: str):
        """
        Creates a Downloader from a .ini file.
        :param config_file: Path to the .ini file.
        :return: A instantiated Downloader
        """

        parser = cfgp.ConfigParser()
        if not parser.read(config_file):
            raise ValueError(f"File '{config_file}' does not exist.")

        username = parser.get("DEFAULT", "username")
        passwd = parser.get("DEFAULT", "passwd")
        try:
            url = parser.get("DEFAULT", "url")
        except configparser.NoOptionError:
            return cls(username, passwd)
        else:
            return cls(username, passwd, url)

    def check_creds(self):
        """
        Checks whether credentials and URL are valid.
        :return: bool. True if success, False if error.
        """
        try:
            # Since sentinelsat 1.0.0, empty queries will raise ValueError exception.
            # That's why a small query needs to be generated.
            self.query(None, "20200301", "20200301")
        except (sentinelsat.UnauthorizedError, AttributeError):
            return False
        else:
            return True

    def download_from_meta4(self, file_path: str, out_dir: str = ".", quicklooks: bool = False):
        """
        Downloads products from meta4 file, which is generated when cart in Open Access Hub is downloaded.
        :param file_path: str. Path to the meta4 file.
        :param out_dir: str. Ouptut directory where files will be downloaded. Defaults to current directory.
        :param quicklooks: bool. Enables the download of quicklooks. Defaults to False.
        :return: The information dict of all downloaded products.
        """

        uuids = {uuid: {} for uuid in Downloader.uuids_from_meta4(file_path)}  # Gather all uuids in the accepted format

        if quicklooks:
            self.download_all_quicklooks(uuids, out_dir)

        return self.download_all(uuids, directory_path=out_dir)

    def download_from_name_file(self, file_path: str, out_dir=".", quicklooks: bool = False):
        """
        Downloads products from a simple text file, which contains product identifiers, one by line.
        :param file_path: str. Path to the file.
        :param out_dir: str. Ouptut directory where files will be downloaded. Defaults to current directory.
        :param quicklooks: bool. Enables the download of quicklooks. Defaults to False.
        :return: The information dict of all downloaded products.
        """

        with open(file_path, "r") as f:
            names = [os.path.splitext(line.rstrip())[0] for line in f.readline()]  # Load lines from simple file

        uuids = {list(self.query(identifier=name).keys())[0] for name in names}  # Create uuid dict

        if quicklooks:
            self.download_all_quicklooks(uuids, out_dir)

        return self.download_all(uuids, out_dir)

    def download_from_csv(self, file_path: str, out_dir=".", quicklooks: bool = False):
        """
        Downloads products from a csv file, where the index labels are the products' UUIDs.
        :param file_path: str. Path to the file.
        :param out_dir: str. Ouptut directory where files will be downloaded. Defaults to current directory.
        :param quicklooks: bool. Enables the download of quicklooks. Defaults to False.
        :return: The information dict of all downloaded products.
        """

        df = pd.read_csv(file_path, sep=";", decimal=",", index_col=0)

        uuids = {i: {} for i in df.index}  # Create uuid dict

        if quicklooks:
            self.download_all_quicklooks(uuids, out_dir)

        return self.download_all(uuids, out_dir)

    def download_from_json(self, file_path: str, out_dir=".", quicklooks: bool = False):
        """
        Downloads products from a simple JSON file, where the resulting dict obtained from query is stored.
        :param file_path: str. Path to the file.
        :param out_dir: str. Ouptut directory where files will be downloaded. Defaults to current directory.
        :param quicklooks: bool. Enables the download of quicklooks. Defaults to False.
        :return: The information dict of all downloaded products.
        """
        with open(file_path) as f:
            res = json.load(f)

        if quicklooks:
            self.download_all_quicklooks(res, out_dir)

        return self.download_all(res, out_dir)

    @staticmethod
    def uuids_from_meta4(file_path: str):
        """
        Extracts the product UUIDs from the meta4 file.
        :param file_path: Path to the meta4 file.
        :return: A list of strings.
        """
        doc = minidom.parse(file_path)  # Reads file
        items = doc.getElementsByTagName("url")  # Gets tags with url
        urls = [item.firstChild.data for item in items]  # Gets urls from tag

        expr = r".*Products\('(?P<uuid>[\w\d-]+)'\).*"  # Regular expression to match uuid
        regex = re.compile(expr)  # Compiled regular expression

        uuids = [regex.search(url).group("uuid") for url in urls]  # Gather all uuids
        return uuids

    @staticmethod
    def to_dict(res: DataFrame, uuids_only: bool = False):
        """
        Converts a result DataFrame back to a dict.
        :param res: DataFrame containing the results.
        :param uuids_only: bool. When creating the dict, if set, the resulting dict will contain uuids with empty dicts.
        :return: A dict with the format { uuid: product_info }, or { uuid: {} }.
        """
        if not uuids_only:
            return res.to_dict(orient="index")
        else:
            return {k: None for k in res.index.values}

    def save_query(self, result: dict, out_fmt: str = "CSV", path=None):
        """
        Saves the query result to the specified format.
        :param result: dict. The results dict.
        :param out_fmt: str. The output format. Valid formats are: CSV, EXCEL and JSON.
        :param path: str. Output path whithout extension.
        :return: None.
        """

        if not isinstance(result, dict):
            raise ValueError("Passed query result is not a dict.")

        df = self.to_geodataframe(result)

        if not path:
            path = f"query_{utils.formatted_ts()}"

        if out_fmt == "CSV":
            df.to_csv(f"{path}.csv", sep=";", decimal=",", date_format="%Y/%m/%d %H:%M:%S")
        elif out_fmt == "JSON":
            with open(f"{path}.json", "w") as f:
                df.to_json(f, orient="index", date_format="%Y/%m/%d %H:%M:%S", indent=2)
        elif out_fmt == "EXCEL":
            df.to_excel(f"{path}.xlsx", sheet_name="Results")
        else:
            raise ValueError(f"Format '{out_fmt}' is not recognized.")
