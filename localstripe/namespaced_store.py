import contextvars
import copy

current_namespace = contextvars.ContextVar('namespace', default='default')


class NamespacedStore:
    """Dict-like store partitioned by namespace via contextvars.

    Seed data is frozen as a template via snapshot_template().
    Each new namespace gets a deep copy of the template on first access.
    """

    def __init__(self):
        self._namespaces = {}   # namespace -> dict
        self._template = {}     # frozen seed data snapshot

    def snapshot_template(self):
        """Freeze current default namespace as the template for new namespaces."""
        default = self._namespaces.get('default', {})
        self._template = copy.deepcopy(default)

    def _get_ns(self):
        ns = current_namespace.get()
        if ns not in self._namespaces:
            self._namespaces[ns] = copy.deepcopy(self._template)
        return self._namespaces[ns]

    def __getitem__(self, key):
        return self._get_ns()[key]

    def __setitem__(self, key, value):
        self._get_ns()[key] = value

    def __delitem__(self, key):
        del self._get_ns()[key]

    def __contains__(self, key):
        return key in self._get_ns()

    def items(self):
        return self._get_ns().items()

    def keys(self):
        return self._get_ns().keys()

    def values(self):
        return self._get_ns().values()

    def get(self, key, default=None):
        return self._get_ns().get(key, default)

    def pop(self, key, *args):
        return self._get_ns().pop(key, *args)

    def clear(self):
        """Clear the current namespace (used by flush endpoint)."""
        ns = current_namespace.get()
        if ns in self._namespaces:
            self._namespaces[ns].clear()

    def clear_namespace(self, namespace):
        """Remove a namespace entirely. Next access re-clones from template."""
        self._namespaces.pop(namespace, None)

    def clear_all_namespaces(self):
        """Remove all namespaces. Used for full CI cleanup."""
        self._namespaces.clear()

    def try_load_from_disk(self):
        """No-op for NamespacedStore (persistence disabled)."""
        pass

    def dump_to_disk(self):
        """No-op for NamespacedStore (persistence disabled)."""
        pass

    def update(self, *args, **kwargs):
        """Update the current namespace's dict."""
        self._get_ns().update(*args, **kwargs)

    def __len__(self):
        return len(self._get_ns())

    def __iter__(self):
        return iter(self._get_ns())
