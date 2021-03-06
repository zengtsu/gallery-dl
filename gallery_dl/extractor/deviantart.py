# -*- coding: utf-8 -*-

# Copyright 2015 Mike Fährmann
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Extract images from http://www.deviantart.com/"""

from .common import Extractor, AsynchronousExtractor, Message
from .. import text
import re

class DeviantartUserExtractor(AsynchronousExtractor):
    """Extractor for all works from an artist on deviantart.com"""
    category = "deviantart"
    subcategory = "user"
    directory_fmt = ["{category}", "{artist}"]
    filename_fmt = "{category}_{index}_{title}.{extension}"
    pattern = [r"(?:https?://)?([^\.]+)\.deviantart\.com(?:/gallery)?/?$"]
    test = [("http://shimoda7.deviantart.com/gallery/", {
        "url": "63bfa8efba199e27181943c9060f6770f91a8441",
        "keyword": "c0343b41c28c87254a3f0b3241222e94f780701e",
    })]

    def __init__(self, match):
        AsynchronousExtractor.__init__(self)
        self.session.cookies["agegate_state"] = "1"
        self.artist = match.group(1)

    def items(self):
        metadata = self.get_job_metadata()
        yield Message.Version, 1
        yield Message.Directory, metadata
        for url, data in self.get_works():
            data.update(metadata)
            yield Message.Url, url, data

    def get_works(self):
        """Yield all work-items for a deviantart-artist"""
        url = "http://{}.deviantart.com/gallery/".format(self.artist)
        params = {"catpath": "/", "offset": 0}
        while True:
            num = 0
            page = self.request(url, params=params).text
            _, pos = text.extract(page, '<div data-dwait-click="GMI.wake"', '')
            while True:
                image_info, pos = text.extract(page, '<a class="thumb', '</a>', pos)
                if not image_info:
                    break
                num += 1
                yield self.get_image_metadata(image_info)
            if num != 24:
                break
            params["offset"] += 24

    def get_job_metadata(self):
        """Collect metadata for extractor-job"""
        return {
            "category": self.category,
            "artist": self.artist,
        }

    def get_image_metadata(self, image):
        """Collect metadata for an image"""
        tmatch = self.extract_data(image, 'title',
            r'(.+) by (.+), ([A-Z][a-z]{2} \d+, \d{4}) in')
        hmatch = self.extract_data(image, 'href', r'[^"]+-(\d+)')

        url, pos = text.extract(image, ' data-super-full-img="', '"', tmatch.end())
        if url:
            width , pos = text.extract(image, ' data-super-full-width="', '"', pos)
            height, pos = text.extract(image, ' data-super-full-height="', '"', pos)
        else:
            url, pos = text.extract(image, ' data-super-img="', '"', pos)
            if url:
                width , pos = text.extract(image, ' data-super-width="', '"', pos)
                height, pos = text.extract(image, ' data-super-height="', '"', pos)
            else:
                page = self.request(hmatch.group(0)).text
                _     , pos = text.extract(page, ' class="dev-content-normal "', '')
                url   , pos = text.extract(page, ' src="', '"', pos)
                width , pos = text.extract(page, ' width="', '"', pos)
                height, pos = text.extract(page, ' height="', '"', pos)
        return url, text.nameext_from_url(url, {
            "index": hmatch.group(1),
            "title": text.unescape(tmatch.group(1)),
            "artist": tmatch.group(2),
            "date": tmatch.group(3),
            "width": width,
            "height": height,
        })

    @staticmethod
    def extract_data(txt, attr, pattern):
        """Extract a HTML attribute and apply a regex to it"""
        txt, _ = text.extract(txt, ' %s="' % attr, '"')
        return re.match(pattern, txt)


class DeviantartImageExtractor(Extractor):
    """Extractor for single images from deviantart.com"""
    category = "deviantart"
    subcategory = "image"
    directory_fmt = ["{category}", "{artist}"]
    filename_fmt = "{category}_{index}_{title}.{extension}"
    pattern = [r"(?:https?://)?[^\.]+\.deviantart\.com/art/.+-(\d+)"]
    test = [("http://shimoda7.deviantart.com/art/For-the-sake-of-a-memory-10073852", {
        "url": "71345ce3bef5b19bd2a56d7b96e6b5ddba747c2e",
        "keyword": "f2dfde276a39990097935ace092811c56bc0bfec",
    })]

    def __init__(self, match):
        Extractor.__init__(self)
        self.url = match.group(0)
        self.index = match.group(1)

    def items(self):
        page = self.request(self.url).text
        data = text.extract_all(page, (
            ('title' , '"og:title" content="', '"'),
            ('image' , '"og:image" content="', '"'),
            ('width' , '"og:image:width" content="', '"'),
            ('height', '"og:image:height" content="', '"'),
            ('url'   , '"og:url" content="', '"'),
            ('description', '"og:description" content="', '"'),
            (None    , '<span class="tt-w">', ''),
            ('date'  , 'title="', '"'),
        ), values={'category': self.category, "index": self.index})[0]
        data["description"] = text.unescape(text.unescape(data["description"]))
        data["artist"] = text.extract(data["url"], "//", ".")[0]
        data["date"] = text.extract(data["date"], ", ", " in ", len(data["title"]))[0]
        text.nameext_from_url(data["image"], data)
        yield Message.Version, 1
        yield Message.Directory, data
        yield Message.Url, data["image"], data
