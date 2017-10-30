from __future__ import print_function
import importlib
import inspect
import os
import re
import tempfile
from contextlib import contextmanager

from . import desc

cacheFolderName = 'MeshroomCache'
defaultCacheFolder = os.environ.get('MESHROOM_CACHE', os.path.join(tempfile.gettempdir(), cacheFolderName))
defaultCacheFolder = defaultCacheFolder.replace("\\", "/")
nodesDesc = {}


@contextmanager
def add_to_path(p):
    import sys
    old_path = sys.path
    sys.path = sys.path[:]
    sys.path.insert(0, p)
    try:
        yield
    finally:
        sys.path = old_path


def loadNodes(folder, packageName):
    """
    """

    nodeTypes = []
    errors = []

    # temporarily add folder to python path
    with add_to_path(folder):
        # import node package
        package = importlib.import_module(packageName)
        packageName = package.packageName if hasattr(package, 'packageName') else package.__name__
        packageVersion = package.__version__

        pysearchre = re.compile('.py$', re.IGNORECASE)
        pluginFiles = filter(pysearchre.search, os.listdir(os.path.dirname(package.__file__)))
        for pluginFile in pluginFiles:
            if pluginFile.startswith('__'):
                continue

            pluginName = os.path.splitext(pluginFile)[0]
            pluginModule = '.' + pluginName
            try:
                m = importlib.import_module(pluginModule, package=package.__name__)
                p = [a for a in m.__dict__.values() if inspect.isclass(a) and issubclass(a, desc.Node)]
                if not p:
                    raise RuntimeError('No class defined in plugin: %s' % pluginModule)
                for a in p:
                    a.packageName = packageName
                    a.packageVersion = packageVersion
                nodeTypes.extend(p)
            except Exception as e:
                errors.append('  * Errors while loading "{}".\n    File: {}\n    {}'.format(pluginName, pluginFile, str(e)))

    if errors:
        print('== Error while loading the following plugins: ==')
        print('\n'.join(errors))
        print('================================================')
    return nodeTypes


def registerNodeType(nodeType):
    """ Register a Node Type based on a Node Description class.

    After registration, nodes of this type can be instantiated in a Graph.
    """
    global nodesDesc
    if nodeType.__name__ in nodesDesc:
        raise RuntimeError("Node Desc {} is already registered.".format(nodeType.__name__))
    nodesDesc[nodeType.__name__] = nodeType


def loadAllNodes(folder):
    global nodesDesc
    for f in os.listdir(folder):
        if os.path.isdir(os.path.join(folder, f)) and not f.startswith('__'):
            nodeTypes = loadNodes(folder, f)
            for nodeType in nodeTypes:
                registerNodeType(nodeType)
            print('Plugins loaded: ', ', '.join([nodeType.__name__ for nodeType in nodeTypes]))


# Load plugins
meshroomFolder = os.path.dirname(os.path.dirname(__file__))
loadAllNodes(folder=os.path.join(meshroomFolder, 'nodes'))
