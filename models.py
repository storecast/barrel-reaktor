from barrel import Store, Field, FloatField


class Price(Store):
    """Helper class to use with the new reaktor price fields."""
    amount = FloatField(target='amount')
    currency = Field(target='currency')
