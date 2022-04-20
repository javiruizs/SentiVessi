"""
Module for detecting vessel.
"""
import datetime as dt
import os.path

import pandas as pd

import utils as u
from .detector import Detector


class VesselDetector(Detector):
    """
    Class that implements the vessel detector.
    """

    def __init__(self,
                 subset: str,
                 tgt_window: float = 30.0,
                 guard_wd_size: float = 500.0,
                 bg_wd_size: float = 800.0,
                 pfa: float = 12.5,
                 min_tgt: float = 30.0,
                 max_tgt: float = 50.0,
                 land_mask: str = "",
                 src_bands: str = "",
                 out_dir: str = "vessel_detections",
                 detect_dir: str = "detections",
                 proc_dir: str = "processed",
                 steps: bool = False,
                 verbose: bool = True):

        super(VesselDetector, self).__init__(
            subset=subset,
            src_bands=src_bands,
            out_dir=out_dir,
            detec_dir=detect_dir,
            proc_dir=proc_dir,
            steps=steps,
            verbose=verbose
        )

        # Params
        self.tgt_window = tgt_window
        self.guard_wd_size = guard_wd_size
        self.bg_wd_size = bg_wd_size
        self.pfa = pfa
        self.min_tgt = min_tgt
        self.max_tgt = max_tgt

        self.land_mask: str = land_mask  # Land mask file to import to the product if wanted

    def add_mask(self, *products, mask_path: str):
        """
        Adds vector mask to the given products.
        :param products: Opened products.
        :param mask_path: str. Path to the vector mask.
        :return:
        """
        # Todo
        pass

    @staticmethod
    def sea_object_detection_chain(prod_path: str, land_mask: str = "", subset: str = "", bands: str = "",
                                   tgt_window: int = 30, guard_wd_size: float = 500.0, bg_wd_size: float = 800.0,
                                   pfa: float = 12.5, min_tgt: float = 30.0, max_tgt: float = 600.0,
                                   out_dir: str = "", terrain_correction: bool = True, steps: bool = False):
        """
        Sea Object Detection processing chain implemented as if it is run from SNAP.
        :param prod_path: str. Path to the product.
        :param land_mask: str, optional. Name to the mask to use as a land mask. Defaults to "".
        :param subset: str, optional. Subset WKT string. Empty string means no subset. Defaults to "".
        :param bands: str, optional. Band names to use. Defaults to "".
        :param tgt_window: float, optional. Target window size. Defaults to 30.
        :param guard_wd_size: float, optional. Guard window size. Defaults to 500.
        :param bg_wd_size: float, optional. Background window size. Defaults to 800.
        :param pfa: float, optional. PFA. Defaults to 12.5.
        :param min_tgt: float, optional. Minimal target size. Defaults to 30.
        :param max_tgt: float, optional. Maximal target size. Defaults to 600.
        :param out_dir: str, optional. Output directory path. Defaults to "".
        :param terrain_correction: bool, optional. If set, applies terrain correction in the end so product is visible
            more user friendly when opened with SNAP. Defaults to True.
        :param steps: bool, optional. If set, all intermediary products are also stored. Defaults to False.
        :return: The processed product.
        """
        import model.preprocessing.operators as op

        # 0 Read
        prod = op.read_product(prod_path)

        # 1 Add mask_dile if specified
        if land_mask:
            pass  # TODO

        # 2 Orbit File
        prod = op.apply_orbit_file(prod)
        if steps:
            out_path = os.path.join(out_dir, prod.getName())
            prod = op.write_product(prod, out_path)

        # 3 Subset
        if subset:
            prod = op.create_subset(prod, subset)
            if steps:
                out_path = os.path.join(out_dir, prod.getName())
                prod = op.write_product(prod, out_path)

        # 4 Land-Sea-Mask
        prod = op.land_sea_mask(prod, bands)
        if steps:
            out_path = os.path.join(out_dir, prod.getName())
            prod = op.write_product(prod, out_path)

        # 5 Calibration
        prod = op.calibration(prod)
        if steps:
            out_path = os.path.join(out_dir, prod.getName())
            prod = op.write_product(prod, out_path)

        # 6 Adaptive Thresholding
        prod = op.adaptive_thresholding(prod, target_window=tgt_window, guard_window=guard_wd_size,
                                        bg_window=bg_wd_size, pfa=pfa)
        if steps:
            out_path = os.path.join(out_dir, prod.getName())
            prod = op.write_product(prod, out_path)

        # 7 Object Discrimination
        prod = op.object_discrimination(prod, min_tgt=min_tgt, max_tgt=max_tgt)

        # 8 Write
        # out_path = u.generate_output_string(prod_path, out_dir, "", suffix)
        out_path = os.path.join(out_dir, prod.getName())
        prod = op.write_product(prod, out_path)

        # 9 Terrain correction
        if terrain_correction:
            prod = op.terrain_correction(prod)
            out_path = os.path.join(out_dir, prod.getName())
            prod = op.write_product(prod, out_path)

        return prod, out_path

    def detect(self, *prods):
        """Detects vessels for the given inputs.

        :param prods: Paths to the input products.
        :return: Summary DataFrame, a list of detection DataFrames, a list of resulting products, and a list of resulting names
        """

        results = []
        result_names = []
        detections = []
        summary = []

        for i, p in enumerate(prods):  # For each input product
            # Execute the defined processing chain
            start_t = dt.datetime.now()
            prod, out_name = VesselDetector.sea_object_detection_chain(p, self.land_mask, self.subset, self.src_bands,
                                                                       out_dir=self.proc_dir, steps=self.steps,
                                                                       terrain_correction=False,
                                                                       tgt_window=self.tgt_window,
                                                                       guard_wd_size=self.guard_wd_size,
                                                                       bg_wd_size=self.bg_wd_size, pfa=self.pfa,
                                                                       min_tgt=self.min_tgt, max_tgt=self.max_tgt)
            end_t = dt.datetime.now()

            if self.verbose:
                print(f"Product {i + 1} of {len(prods)} took {end_t - start_t} to process.")

            results.append(prod)  # Attach the output paths to the list
            result_names.append(out_name)  # Attach the output path to the list

            # Calculate ShipDetections.csv path
            detect_file = os.path.join(f"{out_name}.data", "vector_data", "ShipDetections.csv")

            if os.path.isfile(detect_file):
                # Load it to a DataFrame
                detect_df = pd.read_csv(detect_file, skiprows=1, sep="\t", index_col=0, header=0,
                                        names=["targets", "x", "y", "lat", "lon", "width", "length"],
                                        usecols=[0, 2, 3, 4, 5, 6, 7])

                detections.append(detect_df)  # Append to list

                # Extract filename information
                product_info = u.extract_name_info(p)

                # Add info to summary dict
                summary.append(
                    {
                        "file": prod.getName(),
                        "datetime": dt.datetime.strptime(f"{product_info['start']}", "%Y%m%dT%H%M%S"),
                        "prod_id": product_info["prod_id"],
                        "datatake": product_info["take_id"],
                        "n_detects": len(detect_df)
                    }
                )

                # Save formatted detection dataframe to specified dir
                detect_file = os.path.join(self.detect_dir, f"{prod.getName()}.csv")
                detect_df.to_csv(detect_file)

        # Convert summary to dataframe
        summary_df = pd.DataFrame(summary)
        summary_df.set_index("file", inplace=True)

        # Save summary df to csv
        summary_file = os.path.join(self.out_dir, f"detections_{u.formatted_ts()}.csv")
        summary_df.to_csv(summary_file, sep=";", decimal=",")

        return {"summary": summary_df, "detections": detections, "results": results, "resultnames": result_names}
