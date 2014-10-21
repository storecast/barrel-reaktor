from barrel import Store, Field, DateField, IntField, EmbeddedStoreField
from barrel.rpc import RpcMixin
from barrel_reaktor.models import Price
from money import Money


# FIXME: this class is used as embedded for `voucherApplications` as well as for `Voucher` - a gift card
# thus it might differ from the voucher that comes in the basket position (gift card)
class Voucher(Store, RpcMixin):
    interface = 'WSVoucherMgmt'
    
    code = Field(target='code')
    text = Field(target='text')
    percentage = IntField(target='percentage')
    valid_from = DateField(target='validFrom')
    expiration_date = DateField(target='expirationDate')
    _initial_amount = EmbeddedStoreField(target='initialAmount', store_class=Price)
    _amount = EmbeddedStoreField(target='amount', store_class=Price)
    _java_cls = Field(target='javaClass')

    @property
    def initial_amount(self):
        return Money(amount=self._initial_amount.amount, currency=self._initial_amount.currency)

    @property
    def amount(self):
        return Money(amount=self._amount.amount, currency=self._amount.currency)
    
    @property
    def is_amount(self):
        return "WSTAmountVoucher" in self._java_cls
    
    @property
    def is_percent(self):
        return "WSTPercentVoucher" in self._java_cls
    
    @classmethod
    def get(cls, token):
        return cls.signature(method='getAssignedVouchers', args=[token])
