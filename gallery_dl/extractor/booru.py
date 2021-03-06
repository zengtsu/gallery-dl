# -*- coding: utf-8 -*-

# Copyright 2015 Mike Fährmann
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Base classes for extractors for danbooru and co"""

from .common import Extractor, Message
from .. import text
import xml.etree.ElementTree as ET
import json
import urllib.parse

class BooruExtractor(Extractor):
    """Base class for all booru extractors"""
    info = {}
    headers = {}
    page = "page"
    api_url = ""
    category = ""

    def __init__(self):
        Extractor.__init__(self)
        self.params = {"limit": 50}
        self.setup()

    def items(self):
        yield Message.Version, 1
        yield Message.Directory, self.get_job_metadata()
        yield Message.Headers, self.headers
        for data in self.items_impl():
            try:
                yield Message.Url, self.get_file_url(data), self.get_file_metadata(data)
            except KeyError:
                continue

    def items_impl(self):
        pass

    def setup(self):
        pass

    def update_page(self, reset=False):
        """Update the value of the 'page' parameter"""
        # Override this method in derived classes if necessary.
        # It is usually enough to just adjust the 'page' attribute
        if reset is False:
            self.params[self.page] += 1
        else:
            self.params[self.page] = 1

    def get_job_metadata(self):
        """Collect metadata for extractor-job"""
        # Override this method in derived classes
        return {
            "category": self.category,
        }

    def get_file_metadata(self, data):
        """Collect metadata for a downloadable file"""
        data["category"] = self.category
        return text.nameext_from_url(self.get_file_url(data), data)

    def get_file_url(self, data):
        """Extract download-url from 'data'"""
        url = data["file_url"]
        if url.startswith("/"):
            url = urllib.parse.urljoin(self.api_url, url)
        return url


class JSONBooruExtractor(BooruExtractor):
    """Base class for JSON based API responses"""
    def items_impl(self):
        self.update_page(reset=True)
        while True:
            images = json.loads(
                self.request(self.api_url, verify=True, params=self.params,
                             headers=self.headers).text
            )
            for data in images:
                yield data
            if len(images) < self.params["limit"]:
                return
            self.update_page()


class XMLBooruExtractor(BooruExtractor):
    """Base class for XML based API responses"""
    def items_impl(self):
        self.update_page(reset=True)
        while True:
            root = ET.fromstring(
                self.request(self.api_url, verify=True, params=self.params).text
            )
            for item in root:
                yield item.attrib
            if len(root) < self.params["limit"]:
                return
            self.update_page()


class BooruTagExtractor(BooruExtractor):
    """Extractor for images based on search-tags"""
    directory_fmt = ["{category}", "{tags}"]
    filename_fmt = "{category}_{id}_{md5}.{extension}"

    def __init__(self, match):
        BooruExtractor.__init__(self)
        self.tags = text.unquote(match.group(1))
        self.params["tags"] = self.tags

    def get_job_metadata(self):
        return {
            "category": self.category,
            "tags": self.tags,
        }


class BooruPoolExtractor(BooruExtractor):
    """Extractor for image-pools"""
    directory_fmt = ["{category}", "pool", "{pool}"]
    filename_fmt = "{category}_{id}_{md5}.{extension}"

    def __init__(self, match):
        BooruExtractor.__init__(self)
        self.pool = match.group(1)
        self.params["tags"] = "pool:" + self.pool

    def get_job_metadata(self):
        return {
            "category": self.category,
            "pool": self.pool,
        }


class BooruPostExtractor(BooruExtractor):
    """Extractor for single images"""
    directory_fmt = ["{category}"]
    filename_fmt = "{category}_{id}_{md5}.{extension}"

    def __init__(self, match):
        BooruExtractor.__init__(self)
        self.post = match.group(1)
        self.params["tags"] = "id:" + self.post
