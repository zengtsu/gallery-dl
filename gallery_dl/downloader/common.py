# -*- coding: utf-8 -*-

# Copyright 2014, 2015 Mike Fährmann
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Common classes and constants used by downloader modules."""

import os

class BasicDownloader():
    """Base class for downloader modules"""

    max_tries = 5

    def download(self, url, fileobj):
        """Download the resource at 'url' and write it to a file-like object"""
        try:
            return self.download_impl(url, fileobj)
        except:
            # remove file if download failed
            try:
                fileobj.close()
                os.unlink(fileobj.name)
            except AttributeError:
                pass
            raise

    def download_impl(self, url, file_handle):
        """Actual implementaion of the download process"""
        pass
