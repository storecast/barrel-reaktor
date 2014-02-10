from apps.barrel import Store, DateField, EmbeddedStoreField
from apps.barrel.rpc import RpcMixin, rpc_call
from apps.reaktor_barrel.document.models import Document


class ShoppingListItem(Store, RpcMixin):
    interface='WSShopMgmt'

    document = EmbeddedStoreField(target='document', store_class=Document)
    creation_date = DateField(target='creationDate')

    @classmethod
    def add_to_list(cls):
        pass

    @classmethod
    def remove_from_list(cls):
        pass


class WishlistItem(ShoppingListItem):
    @classmethod
    @rpc_call
    def add_to_list(cls, token, doc_id):
        """Adds a document to the user wishlist."""
        return cls.signature(method='addDocumentToCommercialWishList', args=[token, doc_id])

    @classmethod
    @rpc_call
    def remove_from_list(cls, token, doc_id):
        """Removes a document from the user wishlist."""
        return cls.signature(method='removeDocumentFromCommercialWishList', args=[token, doc_id])


class PreorderlistItem(Store):
    @classmethod
    @rpc_call
    def add_to_list(cls, token, doc_id):
        """Preorder logic for adding item to a list. Note that the reaktor handles this one
        based on the status of document. It is provided here for the sake of consistency.
        """
        return cls.signature(method='addDocumentToCommercialWishList', args=[token, doc_id])

    @classmethod
    @rpc_call
    def remove_from_list(cls, token, doc_id):
        """Preorder logic for removing item from a list."""
        return cls.signature(method='removeDocumentFromPreOrderList', args=[token, doc_id])


class Wishlist(Store, RpcMixin):
    interface='WSShopMgmt'

    items = EmbeddedStoreField(target='entries', store_class=WishlistItem, is_array=True)

    @classmethod
    @rpc_call
    def get_by_token(cls, token):
        return cls.signature(method='getCommercialWishList', args=[token])


class Preorderlist(Store, RpcMixin):
    interface='WSShopMgmt'

    items = EmbeddedStoreField(target='entries', store_class=PreorderlistItem, is_array=True)

    @classmethod
    @rpc_call
    def get_by_token(cls, token):
        return cls.signature(method='getPreOrderList', args=[token])
