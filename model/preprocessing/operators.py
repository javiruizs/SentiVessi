"""
This module maps the used SNAP operators with Python functions.
"""
from typing import Collection

import snappy  # SNAP python interface

VERBOSE = False


def read_product(prod_path: str) -> snappy.Product:
    """Reads a product from a given path.

    :param prod_path: The path to the product.
    :return: The loaded product.
    """
    return snappy.ProductIO.readProduct(prod_path)


def apply_orbit_file(prod, orbit_type: str = "Sentinel Precise (Auto Download)", on_fail: bool = True,
                     poly_degree: int = 3):
    """
    Applies orbit file to product.
    :param prod: Opened product.
    :param orbit_type: str, optional. Way to obtain orbit file. Check SNAP manual for valid options.
    :param on_fail: bool, optional. If True, processing stops when failure occurs, otherwise, step is skipped.
    :param poly_degree: int, optional.
    :return: Modified product.
    """
    parameters = snappy.HashMap()

    parameters.put('orbitType', orbit_type)
    parameters.put('polyDegree', poly_degree)
    parameters.put('continueOnFail', on_fail)

    if VERBOSE:
        print("Applying orbit file...")
    return snappy.GPF.createProduct('Apply-Orbit-File', parameters, prod)


def calibration(prod):
    """
    Calibrates the passed product.
    :param prod: Opened product.
    :return: Modified product.
    """
    parameters = snappy.HashMap()

    # Leave commented so all source bands are used
    # parameters.put('sourceBands', 'Amplitude_VH,Amplitude_VV,Intensity_VH,Intensity_VV')

    parameters.put('auxFile', "Product Auxiliary File")
    parameters.put('outputImageInComplex', False)
    parameters.put('outputImageScaleInDb', False)
    parameters.put('createGammaBand', False)
    parameters.put('createBetaBand', False)
    parameters.put('createBetaBand', False)

    # Leave commented so all polarisations are used
    # parameters.put('selectedPolarisations', 'VH,VV')

    parameters.put('outputSigmaBand', True)
    parameters.put('outputGammaBand', False)
    parameters.put('outputBetaBand', False)

    if VERBOSE:
        print("Calibrating...")
    return snappy.GPF.createProduct("Calibration", parameters, prod)


def speckle_filtering(prod):
    """
    Applies speckle filtering on the passed product.
    :param prod: Opened product.
    :return: Modified product.
    """
    parameters = snappy.HashMap()
    # parameters.put('sourceBands', '')
    parameters.put('filter', 'Lee')
    parameters.put('filterSizeX', 3)
    parameters.put('filterSizeY', 3)
    parameters.put('dampingFactor', 2)
    parameters.put('estimateENL', True)
    parameters.put('enl', 1.0)
    parameters.put('numLooksStr', "1")
    parameters.put('windowSize', '7x7')
    parameters.put('targetWindowSizeStr', '3x3')
    parameters.put('sigmaStr', "0.9")
    parameters.put('anSize', 50)

    if VERBOSE:
        print("Speckle filtering...")

    return snappy.GPF.createProduct('Speckle-Filter', parameters, prod)


def create_subset(prod: snappy.Product, subset_polygon: str):
    """Creates a subset of a product.

    If the specified polygon is not contained in the product, ValueError is raised.

    :param prod: Product to be cropped.
    :param subset_polygon: String. Polygon in WKT.
    :return: Subset product.
    """
    parameters = snappy.HashMap()

    # parameters.put('referenceBand', "")
    parameters.put('geoRegion', subset_polygon)
    parameters.put('subSamplingX', 1)
    parameters.put('subSamplingY', 1)
    parameters.put('fullSwath', False)
    # parameters.put('tiePointGrids', "")
    parameters.put('copyMetadata', True)

    if VERBOSE:
        print("Creating subset...")
    # If the polygon was outside of the product's scope, None is returned.
    subset = snappy.GPF.createProduct('Subset', parameters, prod)

    if not subset:  # If subset is None, then polygon was invalid.
        raise ValueError("Given coordinates are out of input's scope.")

    return subset


def write_product(prod, out_path, out_fmt: str = "BEAM-DIMAP", use_gpf: bool = True, incremental: bool = False):
    """
    Writes product to disk and executes all operators called before it.
    :param prod: Opened product.
    :param out_path: str. Output path to which the product will be saved.
    :param out_fmt: str, optional. Output format. Defaults to BEAM-DIMAP.
    :param use_gpf: bool, optional. If set, snappy.GPF.writeProduct method will be used (better performance).
        Otherwise, snappy.ProductIO.writeProduct will be used. Defaults to True.
    :param incremental: bool, optional. If set, incremental storing option will be used when use_gpf is set. Defaults to False.
    :return: The processed and saved product.
    """
    if not use_gpf:
        snappy.ProductIO.writeProduct(prod, out_path, out_fmt)
    else:
        file = snappy.File(out_path)
        snappy.GPF.writeProduct(prod, file, out_fmt, incremental,
                                snappy.ProgressMonitor.NULL)

    return read_product(f"{out_path}.dim")  # TODO change args to always be BEAM-DIMAP


def terrain_correction(prod, source_bands: str = "", dem_name: str = "SRTM 3Sec", external_dem_file: str = "",
                       external_aux_file: str = "", mask_out_sea: bool = False):
    """
    Applies terrain correction to the passed product.
    :param prod: Opened product.
    :param source_bands: str, optional. Source bands to use. If empty string is passed, all bands will be used. Defaults to "".
    :param dem_name: str, optional. DEM name to use. Defaults to SRTM 3Sec.
    :param external_dem_file: str, optional. Defaults to "".
    :param external_aux_file: str, optional. Defaults to "".
    :param mask_out_sea: bool, optional. If set, sea will be masked out. Defaults to False.
    :return: Modified product.
    """
    # Terrain-Correction Operator - snappy
    parameters = snappy.HashMap()

    if source_bands:
        parameters.put('sourceBands', source_bands)

    parameters.put('demName', dem_name)

    if external_dem_file:
        parameters.put('externalDEMFile', '')

    parameters.put("externalDEMNoDataValue", 0.0)
    parameters.put("externalDEMApplyEGM", True)
    parameters.put("demResamplingMethod", "BILINEAR_INTERPOLATION")
    parameters.put("imgResamplingMethod", "BILINEAR_INTERPOLATION")
    parameters.put("pixelSpacingInMeter", 10.0)
    parameters.put("pixelSpacingInDegree", 8.983152841195215E-5)
    parameters.put("mapProjection", "WGS84(DD)")
    parameters.put("alignToStandardGrid", False)
    parameters.put("standardGridOriginX", 0.0)
    parameters.put("standardGridOriginY", 0.0)

    parameters.put("nodataValueAtSea", mask_out_sea)  # do not mask out areas without elevation

    parameters.put("saveDEM", False)
    parameters.put("saveLatLon", False)
    parameters.put("saveIncidenceAngleFromEllipsoid", False)
    parameters.put("saveLocalIncidenceAngle", False)
    parameters.put("saveProjectedLocalIncidenceAngle", False)
    parameters.put("saveSelectedSourceBand", True)
    parameters.put("saveLayoverShadowMask", False)
    parameters.put("outputComplex", False)
    parameters.put("applyRadiometricNormalization", False)
    parameters.put("saveSigmaNought", False)
    parameters.put("saveGammaNought", False)
    parameters.put("saveBetaNought", False)
    parameters.put("incidenceAngleForSigma0", "Use projected local incidence angle from DEM")
    parameters.put("incidenceAngleForGamma0", "Use projected local incidence angle from DEM")
    parameters.put("auxFile", "Latest Auxiliary File")

    if external_aux_file:
        parameters.put("externalAuxFile", external_aux_file)

    if VERBOSE:
        print("Correcting terrain...")

    return snappy.GPF.createProduct('Terrain-Correction', parameters, prod)


def thermal_noise_removal(prod):
    """
    Removes thermal noise from the passed product.
    :param prod: Opened product.
    :return: Modified product.
    """
    parameters = snappy.HashMap()
    parameters.put('removeThermalNoise', True)

    if VERBOSE:
        print("Removing thermal noise...")

    return snappy.GPF.createProduct('ThermalNoiseRemoval', parameters, prod)


def create_stack(*products: Collection[snappy.Product]) -> snappy.Product:
    """Creates a co-registration stack. Products will be geo-referenced.

    :param products: Products to stack.
    :return: The resulting stack product.
    """
    params = snappy.HashMap()
    params.put("initialOffsetMethod", "Product Geolocation")

    if VERBOSE:
        print("Creating stack...")

    return snappy.GPF.createProduct("CreateStack", params, products)


def adaptive_thresholding(product: snappy.Product, bg_window: float = 800.0, estimate_bg: bool = False,
                          guard_window: float = 500.0, pfa: float = 12.5, target_window: int = 30) -> snappy.Product:
    """
    Applies adaptive thresholding on the passed product.
    :param product: Opened product.
    :param bg_window: float, optional. Background window. Defaults to 800.0.
    :param estimate_bg: bool, optional. If set, background will be estimated. Defaults to False.
    :param guard_window: float, optional. Guard window. Defaults to 500.0.
    :param pfa: float, optional. Defaults to 12.5.
    :param target_window: int, optional. Target window. Defaults to 30.
    :return: Modified product.
    """
    params = snappy.HashMap()

    params.put("targetWindowSizeInMeter", target_window)
    params.put("guardWindowSizeInMeter", guard_window)
    params.put("backgroundWindowSizeInMeter", bg_window)
    params.put("pfa", pfa)
    params.put("estimateBackground", estimate_bg)

    if VERBOSE:
        print("Applying adaptive thresholding subset...")

    return snappy.GPF.createProduct("AdaptiveThresholding", params, product)


def object_discrimination(product: snappy.Product, max_tgt: float = 600.0, min_tgt: float = 30.0) -> snappy.Product:
    """
    Discriminates objects after adaptive thresholding. Make sure adaptive_thresholding is called.
    :param product: Opened product.
    :param max_tgt: float, optional. Max target size. Defaults to 600.
    :param min_tgt: float, optional. Min target size. Defaults to 30.
    :return: Modified product.
    """
    params = snappy.HashMap()

    params.put("minTargetSizeInMeter", min_tgt)

    params.put("maxTargetSizeInMeter", max_tgt)

    if VERBOSE:
        print("Discriminating objects...")

    return snappy.GPF.createProduct("Object-Discrimination", params, product)


def land_sea_mask(product: snappy.Product, source_bands: str = "", land_mask: bool = True,
                  shore_line_extension: int = 10, use_srtm: bool = True, geometry: str = "") -> snappy.Product:
    """
    Applies land-sea mask on the passed product.
    :param product: Opened product.
    :param source_bands: str, optional. If left blank, all soruce bands will be used. Defaults to "".
    :param land_mask: bool, optional. If set, mask will be masked out. Defaults to True.
    :param shore_line_extension: int, optional. Extension to the shore line. Defaults to 10.
    :param use_srtm: bool, optional. Use SRTM if set. Defaults to True.
    :param geometry: str, optional. Custom land mask name to use. Defaults to "".
    :return: Modified product.
    """
    params = snappy.HashMap()

    if source_bands:
        params.put("sourceBands", source_bands)

    params.put("landMask", land_mask)

    params.put("useSRTM", use_srtm)

    if geometry:
        params.put("geometry", "")

    params.put("invertGeometry", False)

    params.put("shorelineExtension", shore_line_extension)

    if VERBOSE:
        print("Applying land-sea mask...")

    return snappy.GPF.createProduct("Land-Sea-Mask", params, product)
