from .errors import UserError
from .resources import Token

# https://stripe.com/docs/testing
test_tokens = [
    {
        'id': 'tok_visa',
        'number': '4242424242424242'
    },
    {
        'id': 'tok_amex',
        'number': '371449635398431',
        'cvc': '3412'
    },
    {
        'id': 'tok_threeDSecure2Required',
        'number': '4000000000003220'
    },
    {
        'id': 'tok_chargeDeclinedInsufficientFunds',
        'number': '4000000000009995'
    },
]


def create_test_tokens():
    for token in test_tokens:
        try:
            Token._api_retrieve(token.get('id'))
            continue
        except UserError:
            pass
        Token._api_create(id=token.get('id'), card={
            'number': token.get('number'),
            'exp_month': token.get('exp_month', 12),
            'exp_year': token.get('exp_year', 2030),
            'cvc': token.get('cvc', '314')
        })
