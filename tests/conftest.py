import pytest
from aiohttp import web

from localstripe.resources import store
from localstripe.test_tokens import create_test_tokens


def create_app():
    """Build a fresh aiohttp Application with all localstripe routes.

    We cannot reuse the module-level `app` from server.py because aiohttp
    binds it to an event loop on first use and pytest-asyncio creates a new
    loop per test.  Instead, we import all the wiring helpers and re-register
    routes on a brand-new Application each time.
    """
    from localstripe.server import (
        error_middleware,
        auth_middleware,
        add_cors_headers,
        api_create,
        api_retrieve,
        api_update,
        api_delete,
        api_list_all,
        api_extra,
        localstripe_js,
        healthcheck,
        config_webhook,
        flush_store,
    )
    from localstripe.resources import (
        Charge, Coupon, Customer, Event, Invoice, InvoiceItem,
        PaymentIntent, PaymentMethod, Plan, Price, Product, Refund,
        SetupIntent, Source, Subscription, SubscriptionItem, TaxRate,
        Token, extra_apis,
    )
    from localstripe.seed_data import seed_data

    app = web.Application(middlewares=[error_middleware, auth_middleware])
    app.on_response_prepare.append(add_cors_headers)

    # Extra routes first (so /invoices/upcoming doesn't match /invoices/{id})
    for method, url, func in extra_apis:
        app.router.add_route(method, url, api_extra(func, url))

    for cls in (Charge, Coupon, Customer, Event, Invoice, InvoiceItem,
                PaymentIntent, PaymentMethod, Plan, Price, Product, Refund,
                SetupIntent, Source, Subscription, SubscriptionItem, TaxRate,
                Token):
        for method, url, handler in (
                ('POST', '/v1/' + cls.object + 's', api_create),
                ('GET', '/v1/' + cls.object + 's/{id}', api_retrieve),
                ('POST', '/v1/' + cls.object + 's/{id}', api_update),
                ('DELETE', '/v1/' + cls.object + 's/{id}', api_delete),
                ('GET', '/v1/' + cls.object + 's', api_list_all)):
            app.router.add_route(method, url, handler(cls, url))

    app.router.add_get('/js.stripe.com/v3/', localstripe_js)
    app.router.add_get('/ping', healthcheck)
    app.router.add_post('/_config/webhooks/{id}', config_webhook)
    app.router.add_delete('/_config/data', flush_store)

    app['seed_dir'] = 'fixtures/integration_test'
    app.on_startup.append(seed_data)

    return app


@pytest.fixture
async def client(aiohttp_client):
    """Create a test client for a fresh localstripe app instance."""
    # Clear the global store so each test starts clean, then re-seed tokens.
    store.clear()
    create_test_tokens()
    app = create_app()
    return await aiohttp_client(app)


@pytest.fixture
def auth():
    """Default auth header using a secret key."""
    return {'Authorization': 'Bearer sk_test_12345'}
