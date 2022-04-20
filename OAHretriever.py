"""Adapted 'sentinelsat' script for quicker product downloads."""
import argparse as ap
import os.path

from model import Downloader


def main():
    """
    Script to download Sentinel products in a more structured, faster, and easier way than the 'sentinelsat' script.
    :return:
    """
    parser = ap.ArgumentParser(description="Script to download products from Open Access Hub listed on a CSV, .meta4, "
                                           "or JSON file.")

    parser.add_argument("-u", "--username", type=str, default="",
                        help="Username to login to Open Access Hub. If given, password"
                             "must be specified, too.")
    parser.add_argument("-p", "--password", type=str, default="",
                        help="Password to login to Open Access Hub. If given, username"
                             "must be specified, too.")
    parser.add_argument("--url", type=str, default="", required=False, help="API URL to use. If not specified, default "
                                                                            "URL in SentinelAPI will be used.")
    parser.add_argument("-f", "--file", type=str, default="",
                        help="Instead of giving username and password, a config file can be "
                             "passed. Please note this argument is mutually exclusive to -u, "
                             "-p and --url. Error will be risen if this is not taken into"
                             "consideration. File must be a .ini or .cfg file.")

    parser.add_argument("-i", "--input_file", type=str, required=True,
                        help="Product list. Can be either a CSV, .meta4 "
                             "or JSON file. Please, make sure the CSV "
                             "file uses ';' and ',' as separators and "
                             "decimal symbol, respectively.")
    parser.add_argument("-o", "--output_dirpath", type=str, default=".", required=False,
                        help="Output directory where the products "
                             "will be downloaded to.")

    parser.add_argument("--quicklooks", action="store_true", help="If specified, quicklooks will be downloaded too.")

    args = parser.parse_args()

    # Valid args conditon (user and password and not file) xor (file and not (user or password or url))
    if not (bool(args.username and args.password and not args.file) != bool(
            args.file and not (args.username or args.password or args.url))):
        parser.error("Args -u, -p and --url are mutually exclusive to -f. The correct usage is: "
                     "( -u username -p password [ --url url ] | -f file )")

    # Check login options
    if args.file:
        api = Downloader.from_file(args.file)
    elif args.url:
        api = Downloader(args.username, args.password, args.url)
    else:
        api = Downloader(args.username, args.password)

    if not api.check_creds():  # If credentials are incorrect.
        parser.error("The credentials or the url you have passed are incorrect. Please check again.")

    # Check file type
    _, ext = os.path.splitext(args.input_file)
    if ext.lower() == ".csv":
        api.download_from_csv(args.input_file, args.output_dirpath, args.quicklooks)
    elif ext.lower() == ".json":
        api.download_from_json(args.input_file, args.output_dirpath, args.quicklooks)
    elif ext.lower() == ".meta4":
        api.download_from_meta4(args.input_file, args.output_dirpath, args.quicklooks)
    else:
        parser.error(f"Unrecognized input file format: '{ext}'.")


if __name__ == '__main__':
    main()
