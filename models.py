from apps.barrel import Store, Field, FloatField
from apps.barrel.rpc import RpcMixin


class Nature(Store, RpcMixin):
    interface = 'WSReaktorMgmt'

    name = Field(target='name')
    home_country = Field(target='homeCountry')
    auth_hash_method = Field(target='authenticationHashAlgorithm')

    @classmethod
    def load(cls, name):
        return cls.signature(method='getNature', args=[name])


class Price(Store):
    """Helper class to use with the new reaktor price fields."""
    amount = FloatField(target='amount')
    currency = Field(target='currency')
