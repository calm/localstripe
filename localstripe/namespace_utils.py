def get_namespace_from_api_key(api_key):
    """Extract namespace from API key.

    sk_test_ns_12345_key -> '12345'
    sk_test_12345       -> 'default'
    """
    if api_key and '_ns_' in api_key:
        parts = api_key.split('_ns_')[1]
        return parts.split('_')[0]
    return 'default'
