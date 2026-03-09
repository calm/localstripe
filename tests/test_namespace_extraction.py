from localstripe.namespace_utils import get_namespace_from_api_key


def test_namespace_from_api_key():
    assert get_namespace_from_api_key('sk_test_ns_abc123_key') == 'abc123'
    assert get_namespace_from_api_key('sk_test_12345') == 'default'
    assert get_namespace_from_api_key('sk_test_ns_42_key') == '42'
    assert get_namespace_from_api_key(None) == 'default'
    assert get_namespace_from_api_key('') == 'default'
