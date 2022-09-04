from __future__ import annotations
import dataclasses
import inspect
from typing import Set, Generator, List

from lxml import html
import time

import requests
import re


@dataclasses.dataclass
class Listing:
    """
    Simple dataclass for structuring scrapped listings.
    Provides utility functions for:
     - getting attr names where two listings differ
     - constructor from dictionary
    """
    id: str
    title: str
    link: str
    type: str
    short_description: str
    long_description: str
    size: float
    price: float
    agency: str

    @classmethod
    def from_dict(cls, dic: dict):
        """
        Create new Listing instance from dict.
        Will ignore any unused attributes, but will fail if not all required are provided.
        :param dic: dictionary with all the required attributes
        :return: new Listing instance
        """
        return cls(**{
            k: v for k, v in dic.items()
            if k in inspect.signature(cls).parameters
        })

    def get_different_attrs_from(self, other: Listing) -> Set[str]:
        """
        Return set of all attrs where this Listing differs from the `other`
        :param other: other listing
        :return: list of all attr names where they differ
        """
        res = set()
        for k in self.__annotations__.keys():
            if getattr(self, k) != getattr(other, k):
                res.add(k)
        return res


def _get_page_number(url: str) -> int:
    """ Get page number from nepremicnine.net search URL """
    reg = re.search(r"/[0-9]/", url)
    if reg is None:
        return 1
    num = reg.group(0).strip("/")
    return int(num)


def _get_base_url(url: str) -> str:
    """ Get the base URL from the whole URL """
    return re.search(r"^.+?[^\/:](?=[?\/]|$)", url).group(0)


def listings(url: str, sleep_between_pages: float = 1) -> Generator[Listing]:
    """ Generator for all the listings within the given URL including all the additional pages """
    page_number = _get_page_number(url)
    base_url = _get_base_url(url)

    while True:
        page = requests.get(url)
        page_tree = html.fromstring(page.content)
        offers = page_tree.xpath('//div[@class="seznam"]/div[@itemprop="itemListElement"]')

        if len(offers) == 0:
            return

        for offer in offers:
            offer_id = offer.attrib["id"][1:]  # skip 'o'
            title = offer.xpath("div/h2//text()")[-1]
            link = f'{base_url}{offer.xpath("div//attribute::href")[0]}'
            offer_type = offer.xpath('div//span[@class="tipi"]')[0].text
            short_desc = offer.xpath('div//div[@class="kratek_container"]/div')[0].text
            size = offer.xpath('div//div[@class="main-data"]/span[@class="velikost"]')[0].text
            price = float(
                offer.xpath('div//div[@class="main-data"]/span[@class="cena"]')[0].text.strip("€ ,0").replace(
                    ".,", "").replace(",", "."))
            agency = offer.xpath('div//div[@class="main-data"]/span[@class="agencija"]')[0].text

            yield Listing(offer_id, title, link, offer_type, short_desc, "", size, price, agency)

        page_number += 1
        url = re.sub(r"/([0-9]+)/", f"/{page_number}/", url)
        time.sleep(sleep_between_pages)  # to reduce traffic


def get_listing_images(url: str, sleep_between: float = 0.25) -> List[bytes]:
    """ Get all images for the given listing's url """
    res = list()
    page = requests.get(url)
    if page.status_code == requests.codes.ok:
        page_tree = html.fromstring(page.content)
        imgs_el = page_tree.xpath("//div[@id='galerija']//a[contains(@href, 'slonep_oglasi')]")
        for img_el in imgs_el:
            img_url = img_el.attrib["href"]
            img_req = requests.get(img_url)
            if img_req.status_code == requests.codes.ok:
                res.append(img_req.content)
            time.sleep(sleep_between)

    return res


def get_long_description(url: str) -> str:
    """ Get the whole description for the listing's url """
    page = requests.get(url)
    final_text = ""
    if page.status_code == requests.codes.ok:
        page_tree = html.fromstring(page.content)
        desc_div = page_tree.xpath("//div[@class='web-opis']/div/*")
        for el in desc_div:
            # handle strong
            strong = el.xpath("strong")
            if len(strong) > 0:
                final_text += f"{strong[0].text} {strong[0].tail}\n"

            # handle normal p
            if el.text is not None:
                final_text += f"{el.text}\n"

            # handle ul
            ul = el.xpath("li")
            for li in ul:
                final_text += f" - {li.text}\n"
    return final_text
