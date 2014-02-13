from apps.barrel import Store, Field, LongIntField, IntField, EmbeddedStoreField
from apps.barrel.rpc import RpcMixin
from apps.reaktor_barrel.models import Price
from money import Money


# FIXME: this class is used as embedded for `voucherApplications` as well as for `Voucher` - a gift card
# thus it might differ from the voucher that comes in the basket position (gift card)
class Voucher(Store, RpcMixin):
    code = LongIntField(target='code')
    text = Field(target='text')
    percentage = IntField(target='percentage')
    _initial_amount = EmbeddedStoreField(target='initialAmount', store_class=Price)
    _amount = EmbeddedStoreField(target='amount', store_class=Price)
    # not sure if it is needed
    # java_cls = Field(target='javaClass')

    @property
    def initial_amount(self):
        return Money(amount=self._initial_amount.amount, currency=self._initial_amount.currency)

    @property
    def amount(self):
        return Money(amount=self._amount.amount, currency=self._amount.currency)
