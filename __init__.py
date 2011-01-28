#import pkgutil
#import imp
#import os
#import sys
#
#plugin_path = [os.path.join(sys.path[0]), 'plugins')]
#
#for loader, name, ispkg in pkgutil.iter_modules(plugin_path):
#    file, pathname, desc = imp.find_module(name, plugin_path)
#
#    imp.load_module(name, file, pathname, desc)
#
#plugins = []
#
#class Plugin(object):
#    pass
#
#def register_plugin(plugin):
#    global plugins
#
#    plugins += [plugin]
