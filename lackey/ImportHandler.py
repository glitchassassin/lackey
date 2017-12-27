import sys
import os.path

from importlib.abc import MetaPathFinder
from importlib.util import spec_from_file_location
from importlib.machinery import SourceFileLoader

class SikuliFinder(MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if "." in fullname:
            *parents, name = fullname.split(".")
        else:
            name = fullname
        for entry in sys.path:
            if entry == "":
                entry = os.getcwd()
            sikuli_path = os.path.join(entry, "{}.sikuli".format(name))
            filename = os.path.join(sikuli_path, "{}.py".format(name))
            if not os.path.exists(filename):
                continue
        
            # Found what we're looking for. Add to path.
            sys.path.append(sikuli_path)

            return spec_from_file_location(fullname, filename, loader=SourceFileLoader(fullname, filename),
                submodule_search_locations=None)

        return None # we don't know how to import this