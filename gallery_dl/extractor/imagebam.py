# -*- coding: utf-8 -*-

# Copyright 2014-2016 Mike Fährmann
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Extract images from http://www.imagebam.com/"""

from .common import Extractor, AsynchronousExtractor, Message
from .. import text

class ImagebamGalleryExtractor(AsynchronousExtractor):
    """Extractor for image galleries from imagebam.com"""
    category = "imagebam"
    subcategory = "gallery"
    directory_fmt = ["{category}", "{title} - {gallery-key}"]
    filename_fmt = "{num:>03}-{filename}"
    pattern = [r"(?:https?://)?(?:www\.)?imagebam\.com/gallery/([^/]+).*"]
    test = [("http://www.imagebam.com/gallery/adz2y0f9574bjpmonaismyrhtjgvey4o", {
        "url": "d7a4483b6d5ebba81950a349aad58ae034c60eda",
        "keyword": "9f54ab808d77f2517444411dfbf8686189c20b43",
        "content": "596e6bfa157f2c7169805d50075c2986549973a8",
    })]
    url_base = "http://www.imagebam.com"

    def __init__(self, match):
        AsynchronousExtractor.__init__(self)
        self.gkey = match.group(1)

    def items(self):
        data = self.get_job_metadata()
        data["num"] = 0
        yield Message.Version, 1
        yield Message.Directory, data
        for image_url, image_id in self.get_images(data["first-url"]):
            data["id"] = image_id
            data["num"] += 1
            text.nameext_from_url(image_url, data)
            yield Message.Url, image_url, data.copy()

    def get_job_metadata(self):
        """Collect metadata for extractor-job"""
        url = self.url_base + "/gallery/" + self.gkey
        page = self.request(url, encoding="utf-8").text
        data = {
            "category": self.category,
            "gallery-key": self.gkey,
        }
        data, _ = text.extract_all(page, (
            (None       , "<img src='/img/icons/photos.png'", ""),
            ("title"    , "'> ", " <"),
            ("count"    , "'>", " images"),
            ("first-url", "<a href='http://www.imagebam.com", "'"),
        ), values=data)
        return data

    def get_images(self, url):
        """Yield all image-urls and -ids for a gallery"""
        done = False
        while not done:
            page = self.request(self.url_base + url).text
            _  , pos = text.extract(page, 'class="btn btn-default" title="Next">', '')
            if pos == 0:
                done = True
            else:
                url, pos = text.extract(page, ' href="', '"', pos-70)
            image_id , pos = text.extract(page, '<img class="image" id="', '"', pos)
            image_url, pos = text.extract(page, ' src="', '"', pos)
            yield image_url, image_id



class ImagebamImageExtractor(Extractor):
    """Extractor for single images from imagebam.com"""
    category = "imagebam"
    subcategory = "image"
    directory_fmt = ["{category}"]
    filename_fmt = "{filename}"
    pattern = [r"(?:https?://)?(?:www\.)?imagebam\.com/image/([0-9a-f]{15})"]
    test = [("http://www.imagebam.com/image/94d56c502511890", {
        "url": "94add9417c685d113a91bcdda4916e9538b5f8a9",
        "keyword": "046f049533126bb0ee7f81419f59371c6903df9e",
        "content": "0c8768055e4e20e7c7259608b67799171b691140",
    })]

    def __init__(self, match):
        Extractor.__init__(self)
        self.token = match.group(1)

    def items(self):
        data = {"category": self.category, "token": self.token}
        page = self.request("http://www.imagebam.com/image/" + self.token).text
        url = text.extract(page, 'property="og:image" content="', '"')[0]
        text.nameext_from_url(url, data)
        yield Message.Version, 1
        yield Message.Directory, data
        yield Message.Url, url, data
