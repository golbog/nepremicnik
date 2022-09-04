import json
import argparse
import sys
from typing import List

from db import DB
import scrapper
from messenger import Messenger


def parse_args(args: List[str]):
    """ Args parser. Check arguments for more info. """
    parser = argparse.ArgumentParser(description='Scrapper for nepremicnine.net.')
    parser.add_argument('--config', type=str, default="appdata.json",
                        help='Configuration JSON file')
    parser.add_argument('--db_name', type=str, default="nepremicnik.db",
                        help='Name of the local database')
    parser.add_argument('--no_bot', default=False, action=argparse.BooleanOptionalAction)
    parser.add_argument('--no_images', default=False, action=argparse.BooleanOptionalAction)

    args = parser.parse_args(args)
    return args


if __name__ == '__main__':
    # TODO: error handling
    # TODO: check last updated times and mark deleted after they reach certain threshold
    # parse args
    args = parse_args(sys.argv[1:])
    use_bot = not args.no_bot
    save_images = not args.no_images

    # load config file
    with open(args.config) as file:
        appdata = json.load(file)

    # init everything needed
    db = DB(args.db_name)
    if use_bot:
        messenger = Messenger(appdata["bot"]["token"], appdata["bot"]["groups"])

    for url in appdata["urls"]:
        for listing in scrapper.listings(url):
            # if already exists, check if something changed
            if db.exists(listing.id):
                old_listing = scrapper.Listing.from_dict(db.get_listing(listing.id).__data__)
                diffs = listing.get_different_attrs_from(old_listing)
                if len(diffs) > 0:
                    changes_prettified = "\n".join(f"{diff.replace('_', ' ').capitalize()}: "
                                                   f"{getattr(old_listing, diff)} -> {getattr(listing, diff)}"
                                                   for diff in diffs)
                    if use_bot:
                        messenger.send_sync(f"Changes in listing:\n{changes_prettified}")

                    for diff in diffs:
                        db.update_listing(listing.id, **{diff: getattr(listing, diff)})
            # create new one
            else:
                listing_db = db.add_listing(**listing.__dict__)
                # get whole description as we can't get it from the search resul
                long_description = scrapper.get_long_description(listing.link)
                if long_description is not None:
                    db.update_listing(listing.id, long_description=long_description, log_changes=False)

                if use_bot:
                    messenger.send_sync(f"New listing:\n{repr(listing_db)}")

                if save_images:
                    imgs = scrapper.get_listing_images(listing.link)
                    for img in imgs:
                        db.add_image(listing.id, img)
