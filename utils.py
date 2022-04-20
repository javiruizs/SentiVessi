"""Module for generic utility functions."""
import datetime as dt
import os
import os.path

from shapely import wkt
from shapely.geos import WKTReadingError


def generate_polygon_str(*coor):
    """Generates a WKT polygon string.

    :param coor: (long, lat) tuples, assuming last one is not first one again. This is done internally.
    :return: str
    """

    coor = list(coor)
    coor.append(coor[0])

    plg = "POLYGON(("
    for i, c in enumerate(coor):
        plg += " ".join(c)
        if i != len(coor) - 1:
            plg += ","

    plg += "))"

    return plg


def generate_output_string(input_path, out_dir: str = "", prefix: str = "", suffix=""):
    """Generates output string mimicking SNAP's.

    :param input_path:
    :param out_dir:
    :param prefix:
    :param suffix:
    :return:
    """

    orig_dir, name = os.path.split(input_path)
    name, _ = os.path.splitext(name)

    if prefix:
        name = f"{prefix}_{name}"

    if suffix:
        name = f"{name}_{suffix}"

    return os.path.join(out_dir if out_dir else orig_dir, name)


def extract_name_info(prod_name: str):
    """Extracts product information from its name.
    Pattern based on https://sentinels.copernicus.eu/web/sentinel/user-guides/sentinel-1-sar/naming-conventions#:~:text=The%20top%2Dlevel%20Sentinel%2D1,separated%20by%20an%20underscore%20(_).&text=The%20Mission%20Identifier%20(MMM)%20denotes,for%20the%20SENTINEL%2D1B%20instrument.

    :param prod_name: Product name.
    :return: Dict with the information
    """
    import re

    pattern = "^(?P<prefix>\w+)?(?P<sat>S1A|S1B)_(?P<beam>S[1-6]|IW|EW|WV)_(?P<prod>GRD|SLC|OCN)(?P<res>F|H|M)_" \
              "(?P<proc_lvl>1|2)(?P<proc_c>S|A)(?P<pol>SH|SV|DH|DV)_(?P<start>\d{8}T\d{6})_(?P<stop>\d{8}T\d{6})_" \
              "(?P<abs_orb>\d{6})_(?P<take_id>[0-9A-F]{6})_(?P<prod_id>[0-9A-F]{4})(?P<suffix>\w+)?$"

    name = os.path.splitext(os.path.basename(prod_name))[0]

    result = re.match(pattern, name.upper())  # Compile the pattern
    return result.groupdict()


def formatted_ts(fmt="%Y-%m-%dT%H-%M-%S"):
    """
    Generates a timestamp with the fiven format.
    :param fmt: str, optional. Timestamp format to use. Defaults to "%Y-%m-%dT%H-%M-%S".
    :return: str. A formatted timestamp.
    """
    now = dt.datetime.now()
    return now.strftime(fmt)


def gen_cmp_path(name_a, name_b):
    """
    Generates a comparison name between two products.
    :param name_a: str. Product A.
    :param name_b: str. Product B.
    :return: str. Resulting name.
    """
    name_a = os.path.splitext(os.path.split(name_a)[1])[0]
    name_b = os.path.splitext(os.path.split(name_b)[1])[0]

    a_info = extract_name_info(name_a)
    b_info = extract_name_info(name_b)

    return f"{a_info['sat']}_{a_info['start']}vs{b_info['sat']}_{b_info['start']}"


def test_wkt(aoi: str):
    """
    Tests a WKT string.
    :param aoi: str. The WKT string.
    :return: bool. True if correct, false if not.
    """
    try:
        aoi = wkt.loads(aoi)
    except WKTReadingError:
        return None
    else:
        return aoi
