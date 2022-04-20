import copy
from datetime import datetime

import geopandas as gpd
import pandas as pd
import shapely.wkt
from sentinelsat import SentinelAPI


def filter_json(aoi, res, api, minaoi=80, json_path="../gibstrait_april2020_full.json"):
    missiondatatakes = {}
    for k, v in res.items():
        footprint = shapely.wkt.loads(v["footprint"])
        del v["footprint"]
        del v["gmlfootprint"]
        v["geometry"] = footprint
        v["sat"] = v["identifier"][:3]
        v["aoicoverage"] = round(footprint.intersection(aoi).area / aoi.area * 100, 0)
        v["access"] = "online" if api.is_online(k) else "offline"
        if v["missiondatatakeid"] in missiondatatakes:
            missiondatatakes[v["missiondatatakeid"]]["uuids"].append(k)
            missiondatatakes[v["missiondatatakeid"]]["pcts"].append(v["aoicoverage"])
        else:
            missiondatatakes[v["missiondatatakeid"]] = {"uuids": [k], "pcts": [v["aoicoverage"]]}

    uuids = []
    for k, v in missiondatatakes.items():
        if sum(v["pcts"]) >= minaoi:
            uuids += v["uuids"]

    return gpd.GeoDataFrame(pd.DataFrame.from_dict({k: res[k] for k in uuids}, orient="index"), geometry="geometry",
                            crs="EPSG:4326")


def filter_dataframe(aoi, res, api, minaoi=80, json_path="../gibstrait_april2020_full.json"):
    df = api.to_dataframe(res)

    # geometry = gpd.GeoSeries.from_wkt(df["footprint"])
    # aoicoverage = [round(shape.intersection(aoi).area / aoi.area * 100, 0) for shape in geometry]
    # access = ["online" if api.is_online(i) else "offline" for i in df.index.tolist()]
    # sats = [i[:3] for i in df["identifier"]]

    geometry = []
    aoicoverage = []
    access = []
    sats = []

    for row in df.itertuples():
        shape = shapely.wkt.loads(row.footprint)
        geometry.append(shape)
        aoicoverage.append(round(shape.intersection(aoi).area / aoi.area * 100, 0))
        access.append("online" if api.is_online(row.Index) else "offline")
        sats.append(row.identifier[:3])

    df["aoicoverage"] = aoicoverage
    df["access"] = access
    df["sat"] = sats

    df.drop(["footprint", "gmlfootprint"], axis=1, inplace=True)
    df = gpd.GeoDataFrame(df, crs="EPSG:4326", geometry=geometry)

    missiondtids_df = df[["missiondatatakeid", "aoicoverage"]].groupby(["missiondatatakeid"])
    missiondtids_df = missiondtids_df.filter(lambda x: x["aoicoverage"].sum() >= minaoi)

    final_df = df.loc[df.index.intersection(missiondtids_df.index)]

    return final_df


def main():
    aoi = "POLYGON((-6.0333718879122396 36.19765422366146, -5.8685769660372396 36.19100459398794, -5.7751931769747396 36.09563120236264, -5.6296243293184896 36.071214738040524, -5.5994119269747396 36.02680174350429, -5.4620828254122396 36.07565465918803, -5.4675759894747396 36.19765422366146, -5.3137673957247396 36.18657119381867, -5.2533425910372396 35.886737128238366, -5.3989114386934896 35.90008731402379, -5.5609597785372396 35.82217950335687, -5.7202615363497396 35.797678380278356, -5.7669534308809896 35.74419515250926, -5.9537210090059896 35.77094126240784, -6.0333718879122396 36.19765422366146))"
    aoi = shapely.wkt.loads(aoi)

    api = SentinelAPI("fjavier.ruizs", "Pj9a2f2@v^mZ")

    src = api.query(area=aoi, date=("20200301", "20200430"), order_by="+beginposition", platformname="Sentinel-1",
                    producttype="GRD")

    srccpy = copy.deepcopy(src)
    start = datetime.now()
    res = filter_json(aoi, srccpy, api)
    end = datetime.now()
    print(f"Filter by JSON ({len(src)} -> {len(res)}): {end - start}")

    start = datetime.now()
    res = filter_dataframe(aoi, src, api)
    end = datetime.now()
    print(f"Filter by DataFrame ({len(src)} -> {len(res)}): {end - start}")


if __name__ == '__main__':
    main()
