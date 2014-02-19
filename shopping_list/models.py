from apps.barrel import Store, DateField, EmbeddedStoreField
from apps.barrel.rpc import RpcMixin
from apps.reaktor_barrel.document.models import Document


class ShoppingListItem(Store, RpcMixin):
    interface='WSShopMgmt'

    document = EmbeddedStoreField(target='document', store_class=Document)
    creation_date = DateField(target='creationDate')

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

    @classmethod
    def get_by_token(cls, token):
        return cls.signature(method='getCommercialWishList', args=[token])


class Preorderlist(Store, RpcMixin):
    interface='WSShopMgmt'

    items = EmbeddedStoreField(target='entries', store_class=PreorderlistItem, is_array=True)

    @classmethod
    def get_by_token(cls, token):
        return cls.signature(method='getPreOrderList', args=[token])
