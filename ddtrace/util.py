"""
Generic utilities for tracers
"""

import inspect


def deep_getattr(obj, attr_string, default=None):
    """
    Returns the attribute of `obj` at the dotted path given by `attr_string`
    If no such attribute is reachable, returns `default`

    >>> deep_getattr(cass, "cluster")
    <cassandra.cluster.Cluster object at 0xa20c350

    >>> deep_getattr(cass, "cluster.metadata.partitioner")
    u'org.apache.cassandra.dht.Murmur3Partitioner'

    >>> deep_getattr(cass, "i.dont.exist", default="default")
    'default'
    """
    attrs = attr_string.split('.')
    for attr in attrs:
        try:
            obj = getattr(obj, attr)
        except AttributeError:
            return default

    return obj


# monkey patch all the things
# subtle:
#   if this is the module/class we can go yolo as methods are unbound
#   and just stored like that in class __dict__
#   if this is an instance, we have to unbind the current and rebind our
#   patched method

# Also subtle:
#   If patchable is an instance and if we've already patched at the module/class level
#   then patchable[key] contains an already patched command!
#   To workaround this, check if patchable or patchable.__class__ are _dogtraced
#   If is isn't, nothing to worry about, patch the key as usual
#   But if it is, search for a "__dd_orig_{key}" method on the class, which is
#   the original unpatched method we wish to trace.

def safe_patch(patchable, key, patch_func, service, meta):
    """ takes patch_func (signature: takes the orig_method that is
    wrapped in the monkey patch == UNBOUND + service and meta) and
    attach the patched result to patchable at patchable.key
    """

    def _get_original_method(thing, key):
        orig = None
        if hasattr(thing, '_dogtraced'):
            # Search for original method
            orig = getattr(thing, "__dd_orig_{}".format(key), None)
        else:
            orig = getattr(thing, key)
            # Set it for the next time we attempt to patch `thing`
            setattr(thing, "__dd_orig_{}".format(key), orig)

        return orig

    if inspect.isclass(patchable) or inspect.ismodule(patchable):
        orig = _get_original_method(patchable, key)
        if not orig:
            # Should never happen
            return
    elif hasattr(patchable, '__class__'):
        orig = _get_original_method(patchable.__class__, key)
        if not orig:
            # Should never happen
            return
    else:
        return

    dest = patch_func(orig, service, meta)

    if inspect.isclass(patchable) or inspect.ismodule(patchable):
        setattr(patchable, key, dest)
    elif hasattr(patchable, '__class__'):
        setattr(patchable, key, dest.__get__(patchable, patchable.__class__))
