import copy
import contextvars
import pytest

# We'll test the NamespacedStore class directly
from localstripe.namespaced_store import NamespacedStore, current_namespace


def test_default_namespace_is_isolated():
    """Items in default namespace aren't visible in other namespaces."""
    store = NamespacedStore()
    current_namespace.set('default')
    store['customer:cus_1'] = {'id': 'cus_1', 'name': 'Default'}
    store.snapshot_template()

    current_namespace.set('ns_abc')
    # New namespace gets template copy
    assert 'customer:cus_1' in store
    assert store['customer:cus_1']['name'] == 'Default'

    # Mutate in namespace — doesn't affect template
    store['customer:cus_1'] = {'id': 'cus_1', 'name': 'Changed'}
    assert store['customer:cus_1']['name'] == 'Changed'

    # Switch to another namespace — gets original template
    current_namespace.set('ns_xyz')
    assert store['customer:cus_1']['name'] == 'Default'


def test_namespaces_dont_see_each_others_objects():
    """Objects created in one namespace are invisible in another."""
    store = NamespacedStore()
    store.snapshot_template()

    current_namespace.set('ns_1')
    store['customer:cus_new'] = {'id': 'cus_new'}

    current_namespace.set('ns_2')
    assert 'customer:cus_new' not in store


def test_clear_namespace():
    """Clearing a namespace removes it; next access re-clones template."""
    store = NamespacedStore()
    current_namespace.set('default')
    store['plan:plan_1'] = {'id': 'plan_1'}
    store.snapshot_template()

    current_namespace.set('ns_temp')
    store['customer:cus_temp'] = {'id': 'cus_temp'}
    assert 'customer:cus_temp' in store

    store.clear_namespace('ns_temp')

    # Re-access should re-clone from template (no cus_temp)
    assert 'customer:cus_temp' not in store
    # But template data is still there
    assert 'plan:plan_1' in store


def test_items_keys_scoped_to_namespace():
    """items() and keys() only return current namespace's data."""
    store = NamespacedStore()
    store.snapshot_template()

    current_namespace.set('ns_a')
    store['customer:cus_a'] = {'id': 'cus_a'}

    current_namespace.set('ns_b')
    store['customer:cus_b'] = {'id': 'cus_b'}

    keys = list(store.keys())
    assert 'customer:cus_b' in keys
    assert 'customer:cus_a' not in keys


def test_delete_item():
    """Deleting in one namespace doesn't affect others."""
    store = NamespacedStore()
    current_namespace.set('default')
    store['coupon:cpn_1'] = {'id': 'cpn_1'}
    store.snapshot_template()

    current_namespace.set('ns_del')
    assert 'coupon:cpn_1' in store
    del store['coupon:cpn_1']
    assert 'coupon:cpn_1' not in store

    # Other namespace still has it
    current_namespace.set('ns_other')
    assert 'coupon:cpn_1' in store
