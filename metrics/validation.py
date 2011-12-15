LIST_SCHEMA = {
    'type': 'array',
    'items': [
        {
            'type': 'object',
            'properties': {
                'rank': {'type': 'integer'},
                'name': {'type': 'string'},
                'value': {'type': 'integer', 'required': False},
            }
        }
    ],
    'additionalItems': True,
}