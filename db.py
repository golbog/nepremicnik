from datetime import datetime
from pathlib import Path
import hashlib

from peewee import *


db = SqliteDatabase(None)


class BaseModel(Model):
    class Meta:
        database = db


class Listing(BaseModel):
    id = CharField(unique=True)
    title = CharField()
    link = CharField()
    type = CharField()
    short_description = CharField()
    long_description = CharField()
    size = FloatField()
    price = FloatField()
    agency = CharField()
    deleted = BooleanField(default=False)
    timestamp = DateTimeField(default=datetime.now)

    def __repr__(self):
        return f"Listing: {self.title}-{self.id}\n" \
               f"Link: {self.link}\n" \
               f"Info: {self.type} - {self.size}\n" \
               f"Price: {self.price}\n" \
               f"Agency: {self.agency}"


class Image(BaseModel):
    listing = ForeignKeyField(Listing, backref="images")
    path = CharField()
    sha1sum = CharField(unique=True)


class Change(BaseModel):
    listing = ForeignKeyField(Listing, backref="changes")
    column = CharField()
    change = AnyField()
    timestamp = DateTimeField(default=datetime.now)


class DB:
    """
    Class for abstracting database interface
    """
    _TABLES = {Listing, Image, Change}

    def __init__(self, name: str, images_folder: str = "images"):
        """
        :param name: name of the database
        :param images_folder: folder where images will be saved
        """
        self._db = db
        self._db.init(name)
        self._images_folder = Path(images_folder)

        self._db.create_tables([Listing, Image, Change])

    @staticmethod
    def add_listing(**kwargs) -> Listing:
        """
        Add new listing to the database
        :param kwargs: all the parameters needed for initializing Listing
        :return: newly added Listing instance
        """
        listing = Listing.create(**kwargs)
        return listing

    @staticmethod
    def get_listing(listing_id: str) -> Listing:
        """ Get listing from database  """
        return Listing.get(listing_id == Listing.id)

    def add_image(self, listing_id: str, image: bytes, file_type: str = "jpg") -> Image:
        """
        Add image to the database.
        Actual image will be saved to the disk, database will only hold its hash and path.
        :param listing_id: owner of the images
        :param image: listing in bytes
        :param file_type: file type of image
        :return: newly added Image instance
        """
        img_hash = hashlib.sha1(image).hexdigest()
        img_path = self._images_folder / listing_id / f"{img_hash}.{file_type}"
        img_path.parent.mkdir(parents=True, exist_ok=True)
        with img_path.open("wb") as f:
            f.write(image)
        img = Image.create(listing=listing_id, path=str(img_path), sha1sum=hashlib.sha1(image).hexdigest())
        return img

    def mark_deleted(self, listing_id: str):
        """ TODO """

    def mark_undeleted(self, listing_id: str):
        """ TODO """

    @staticmethod
    def update_listing(listing_id: str, log_changes=True, **kwargs):
        """
        Update listing with the new data.
        :param listing_id: id of the listing
        :param log_changes: whether to save change into Change table - old value will be saved
        :param kwargs: (key (attr name) - new value) pairs
        """
        listing = Listing.get(listing_id == Listing.id)

        for k, v in kwargs.items():
            if k in Listing._meta.sorted_field_names:
                # if we're logging changes we need to first save the old value
                if log_changes:
                    Change.create(listing=listing_id, column=k, change=getattr(listing, k))

                # for some reason we still need to provide where statement, even though we're calling update on a single row
                listing.update({k: v}).where(listing_id == Listing.id).execute()

    @staticmethod
    def exists(listing_id: str) -> bool:
        """ Does listing exist """
        return Listing.select().where(Listing.id == listing_id).exists()
