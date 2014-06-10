from barrel import Store
from barrel.rpc import RpcMixin
from barrel.cache import clear_cache, reduced_call_key
from apps.reaktor_barrel.document.models import Document


def doc_by_id_and_isbn(token, doc_id, stars):
    """Computes cache keys to clear a document. It currently needs one extra
    API call to get the ISBN from the document ID.
    """
    doc = Document.get_by_id(token, doc_id)
    doc_isbn = doc.attributes.isbn
    return (reduced_call_key(Document, Document.get_by_id, [doc_id]),
            reduced_call_key(Document, Document.get_by_isbn, [doc_isbn]), )


class Vote(Store, RpcMixin):
    interface = 'WSDiscussionMgmt'

    @classmethod
    @clear_cache(keygen=doc_by_id_and_isbn)
    def for_doc_id(cls, token, doc_id, stars):
        return cls.signature(method='postVoteForDocument', args=[token, doc_id, {'stars': stars}])
