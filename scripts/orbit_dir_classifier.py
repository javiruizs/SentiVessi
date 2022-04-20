import argparse
import os


def main(args):
    # Check if output dirs exist
    asc_path = os.path.join(args.srcs_dir, args.ascending)
    if not os.path.exists(asc_path):
        os.mkdir(asc_path)

    dsc_path = os.path.join(args.srcs_dir, args.descending)
    if not os.path.exists(dsc_path):
        os.mkdir(dsc_path)

    # Get products
    prods = [prod for prod in os.listdir(args.srcs_dir) if prod.endswith(".zip")]

    # Import snappy now so JVM is only created if there are files
    if prods:
        import snappy

    for prod in prods:
        p_full_path = os.path.join(args.srcs_dir, prod)
        p = snappy.ProductIO.readProduct(p_full_path)
        orbit = str(p.getMetadataRoot().getElement('Abstracted_Metadata').getAttribute('PASS').getData())
        # look = p.getMetadataRoot().getElement('Abstracted_Metadata').getAttribute('antenna_pointing').getData()

        p.dispose()  # Closes product so moving is possible

        print(f"{prod}'s orbit direction: {orbit}")

        if not args.dry:
            if orbit == "ASCENDING":
                dest = args.ascending
            else:
                dest = args.descending

            os.rename(p_full_path, os.path.join(args.srcs_dir, dest, prod))

            # Move quicklook if exists
            basename, _ = os.path.splitext(prod)
            quicklook = basename + ".jpeg"
            if os.path.exists(quicklook):
                os.rename(quicklook, os.path.join(args.srcs_dir, dest, quicklook))

            print(f"Moved to {dest} folder.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Sorts Sentinel-1 products by ascending or descending orbit.")
    parser.add_argument("prods_dir", type=str)
    parser.add_argument("-a", "--ascending", type=str, default="Ascending", help="Ascending products directory name.")
    parser.add_argument("-d", "--descending", type=str, default="Descending",
                        help="Descending products directory name.")
    parser.add_argument("--dry", help="Dry run. Only print on console.", action="store_true")

    args = parser.parse_args()

    main(args)
