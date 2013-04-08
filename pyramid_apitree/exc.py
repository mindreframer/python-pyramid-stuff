""" Copyright (c) 2013 Josh Matthias <pyramid.apitree@gmail.com> """

class Error(Exception):
    """ Base class for errors. """

class BadAPITreeError(Error):
    """ Provided API tree dictionary has invalid structure or composition. """