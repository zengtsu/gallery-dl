# -*- coding: utf-8 -*-

# Copyright 2016 Mike Fährmann
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Extract images from http://imgtrex.com/"""

from .common import Extractor, Message
from .. import text

class ImgtrexImageExtractor(Extractor):
    """Extractor for single images from imgtrex.com"""
    category = "imgtrex"
    subcategory = "image"
    directory_fmt = ["{category}"]
    filename_fmt = "{filename}"
    pattern = [r"(?:https?://)?(?:www\.)?imgtrex\.com/([^/]+)"]
    test = [("http://imgtrex.com/im0ypxq0rke4/test-テスト-&<a>.png", {
        "url": "c000618bddda42bd599a590b7972c7396d19d8fe",
        "keyword": "4d766eae04aa5457bca4992290aa28b76239d287",
        "content": "0c8768055e4e20e7c7259608b67799171b691140",
    })]

    def __init__(self, match):
        Extractor.__init__(self)
        self.token = match.group(1)

    def items(self):
        data = {"category": self.category, "token": self.token}
        page = self.request("http://imgtrex.com/" + self.token).text
        filename, pos = text.extract(page, '<title>ImgTrex: ', '</title>')
        url     , pos = text.extract(page, '<br>\n<img src="', '"', pos)
        text.nameext_from_url(filename, data)
        yield Message.Version, 1
        yield Message.Directory, data
        yield Message.Url, url, data
