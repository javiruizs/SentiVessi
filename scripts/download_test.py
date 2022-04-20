import pandas as pd

from model.downloader import Downloader


def offline_dl(dlr):
    df = pd.read_csv(r"B:\TFG FJRS\Productos\Gibraltar Strait Apr. 2019\gibstrait_Apr19_full.csv", index_col=0)
    df = df[df["covered_aoi"] < 0.8]

    uuids = Downloader.uuids_from_df(df)

    dlr.dl_quicklooks(uuids, r"B:\TFG FJRS\Productos\Gibraltar Strait Apr. 2019")
    dlr.download(df, dl_offl=True, out_dir=r"B:\TFG FJRS\Productos\Gibraltar Strait Apr. 2019")


def search(dlr, aoi):
    res = dlr.search(start="20190401", end="20190430", footprint=aoi,
                     res_path=r"B:\TFG FJRS\Productos\Gibraltar Strait Apr. 2019\gibstrait_Apr19_full.csv", intrs_pct=0,
                     write_result=True)

    dlr.download(res, dl_offl=True, out_dir=r"B:\TFG FJRS\Productos\Gibraltar Strait Apr. 2019")


def filter_test(dlr):
    df = pd.read_csv("B:\TFG FJRS\Productos\Gibraltar Strait Apr. 2020\GibStrait_Apr2020_full.csv", sep=";",
                     index_col=0, decimal=",")

    df.rename({"geometry": "footprint"}, axis=1, inplace=True)

    df["gmlfootprint"] = ""

    res = dlr.to_dict(df)

    filtered = dlr.filter(res, aoi_pcnt=0.8)
    pd.DataFrame.from_dict(filtered, orient="index").to_excel("filtered_test.xlsx")


if __name__ == '__main__':
    aoi = "POLYGON((-6.0333718879122396 36.19765422366146, -5.8685769660372396 36.19100459398794, " \
          "-5.7751931769747396 36.09563120236264, -5.6296243293184896 36.071214738040524, " \
          "-5.5994119269747396 36.02680174350429, -5.4620828254122396 36.07565465918803, " \
          "-5.4675759894747396 36.19765422366146, -5.3137673957247396 36.18657119381867, " \
          "-5.2533425910372396 35.886737128238366, -5.3989114386934896 35.90008731402379, " \
          "-5.5609597785372396 35.82217950335687, -5.7202615363497396 35.797678380278356, " \
          "-5.7669534308809896 35.74419515250926, -5.9537210090059896 35.77094126240784, " \
          "-6.0333718879122396 36.19765422366146))"
    dlr = Downloader.from_file("../login_cfg.ini")
    # search(dlr, aoi)
    filter_test(dlr)
