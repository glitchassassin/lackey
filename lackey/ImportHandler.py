import sys
import os.path

if sys.version_info[0] == 3:
    from importlib.abc import MetaPathFinder
    from importlib.util import spec_from_file_location
    from importlib.machinery import SourceFileLoader

    class SikuliFinder(MetaPathFinder):
        def find_spec(self, fullname, path, target=None):
            if "." in fullname:
                name = fullname.split(".")[-1]
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
    sys.meta_path.append(SikuliFinder())
elif sys.version_info[0] == 2:
    import imp

    class SikuliFinder(object):
        def __init__(self, path):
            self.path = path

        @classmethod
        def find_module(cls, name, path=None):
            for entry in sys.path:
                sikuli_path = os.path.join(entry, "{}.sikuli".format(name))
                filename = os.path.join(sikuli_path, "{}.py".format(name))
                if not os.path.exists(filename):
                    continue
            
                # Found what we're looking for. Add to path.
                sys.path.append(sikuli_path)
                return cls(filename)
        
        def load_module(self, name):
            if name in sys.modules:
                return sys.modules[name]
            with open(self.path, "r") as project:
                mod = imp.load_module(name, project, self.path, (".py", "r", imp.PY_SOURCE))
            return mod
    sys.meta_path.append(SikuliFinder)