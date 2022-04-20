"""Module where the ChangeDetector class is implemented."""
import enum
import os.path

import numpy as np
from PIL import Image

import utils as u
from model.detectors.detector import Detector


class RGBChannel(enum.Enum):
    """
    Enumerator for the available RGB channels that the detector will recognize.
    """
    RED = 1
    GREEN = 2
    BLUE = 3


class ChangeDetector(Detector):
    """
    Detector which will create the RGB PNGs from two source products.
    """

    def __init__(self,
                 subset: str,
                 ref_prod,
                 rgb_pol: str = "VH",
                 ref_chnl: RGBChannel = RGBChannel.RED,
                 sequential: bool = False,
                 src_bands: str = "",
                 out_dir: str = "change_detections",
                 detect_dir: str = "rgb",
                 proc_dir: str = "processed",
                 stack_dir: str = "stacks",
                 steps: bool = False,
                 verbose: bool = True):
        super(ChangeDetector, self).__init__(
            subset=subset,
            src_bands=src_bands,
            out_dir=out_dir,
            detec_dir=detect_dir,
            proc_dir=proc_dir,
            steps=steps,
            verbose=verbose
        )

        self.stack_dir = os.path.join(self.out_dir, stack_dir)

        self.ref_prod_path = ref_prod
        self.ref_prod = None

        self.ref_color = ref_chnl
        self.sequential: bool = sequential
        self.rgb_pol = rgb_pol

    @staticmethod
    def rgb_cmp(prod_a, prod_b, a_chnl, pol, cmp_path):
        """
        Creates the PNG RGB comparison given two preprocessed source products.
        :param prod_a: snappy.Product. Already opened primary product.
        :param prod_b: snappy.Product. Already opened second product.
        :param a_chnl: RGBChannel. Channel assigned to prod_a. The remaining unselected channels will be used for prod_b.
        :param pol: str. Polarization to use in the band selection. Either VV or VH.
        :param cmp_path: str. Path where the resulting PNG image will be saved to.
        :return: PIL.Image object.
        """
        import model.preprocessing.operators as op
        import model.preprocessing.formatting as fmt
        import model.preprocessing.utils as pu

        stack = op.create_stack(prod_a, prod_b)

        # Stack needs to be written and re-read first so bands are calculated and accesible
        prod = op.write_product(stack, out_path=cmp_path)
        stack = op.read_product(f"{cmp_path}.dim")

        stack_bands = list(stack.getBandNames())
        a_band = ""
        b_band = ""

        mst = f"Sigma0_{pol}_mst"
        slv = f"Sigma0_{pol}_slv"

        for band in stack_bands:
            if band.startswith(mst):
                a_band = band
            elif band.startswith(slv):
                b_band = band

        mst_band = pu.get_band_pixels(a_band, stack)
        slv_band = pu.get_band_pixels(b_band, stack)

        mst_img = Image.fromarray(mst_band)
        slv_img = Image.fromarray(slv_band)

        chnl_list = []

        if a_chnl == RGBChannel.RED:
            chnl_list.insert(0, mst_img)
            chnl_list.insert(1, slv_img)
            chnl_list.insert(2, slv_img)
        elif a_chnl == RGBChannel.GREEN:
            chnl_list.insert(1, mst_img)
            chnl_list.insert(0, slv_img)
            chnl_list.insert(2, slv_img)
        else:
            chnl_list.insert(2, mst_img)
            chnl_list.insert(0, slv_img)
            chnl_list.insert(1, slv_img)

        stack_img = np.dstack(chnl_list)

        clipped_stack = fmt.clip_scale_percent_pixels(stack_img)
        rgb = Image.fromarray(clipped_stack)

        return rgb

    def detect(self, *products) -> None:
        """
        Launches the detection process chain for the given product paths.
        :param products: str. Source product paths.
        :return: None.
        """
        import snappy

        # First check if there is a reference product generated, otherwise create it
        if not isinstance(self.ref_prod, snappy.Product):
            self.ref_prod = ChangeDetector.preprocess(self.ref_prod_path, self.subset, self.proc_dir)

        procs = []
        for p in products:
            proc = ChangeDetector.preprocess(p, self.subset, self.proc_dir)
            procs.append(proc)

            cmp_name = u.gen_cmp_path(self.ref_prod.getName(), proc.getName())
            cmp_path = os.path.join(self.stack_dir, cmp_name)

            rgb = ChangeDetector.rgb_cmp(self.ref_prod, proc, self.ref_color, self.rgb_pol, cmp_path)

            rgb.save(os.path.join(self.detect_dir, cmp_name + ".png"))

            if self.sequential and len(procs) > 1:
                cmp_name = u.gen_cmp_path(procs[-2].getName(), proc.getName())
                cmp_path = os.path.join(self.stack_dir, cmp_name)

                rgb = ChangeDetector.rgb_cmp(procs[-2], proc, self.ref_color, self.rgb_pol, cmp_path)

                rgb.save(os.path.join(self.detect_dir, cmp_name + ".png"))

    @staticmethod
    def preprocess(prod_path, subset: str = "", out_dir: str = "", out_name_fmt: str = "Subset_{}_Orb_Cal_Spk_TC",
                   steps: bool = False):
        """
        Preprocessing chain to apply to the source products prior to create the RGB PNG composition.
        :param prod_path: str. Path to the product.
        :param subset: str. Subset string in WKT format.
        :param out_dir: str. Output directory path.
        :param out_name_fmt: str. Unused. Output naming template to use when saving the resulting products. Since snappy
                is being used, the output name is automatically generated.
        :param steps: bool. If set, writes out the intermediary products after application of each operator.
        :return: snappy.Product: The preprocessed product.
        """

        import model.preprocessing.operators as op

        # 1. Read products
        prod = op.read_product(prod_path)

        # 2. Apply orbit file
        prod = op.apply_orbit_file(prod)
        if steps:
            out_path = os.path.join(out_dir, prod.getName())
            prod = op.write_product(prod, out_path)

        # 3. Calibration
        prod = op.calibration(prod)
        if steps:
            out_path = os.path.join(out_dir, prod.getName())
            prod = op.write_product(prod, out_path)

        # 4. Speckle filtering
        prod = op.speckle_filtering(prod)
        if steps:
            out_path = os.path.join(out_dir, prod.getName())
            prod = op.write_product(prod, out_path)

        # 5. Geocoding
        prod = op.terrain_correction(prod)
        if steps:
            out_path = os.path.join(out_dir, prod.getName())
            prod = op.write_product(prod, out_path)

        # 6 Create subset
        if subset:
            prod = op.create_subset(prod, subset)
            if steps:
                out_path = os.path.join(out_dir, prod.getName())
                prod = op.write_product(prod, out_path)

        # 7. Write
        out_path = os.path.join(out_dir, prod.getName())
        prod = op.write_product(prod, out_path)

        return prod
