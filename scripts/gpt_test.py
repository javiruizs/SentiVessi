import datetime
import os
import subprocess as sp

import pandas as pd


def main():
    subset = "POLYGON((-6.061999797821045 35.62300109863281, -5.184999942779541 35.62300109863281," \
             "-5.184999942779541 36.29800033569336, -6.061999797821045 36.29800033569336, " \
             "-6.061999797821045 35.62300109863281, -6.061999797821045 35.62300109863281))"
    shp_detec = "Subset_{basename}_Orb_Cal_LSMask_THR_SHP_TC.dim"
    rgb_prep = "Subset_{basename}_Orb_Cal_Spk_TC.dim"

    cd_graph = "/home/fjrs/GitHub/codigo_tfg/scripts/change_preprocessing.xml"
    vd_graph = "/home/fjrs/GitHub/codigo_tfg/scripts/ship_detection.xml"

    srcs_dir = "/home/fjrs/Escritorio/DEMO/raw"
    gpt_out = "/home/fjrs/Escritorio/DEMO/GPT"
    gpf_out = "/home/fjrs/Escritorio/DEMO/GPF"

    command = 'gpt-esa "{cmd}" -Psource="{src}" -Psubset="{subset}" -Ptarget="{tgt}"'

    src_paths = []
    out_gpt_ship = []
    out_gpt_rgb = []
    for f in os.listdir(srcs_dir):
        full_path = os.path.join(srcs_dir, f)
        if os.path.isfile(full_path):
            src_paths.append(full_path)
            basename = os.path.splitext(f)[0]
            out_gpt_rgb.append(os.path.join(gpt_out, rgb_prep.format(basename=basename)))
            out_gpt_ship.append(os.path.join(gpt_out, shp_detec.format(basename=basename)))

    times = {f: [] for f in src_paths}

    print("RGB GPT...")
    for i, o in zip(src_paths, out_gpt_rgb):
        start = datetime.datetime.now()
        try:
            cmd = rf'{command.format(cmd=cd_graph, src=i, subset=subset, tgt=o)}'
            res = sp.run(cmd, stdout=sp.PIPE, stderr=sp.STDOUT, shell=True)
            res.check_returncode()
        except sp.CalledProcessError:
            print(res.stdout.decode())
            exit(1)
        end = datetime.datetime.now()
        times[i].append(end - start)

    print("VD GPT...")
    for i, o in zip(src_paths, out_gpt_ship):
        start = datetime.datetime.now()
        try:
            cmd = rf'{command.format(cmd=vd_graph, src=i, subset=subset, tgt=o)}'
            res = sp.run(cmd, stdout=sp.PIPE, stderr=sp.STDOUT, shell=True)
            res.check_returncode()
        except sp.CalledProcessError:
            print(res.stdout.decode())
            exit(1)
        end = datetime.datetime.now()
        times[i].append(end - start)

    import model.preprocessing.operators as op
    from model import ChangeDetector, VesselDetector
    op.VERBOSE = False

    print("RGB GPF...")
    for i in src_paths:
        start = datetime.datetime.now()
        ChangeDetector.preprocess(i, subset, gpf_out)
        end = datetime.datetime.now()
        times[i].append(end - start)

    print("VD GPF...")
    for i in src_paths:
        start = datetime.datetime.now()
        VesselDetector.sea_object_detection_chain(i, subset=subset, out_dir=gpf_out)
        end = datetime.datetime.now()
        times[i].append(end - start)

    df = pd.DataFrame.from_dict(times, orient="index", columns=["RGB GPT", "VD GPT", "RGB GPF", "VD GPF"])
    df.to_csv("GPT_vs_GPF.csv", sep=";", decimal=",")
    print(df)


if __name__ == '__main__':
    main()
