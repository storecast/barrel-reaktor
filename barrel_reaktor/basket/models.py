from barrel import Store, Field, BooleanField, DateField, EmbeddedStoreField
from barrel.rpc import RpcMixin
from barrel_reaktor.document.models import Document
from barrel_reaktor.models import Price
from barrel_reaktor.voucher.models import Voucher
from money import Money


class Item(Store):
    """Base item class, to be extended for specific purposes."""
    _total = EmbeddedStoreField(target='positionTotal', store_class=Price)
    _net_total = EmbeddedStoreField(target='positionNetTotal', store_class=Price)
    _tax_total = EmbeddedStoreField(target='positionTaxTotal', store_class=Price)
    _undiscounted_total = EmbeddedStoreField(target='undiscountedPositionTotal', store_class=Price)

    @property
    def total(self):
        return Money(amount=self._total.amount, currency=self._total.currency)

    @property
    def net_total(self):
        return Money(amount=self._net_total.amount, currency=self._net_total.currency)

    @property
    def tax_total(self):
        return Money(amount=self._tax_total.amount, currency=self._tax_total.currency)

    @property
    def undiscounted_total(self):
        return Money(amount=self._undiscounted_total.amount, currency=self._undiscounted_total.currency)

    @classmethod
    def add_to_basket(cls, token, basket_id, item_id):
        """A convenience shortcut to provide nicer API."""
        return cls.set_basket_quantity(token, basket_id, item_id, 1)

    @classmethod
    def remove_from_basket(cls, token, basket_id, item_id):
        """A convenience shortcut to provide nicer API."""
        return cls.set_basket_quantity(token, basket_id, item_id, 0)


class DocumentItem(Item, RpcMixin):
    """Abstraction for `BasketPosition` reaktor object, that stores `Document`."""
    interface = 'WSDocMgmt'
    document = EmbeddedStoreField(target='item', store_class=Document)

    @classmethod
    def set_basket_quantity(cls, token, basket_id, doc_id, quantity):
        """Reaktor `WSDocMgmt.changeDocumentBasketPosition` call.
        If `quantity` is 0, then removes the document from the basket.
        If `quantity` is not 0, then adds the document into the basket.
        Returns None.
        """
        return cls.signature(method='changeDocumentBasketPosition', args=[token, basket_id, doc_id, quantity])


class GiftCardItem(Item, RpcMixin):
    """Abstraction for `BasketPosition` reaktor object, that stores `Voucher`.
    Named following the naming convention at txtr.
    """
    giftcard = EmbeddedStoreField(target='item', store_class=Voucher)

    @classmethod
    def set_basket_quantity(cls, token, basket_id, voucher_code, quantity):
        """This method should call the similar to `changeDocumentBasketPosition` reaktor method, handling Voucher.
        """
        raise NotImplemented


class VoucherItem(Store, RpcMixin):
    """Abstraction for `VoucherApplication` reaktor object, that stores `Voucher`."""
    interface = 'WSVoucherMgmt'

    class Result(Store):
        """Helper class to abstract `BasketModificationResult` reaktor object."""
        code = Field(target='resultCode')
        basket = EmbeddedStoreField(target='basket', store_class='Basket')

    voucher = EmbeddedStoreField(target='voucher', store_class=Voucher)
    _discount = EmbeddedStoreField(target='discountAmount', store_class=Price)

    @property
    def discount(self):
        return Money(amount=self._discount.amount, currency=self._discount.currency)

    @classmethod
    def apply(cls, token, code, basket_id):
        """Reaktor `WSVoucherMgmt.addVoucherToBasket` call.
        Returns `Result` object.
        """
        return cls.signature(method='addVoucherToBasket', args=[token, code, basket_id], data_converter=cls.Result)

    @classmethod
    def remove(cls, token, code, basket_id):
        """Reaktor `WSVoucherMgmt.removeVoucherFromBasket` call.
        Returns `Result` object.
        """
        return cls.signature(method='removeVoucherFromBasket', args=[token, code, basket_id], data_converter=cls.Result)

    @classmethod
    def assign(cls, token, code):
        return cls.signature(method='assignVoucherToUserAccount', args=[token, code], data_converter=cls.Result)


def item_factory(data=None):
    """Item factory to get properly typed basket items."""
    if data is None:
        return Item()
    item_type = data.get('itemType', 'NONE')
    if item_type == 'DOCUMENT':
        return DocumentItem(data)
    elif item_type == 'VOUCHER':
        return GiftCardItem(data)
    else:
        raise ValueError('Basket item type not supported: %s' % item_type)


class CheckoutProperties(Store):
    clear_failed_preauth = BooleanField(target='clearFailedAuthorization')
    clear_preauth = BooleanField(target='clearPreAuthorization')
    use_preauth = BooleanField(target='usePreAuthorization')
    recurring_payment = BooleanField(target='requestedRecurringPayment')
    affiliate_id = Field(target='affiliateID')
    external_transaction_id = Field(target='externalTransactionID')


class Basket(Store, RpcMixin):
    interface = 'WSShopMgmt'

    # txtr to adyen mapping of payment methods;
    # see Enum com.bookpac.server.shop.payment.PaymentMethod and adyen's Integration Manual pp 12+13 for the names
    PAYMENT_METHODS = {"CREDITCARD": ["visa", "mc"], "ELV": ["elv"]}

    # not sure if this is used
    # NOTE (Iurii Kudriavtsev): this is not a complete fields definition
    # class PaymentProperty(Store):
    #     merchant_account = Field(target='merchantAccount')
    #     merchant_ref = Field(target='merchantReference')

    class PaymentForm(Store):
        form = Field(target='com.bookpac.server.shop.payment.paymentform')
        recurring = Field(target='com.bookpac.server.shop.payment.paymentform.recurring')
        worecurring = Field(target='com.bookpac.server.shop.payment.paymentform.worecurring')

    id = Field(target='ID')
    checked_out = BooleanField(target='checkedOut')
    creation_date = DateField(target='creationTime')
    modification_date = DateField(target='modificationTime')
    country = Field(target='country')
    _total = EmbeddedStoreField(target='total', store_class=Price)
    _net_total = EmbeddedStoreField(target='netTotal', store_class=Price)
    _tax_total = EmbeddedStoreField(target='taxTotal', store_class=Price)
    _undiscounted_total = EmbeddedStoreField(target='undiscountedTotal', store_class=Price)
    # payment_props = EmbeddedStoreField(target='paymentProperties', store_class=PaymentProperty)
    payment_forms = EmbeddedStoreField(target='paymentForms', store_class=PaymentForm)
    items = EmbeddedStoreField(target='positions', store_class=item_factory, is_array=True)
    authorized_payment_methods = Field(target='authorizedPaymentMethods')
    vouchers = EmbeddedStoreField(target='voucherApplications', store_class=VoucherItem, is_array=True)

    @property
    def total(self):
        return Money(amount=self._total.amount, currency=self._total.currency)

    @property
    def net_total(self):
        return Money(amount=self._net_total.amount, currency=self._net_total.currency)

    @property
    def tax_total(self):
        return Money(amount=self._tax_total.amount, currency=self._tax_total.currency)

    @property
    def undiscounted_total(self):
        return Money(amount=self._undiscounted_total.amount, currency=self._undiscounted_total.currency)

    @property
    def document_items(self):
        """A property that allows to iterate over the document items.
        Returns generator.
        """
        for item in self.items:
            if isinstance(item, DocumentItem):
                yield item

    @property
    def giftcard_items(self):
        """A property that allows to iterate over the gift card items.
        Returns generator.
        """
        for item in self.items:
            if isinstance(item, GiftCardItem):
                yield item

    @property
    def documents(self):
        """A property that allows to iterate over the documents.
        Returns generator.
        """
        for item in self.document_items:
            yield item.document

    @property
    def giftcards(self):
        """A property that allows to iterate over the gift cards.
        Returns generator.
        """
        for item in self.giftcard_items:
            yield item.giftcard

    @property
    def is_regular(self):
        """Return `True` if at least one document in the basket is regular (i.e. not a preorder)."""
        return any(map(lambda d: not d.is_preorder, self.documents))

    @property
    def is_preorder(self):
        """Return `True` if at least one document in the basket is a preorder."""
        return any(map(lambda d: d.is_preorder, self.documents))

    def is_authorized_for(self, payment_method):
        """Check whether the basket is authorized for the given payment_method.
        """
        if payment_method in self.PAYMENT_METHODS.get("CREDITCARD") and hasattr(self, 'authorized_payment_methods'):
            return "CREDITCARD" in self.authorized_payment_methods
        elif payment_method in self.PAYMENT_METHODS.get("ELV") and hasattr(self, 'authorized_payment_methods'):
            return "ELV" in self.authorized_payment_methods
        else:
            return False

    @classmethod
    def get_by_id(cls, token, basket_id):
        return cls.signature(method='getBasket', args=[token, basket_id])

    @classmethod
    def get_by_token(cls, token):
        return cls.get_by_id(token, None)

    @classmethod
    def get_free(cls, token, marker=None):
        return cls.signature(method='getFreeBasket', args=[token, marker])

    @classmethod
    def get_preview(cls, token, marker=None):
        return cls.signature(method='getNewPreviewBasket', args=[token, marker])

    @classmethod
    def get_validation(cls, token, marker):
        return cls.signature(method='getValidationBasket', args=[token, marker])

    @classmethod
    def checkout(cls, token, basket_id, checkout_props):
        return cls.signature(method='checkoutBasketAsynchronously', data_converter=CheckoutResult,
                             args=[token, basket_id, checkout_props])

    @classmethod
    def create(cls, token, marker=None):
        return cls.signature(method='getNewBasket', args=[token, marker])

    @classmethod
    def clear(cls, token, basket_id):
        return cls.signature(method='removeAllBasketPositions', args=[token, basket_id])


class CheckoutResult(Store):
    basket = EmbeddedStoreField(target='basket', store_class=Basket)
    code = Field(target='resultCode')
    receipt_id = Field(target='receiptIdentifier')
    transaction_id = Field(target='transactionID')
