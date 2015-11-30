from qosdeploy.qosorch.common import importutils

def import_versioned_module(version, submodule=None):
    module = 'qosdeploy.v%s' % version
    if submodule:
        module = '.'.join((module, submodule))
    return importutils.import_module(module)
