""" Custom exceptions for Sikuli script """

class FindFailed(Exception):
    """ Exception: Unable to find the searched item """
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)
