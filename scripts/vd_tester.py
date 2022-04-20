import os

from model.detectors.vessel_detector import VesselDetector


def main():
    subset = "POLYGON((-6.10 35.618, -5.243 35.618, -5.243 36.289, -6.10 36.289 , -6.10 35.618))"
    subset_suez = "POLYGON((32.26576107780424 30.42075737430954,32.42780941764799 30.42786249819021,32.60633724967924 30.21923079475643,32.65852230827299 29.934018753678696,32.71620053092924 29.757729011895638,32.34266537467924 29.68378550925287,32.48274105827299 29.983990178907213,32.52943295280424 30.10286855306152,32.49372738639799 30.185998455255294,32.36463803092924 30.23109676788321,32.26850765983549 30.29277673863913,32.26576107780424 30.42075737430954))"
    path = r"B:\TFG FJRS\Productos\Ever Given Mar. 21"
    products = [os.path.join(path, p) for p in os.listdir(path) if
                os.path.isfile(os.path.join(path, p)) and p.endswith(".zip")]

    vd = VesselDetector(subset_suez, out_dir=os.path.join(path, "vessel_detection"))

    result = vd.detect(*products)

    print(result["summary"])


if __name__ == '__main__':
    main()
