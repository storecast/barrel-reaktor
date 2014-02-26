from apps.barrel import Store, DateField, EmbeddedStoreField, Field, FloatField, LongIntField
from apps.barrel.rpc import RpcMixin
from apps.reaktor_barrel.document.models import Document
from money import Money


class Notification(Store):
    id = Field(target='ID')
    isbn = LongIntField(target='isbn')
    type = Field(target='type')


class PriceNotification(Notification):
    creation_date = DateField(target='creationTime')
    display_name = Field(target='displayName')
    new_amount = FloatField(target='newPrice:amount')
    new_currency = Field(target='newPrice:currency')
    old_amount = FloatField(target='oldPrice:amount')
    old_currency = Field(target='oldPrice:currency')

    @property
    def previous_price(self):
        return Money(amount=self.old_amount, currency=self.old_currency)

    @property
    def current_price(self):
        return Money(amount=self.new_amount, currency=self.new_currency)

    @property
    def price_down(self):
        return self.type == 'DOCUMENT_LESS_EXPENSIVE'

    @property
    def price_up(self):
        return not self.price_down


def notification_factory(data=None):
    """Notification factory to get properly typed notifications."""
    if data is None:
        return Notification()
    notification_type = data.get('type', 'NONE')
    if notification_type in ('DOCUMENT_LESS_EXPENSIVE', 'DOCUMENT_MORE_EXPENSIVE'):
        return PriceNotification(data)
    else:
        raise ValueError('Notification type not supported: %s' % notification_type)


class ShoppingListItem(Store, RpcMixin):
    interface='WSShopMgmt'

    document = EmbeddedStoreField(target='document', store_class=Document)
    creation_date = DateField(target='creationDate')
    notifications = []

    @classmethod
    def add_to_list(cls):
        raise NotImplementedError()

    @classmethod
    def remove_from_list(cls):
        raise NotImplementedError()


class WishlistItem(ShoppingListItem):
    @classmethod
    def add_to_list(cls, token, doc_id):
        """Adds a document to the user wishlist."""
        return cls.signature(method='addDocumentToCommercialWishList', args=[token, doc_id])

    @classmethod
    def remove_from_list(cls, token, doc_id):
        """Removes a document from the user wishlist."""
        return cls.signature(method='removeDocumentFromCommercialWishList', args=[token, doc_id])


class PreorderlistItem(ShoppingListItem):
    @classmethod
    def add_to_list(cls, token, doc_id):
        """Adding an item to the preorder list is done by buying a document not yet released.
        So this method shouldn't be used.
        """
        raise NotImplementedError("Checkout process is needed to add something to the preorder list.")

    @classmethod
    def remove_from_list(cls, token, doc_id):
        """Preorder logic for removing item from a list."""
        return cls.signature(method='removeDocumentFromPreOrderList', args=[token, doc_id])


class Wishlist(Store, RpcMixin):
    interface='WSShopMgmt'

    items = EmbeddedStoreField(target='entries', store_class=WishlistItem, is_array=True)

    def __len__(self):
        return len(self.items)

    @classmethod
    def get_by_token(cls, token):
        return cls.signature(method='getCommercialWishList', args=[token])


class Preorderlist(Store, RpcMixin):
    interface='WSShopMgmt'

    items = EmbeddedStoreField(target='entries', store_class=PreorderlistItem, is_array=True)
    notifications = EmbeddedStoreField(target='notifications', store_class=notification_factory, is_array=True)

    def __len__(self):
        return len(self.items)

    @classmethod
    def get_by_token(cls, token):
        return cls.signature(method='getPreOrderList', args=[token])

    @property
    def notified_items(self):
        for item in self.items:
            item.notifications = []
            for notif in self.notifications:
                if notif.isbn == item.document.attributes.isbn:
                    item.notifications.append(notif)
            yield item
