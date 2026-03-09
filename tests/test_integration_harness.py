"""Integration test harness for localstripe.

Exercises all Stripe API operations that calm/api relies on, establishing a
regression baseline before any namespace-isolation refactoring.

All requests use form-encoded data to match Stripe's real API conventions.
"""
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def create_customer(client, auth, **extra):
    data = {'email': 'test@example.com', 'name': 'Test User', **extra}
    resp = await client.post('/v1/customers', data=data, headers=auth)
    assert resp.status == 200
    return await resp.json()


async def create_payment_method(client, auth, **extra):
    data = {
        'type': 'card',
        'card[number]': '4242424242424242',
        'card[exp_month]': '12',
        'card[exp_year]': '2030',
        'card[cvc]': '123',
        **extra,
    }
    resp = await client.post('/v1/payment_methods', data=data, headers=auth)
    assert resp.status == 200
    return await resp.json()


async def create_product(client, auth, **extra):
    data = {'name': 'Test Product', 'type': 'service', **extra}
    resp = await client.post('/v1/products', data=data, headers=auth)
    assert resp.status == 200
    return await resp.json()


async def create_price(client, auth, product_id, **extra):
    data = {
        'unit_amount': '1000',
        'currency': 'usd',
        'product': product_id,
        **extra,
    }
    resp = await client.post('/v1/prices', data=data, headers=auth)
    assert resp.status == 200
    return await resp.json()


async def setup_customer_with_pm(client, auth):
    """Create a customer and attach a payment method, return both."""
    cust = await create_customer(client, auth)
    pm = await create_payment_method(client, auth)
    # attach
    resp = await client.post(
        f'/v1/payment_methods/{pm["id"]}/attach',
        data={'customer': cust['id']},
        headers=auth,
    )
    assert resp.status == 200
    pm = await resp.json()
    return cust, pm


# ---------------------------------------------------------------------------
# Customers
# ---------------------------------------------------------------------------

class TestCustomers:
    async def test_create(self, client, auth):
        body = await create_customer(client, auth)
        assert body['object'] == 'customer'
        assert body['email'] == 'test@example.com'

    async def test_retrieve(self, client, auth):
        cust = await create_customer(client, auth)
        resp = await client.get(f'/v1/customers/{cust["id"]}', headers=auth)
        assert resp.status == 200
        body = await resp.json()
        assert body['id'] == cust['id']

    async def test_update(self, client, auth):
        cust = await create_customer(client, auth)
        resp = await client.post(
            f'/v1/customers/{cust["id"]}',
            data={'name': 'Updated'},
            headers=auth,
        )
        assert resp.status == 200
        body = await resp.json()
        assert body['name'] == 'Updated'

    async def test_list(self, client, auth):
        await create_customer(client, auth)
        resp = await client.get('/v1/customers', headers=auth)
        assert resp.status == 200
        body = await resp.json()
        assert body['object'] == 'list'
        assert len(body['data']) >= 1

    async def test_create_source(self, client, auth):
        cust = await create_customer(client, auth)
        resp = await client.post(
            f'/v1/customers/{cust["id"]}/sources',
            data={'source': 'tok_visa'},
            headers=auth,
        )
        assert resp.status == 200
        body = await resp.json()
        assert body['object'] == 'card'


# ---------------------------------------------------------------------------
# Payment Methods
# ---------------------------------------------------------------------------

class TestPaymentMethods:
    async def test_create(self, client, auth):
        pm = await create_payment_method(client, auth)
        assert pm['object'] == 'payment_method'
        assert pm['type'] == 'card'

    async def test_retrieve(self, client, auth):
        pm = await create_payment_method(client, auth)
        resp = await client.get(
            f'/v1/payment_methods/{pm["id"]}', headers=auth
        )
        assert resp.status == 200
        body = await resp.json()
        assert body['id'] == pm['id']

    async def test_attach(self, client, auth):
        cust = await create_customer(client, auth)
        pm = await create_payment_method(client, auth)
        resp = await client.post(
            f'/v1/payment_methods/{pm["id"]}/attach',
            data={'customer': cust['id']},
            headers=auth,
        )
        assert resp.status == 200
        body = await resp.json()
        assert body['customer'] == cust['id']


# ---------------------------------------------------------------------------
# Payment Intents
# ---------------------------------------------------------------------------

class TestPaymentIntents:
    async def test_create(self, client, auth):
        resp = await client.post(
            '/v1/payment_intents',
            data={'amount': '2000', 'currency': 'usd'},
            headers=auth,
        )
        assert resp.status == 200
        body = await resp.json()
        assert body['object'] == 'payment_intent'
        assert body['amount'] == 2000

    async def test_retrieve(self, client, auth):
        resp = await client.post(
            '/v1/payment_intents',
            data={'amount': '1000', 'currency': 'usd'},
            headers=auth,
        )
        pi = await resp.json()
        resp = await client.get(
            f'/v1/payment_intents/{pi["id"]}', headers=auth
        )
        assert resp.status == 200
        body = await resp.json()
        assert body['id'] == pi['id']

    async def test_confirm(self, client, auth):
        cust, pm = await setup_customer_with_pm(client, auth)
        resp = await client.post(
            '/v1/payment_intents',
            data={
                'amount': '5000',
                'currency': 'usd',
                'customer': cust['id'],
                'payment_method': pm['id'],
            },
            headers=auth,
        )
        pi = await resp.json()
        resp = await client.post(
            f'/v1/payment_intents/{pi["id"]}/confirm',
            headers=auth,
        )
        assert resp.status == 200
        body = await resp.json()
        assert body['status'] in ('succeeded', 'requires_action')

    async def test_cancel(self, client, auth):
        resp = await client.post(
            '/v1/payment_intents',
            data={'amount': '1000', 'currency': 'usd'},
            headers=auth,
        )
        pi = await resp.json()
        resp = await client.post(
            f'/v1/payment_intents/{pi["id"]}/cancel',
            headers=auth,
        )
        assert resp.status == 200
        body = await resp.json()
        assert body['status'] == 'canceled'


# ---------------------------------------------------------------------------
# Setup Intents
# ---------------------------------------------------------------------------

class TestSetupIntents:
    async def test_create(self, client, auth):
        resp = await client.post(
            '/v1/setup_intents',
            data={'usage': 'off_session'},
            headers=auth,
        )
        assert resp.status == 200
        body = await resp.json()
        assert body['object'] == 'setup_intent'

    async def test_retrieve(self, client, auth):
        resp = await client.post(
            '/v1/setup_intents',
            data={'usage': 'off_session'},
            headers=auth,
        )
        si = await resp.json()
        resp = await client.get(
            f'/v1/setup_intents/{si["id"]}', headers=auth
        )
        assert resp.status == 200
        body = await resp.json()
        assert body['id'] == si['id']


# ---------------------------------------------------------------------------
# Subscriptions
# ---------------------------------------------------------------------------

class TestSubscriptions:
    async def _make_subscription(self, client, auth):
        cust, pm = await setup_customer_with_pm(client, auth)
        product = await create_product(client, auth)
        # Subscriptions in localstripe use Plan (not Price)
        resp = await client.post('/v1/plans', data={
            'amount': '2000',
            'currency': 'usd',
            'interval': 'month',
            'product': product['id'],
        }, headers=auth)
        assert resp.status == 200
        plan = await resp.json()
        # Set default payment method on customer
        await client.post(
            f'/v1/customers/{cust["id"]}',
            data={
                'invoice_settings[default_payment_method]': pm['id'],
            },
            headers=auth,
        )
        resp = await client.post(
            '/v1/subscriptions',
            data={
                'customer': cust['id'],
                'items[0][plan]': plan['id'],
            },
            headers=auth,
        )
        assert resp.status == 200
        sub = await resp.json()
        return sub, cust, plan

    async def test_create(self, client, auth):
        sub, _, _ = await self._make_subscription(client, auth)
        assert sub['object'] == 'subscription'

    async def test_retrieve(self, client, auth):
        sub, _, _ = await self._make_subscription(client, auth)
        resp = await client.get(
            f'/v1/subscriptions/{sub["id"]}', headers=auth
        )
        assert resp.status == 200
        body = await resp.json()
        assert body['id'] == sub['id']

    async def test_list(self, client, auth):
        await self._make_subscription(client, auth)
        resp = await client.get('/v1/subscriptions', headers=auth)
        assert resp.status == 200
        body = await resp.json()
        assert body['object'] == 'list'


# ---------------------------------------------------------------------------
# Products & Prices
# ---------------------------------------------------------------------------

class TestProductsAndPrices:
    async def test_create_product(self, client, auth):
        product = await create_product(client, auth)
        assert product['object'] == 'product'

    async def test_create_price(self, client, auth):
        product = await create_product(client, auth)
        price = await create_price(client, auth, product['id'])
        assert price['object'] == 'price'
        assert price['unit_amount'] == 1000

    async def test_retrieve_price(self, client, auth):
        product = await create_product(client, auth)
        price = await create_price(client, auth, product['id'])
        resp = await client.get(f'/v1/prices/{price["id"]}', headers=auth)
        assert resp.status == 200
        body = await resp.json()
        assert body['id'] == price['id']

    async def test_list_prices(self, client, auth):
        product = await create_product(client, auth)
        await create_price(client, auth, product['id'])
        resp = await client.get('/v1/prices', headers=auth)
        assert resp.status == 200
        body = await resp.json()
        assert body['object'] == 'list'
        assert len(body['data']) >= 1


# ---------------------------------------------------------------------------
# Invoices
# ---------------------------------------------------------------------------

class TestInvoices:
    async def _create_subscription_and_invoice(self, client, auth):
        """Create a subscription (which auto-creates an invoice), return both."""
        cust, pm = await setup_customer_with_pm(client, auth)
        product = await create_product(client, auth)
        resp = await client.post('/v1/plans', data={
            'amount': '2000', 'currency': 'usd',
            'interval': 'month', 'product': product['id'],
        }, headers=auth)
        assert resp.status == 200
        plan = await resp.json()
        await client.post(
            f'/v1/customers/{cust["id"]}',
            data={'invoice_settings[default_payment_method]': pm['id']},
            headers=auth,
        )
        resp = await client.post('/v1/subscriptions', data={
            'customer': cust['id'], 'items[0][plan]': plan['id'],
        }, headers=auth)
        assert resp.status == 200
        sub = await resp.json()
        # The subscription creates an invoice; fetch it from the list
        resp = await client.get(
            f'/v1/invoices?customer={cust["id"]}', headers=auth)
        assert resp.status == 200
        invoices = await resp.json()
        assert len(invoices['data']) >= 1
        return invoices['data'][0], cust

    async def test_create_via_subscription(self, client, auth):
        inv, _ = await self._create_subscription_and_invoice(client, auth)
        assert inv['object'] == 'invoice'

    async def test_retrieve(self, client, auth):
        inv, _ = await self._create_subscription_and_invoice(client, auth)
        resp = await client.get(f'/v1/invoices/{inv["id"]}', headers=auth)
        assert resp.status == 200
        body = await resp.json()
        assert body['id'] == inv['id']

    async def test_list(self, client, auth):
        await self._create_subscription_and_invoice(client, auth)
        resp = await client.get('/v1/invoices', headers=auth)
        assert resp.status == 200
        body = await resp.json()
        assert body['object'] == 'list'
        assert len(body['data']) >= 1


# ---------------------------------------------------------------------------
# Coupons
# ---------------------------------------------------------------------------

class TestCoupons:
    async def test_create(self, client, auth):
        resp = await client.post(
            '/v1/coupons',
            data={'id': 'test_coupon_25', 'percent_off': '25', 'duration': 'once'},
            headers=auth,
        )
        assert resp.status == 200
        body = await resp.json()
        assert body['object'] == 'coupon'
        assert body['percent_off'] == 25

    async def test_retrieve(self, client, auth):
        resp = await client.post(
            '/v1/coupons',
            data={'id': 'test_coupon_10', 'percent_off': '10', 'duration': 'once'},
            headers=auth,
        )
        assert resp.status == 200
        coupon = await resp.json()
        resp = await client.get(f'/v1/coupons/{coupon["id"]}', headers=auth)
        assert resp.status == 200
        body = await resp.json()
        assert body['id'] == coupon['id']

    async def test_delete(self, client, auth):
        resp = await client.post(
            '/v1/coupons',
            data={'id': 'test_coupon_15', 'percent_off': '15', 'duration': 'once'},
            headers=auth,
        )
        assert resp.status == 200
        coupon = await resp.json()
        resp = await client.delete(
            f'/v1/coupons/{coupon["id"]}', headers=auth
        )
        assert resp.status == 200


# ---------------------------------------------------------------------------
# Charges
# ---------------------------------------------------------------------------

class TestCharges:
    async def test_create(self, client, auth):
        cust = await create_customer(client, auth)
        # Add a source to the customer
        await client.post(
            f'/v1/customers/{cust["id"]}/sources',
            data={'source': 'tok_visa'},
            headers=auth,
        )
        resp = await client.post(
            '/v1/charges',
            data={
                'amount': '2000',
                'currency': 'usd',
                'customer': cust['id'],
            },
            headers=auth,
        )
        assert resp.status == 200
        body = await resp.json()
        assert body['object'] == 'charge'
        assert body['amount'] == 2000

    async def test_retrieve(self, client, auth):
        cust = await create_customer(client, auth)
        await client.post(
            f'/v1/customers/{cust["id"]}/sources',
            data={'source': 'tok_visa'},
            headers=auth,
        )
        resp = await client.post(
            '/v1/charges',
            data={'amount': '1500', 'currency': 'usd', 'customer': cust['id']},
            headers=auth,
        )
        charge = await resp.json()
        resp = await client.get(f'/v1/charges/{charge["id"]}', headers=auth)
        assert resp.status == 200
        body = await resp.json()
        assert body['id'] == charge['id']

    async def test_list(self, client, auth):
        resp = await client.get('/v1/charges', headers=auth)
        assert resp.status == 200
        body = await resp.json()
        assert body['object'] == 'list'


# ---------------------------------------------------------------------------
# Refunds
# ---------------------------------------------------------------------------

class TestRefunds:
    async def test_create(self, client, auth):
        cust = await create_customer(client, auth)
        await client.post(
            f'/v1/customers/{cust["id"]}/sources',
            data={'source': 'tok_visa'},
            headers=auth,
        )
        resp = await client.post(
            '/v1/charges',
            data={'amount': '3000', 'currency': 'usd', 'customer': cust['id']},
            headers=auth,
        )
        charge = await resp.json()
        resp = await client.post(
            '/v1/refunds',
            data={'charge': charge['id']},
            headers=auth,
        )
        assert resp.status == 200
        body = await resp.json()
        assert body['object'] == 'refund'


# ---------------------------------------------------------------------------
# Tokens
# ---------------------------------------------------------------------------

class TestTokens:
    async def test_create(self, client, auth):
        resp = await client.post(
            '/v1/tokens',
            data={
                'card[number]': '4242424242424242',
                'card[exp_month]': '12',
                'card[exp_year]': '2030',
                'card[cvc]': '123',
                'key': 'pk_test_12345',
            },
        )
        assert resp.status == 200
        body = await resp.json()
        assert body['object'] == 'token'

    async def test_retrieve(self, client, auth):
        resp = await client.get('/v1/tokens/tok_visa', headers=auth)
        assert resp.status == 200
        body = await resp.json()
        assert body['id'] == 'tok_visa'


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------

class TestEvents:
    async def test_list(self, client, auth):
        # Create something to generate an event
        await create_customer(client, auth)
        resp = await client.get('/v1/events', headers=auth)
        assert resp.status == 200
        body = await resp.json()
        assert body['object'] == 'list'


# ---------------------------------------------------------------------------
# Seeded Fixtures
# ---------------------------------------------------------------------------

class TestSeededFixtures:
    async def test_seeded_product_exists(self, client, auth):
        resp = await client.get(
            '/v1/products/prod_testSeedOnStartUp', headers=auth
        )
        assert resp.status == 200
        body = await resp.json()
        assert body['id'] == 'prod_testSeedOnStartUp'

    async def test_seeded_price_exists(self, client, auth):
        resp = await client.get(
            '/v1/prices/price_testSeedOnStartUp', headers=auth
        )
        assert resp.status == 200
        body = await resp.json()
        assert body['id'] == 'price_testSeedOnStartUp'

    async def test_seeded_coupon_exists(self, client, auth):
        resp = await client.get(
            '/v1/coupons/coupon_testSeedOnStartUp', headers=auth
        )
        assert resp.status == 200
        body = await resp.json()
        assert body['id'] == 'coupon_testSeedOnStartUp'

    async def test_tok_visa_exists(self, client, auth):
        resp = await client.get('/v1/tokens/tok_visa', headers=auth)
        assert resp.status == 200
        body = await resp.json()
        assert body['id'] == 'tok_visa'
