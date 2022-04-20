import datetime
import os

from model.detectors.change_detector import ChangeDetector


def main():
    subset = "POLYGON((-6.10 35.618, -5.243 35.618, -5.243 36.289, -6.10 36.289 , -6.10 35.618))"
    subset_suez = "POLYGON((32.26576107780424 30.42075737430954,32.42780941764799 30.42786249819021,32.60633724967924 30.21923079475643,32.65852230827299 29.934018753678696,32.71620053092924 29.757729011895638,32.34266537467924 29.68378550925287,32.48274105827299 29.983990178907213,32.52943295280424 30.10286855306152,32.49372738639799 30.185998455255294,32.36463803092924 30.23109676788321,32.26850765983549 30.29277673863913,32.26576107780424 30.42075737430954))"
    path = r"B:\TFG FJRS\Productos\Gibraltar Strait Mar. 2019"
    products = [os.path.join(path, p) for p in os.listdir(path) if
                os.path.isfile(os.path.join(path, p)) and p.endswith(".zip")]

    cd = ChangeDetector(subset, products[0], out_dir=os.path.join(path, "change_detection"), sequential=True)

    cd.detect(*products[1:])


def performance():
    subset = "POLYGON((-6.061999797821045 35.62300109863281, -5.184999942779541 35.62300109863281," \
             "-5.184999942779541 36.29800033569336, -6.061999797821045 36.29800033569336, " \
             "-6.061999797821045 35.62300109863281, -6.061999797821045 35.62300109863281))"
    shp_detec = "Subset_{basename}_Orb_Cal_LSMask_THR_SHP.dim"
    rgb_prep = "Subset_{basename}_Orb_Cal_Spk_TC.dim"

    cd_graph = r"C:\Users\javie\Documents\GitHub\codigo_tfg\scripts\RGB Comparison Gibraltar Straight.xml"
    vd_graph = r"C:\Users\javie\Documents\GitHub\codigo_tfg\scripts\ShipDetectionGraph_tutorial.xml"

    prods_dir = r"C:\Users\javie\QSync Folders\TFG FJRS\Productos\DEMO\raw"

    full_paths = []
    for f in os.listdir(prods_dir):
        full_path = os.path.join(prods_dir, f)
        if os.path.isfile(full_path):
            full_paths.append(full_path)

    start = datetime.datetime.now()
    for f in full_paths:
        ChangeDetector.preprocess(f, subset, prods_dir)
    end = datetime.datetime.now()

    print(f"Full change detection preprocessing: {end - start}")


if __name__ == '__main__':
    performance()
