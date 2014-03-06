from apps.barrel import Store, Field, FloatField, EmbeddedStoreField
from apps.barrel.rpc import RpcMixin
from apps.reaktor_barrel.document.models import Document


class Stat(Store):
    count = Field(target="count")
    name = Field(target="name")


class DocumentResult(Store):
    """Search result object wrapping search itemsalongside search info
    like pagination information.
    """

    class DocumentItem(Store):
        """Search result item wrapping a document alongside search info like
        item relevance.
        """
        document = EmbeddedStoreField(target="searchResult", store_class=Document)
        relevance = FloatField(target="relevance")

    class Stats(Store):
        """Represents stats about a search result, e.g. how many books for
        this language, how many books available as pdf, ...
        """
        available_as_epub = EmbeddedStoreField(target="available_as_epub", store_class=Stat, is_array=True)
        available_as_pdf = EmbeddedStoreField(target="available_as_pdf", store_class=Stat, is_array=True)
        available_as_pdf_mobile = EmbeddedStoreField(target="available_as_pdf_mobile", store_class=Stat, is_array=True)
        category = EmbeddedStoreField(target="category", store_class=Stat, is_array=True)
        collection_title = EmbeddedStoreField(target="collectionTitle", store_class=Stat, is_array=True)
        language = EmbeddedStoreField(target="language", store_class=Stat, is_array=True)
        source = EmbeddedStoreField(target="source", store_class=Stat, is_array=True)
        tag = EmbeddedStoreField(target="tag", store_class=Stat, is_array=True)
        version_access_type = EmbeddedStoreField(target="currentVersionAccessType", store_class=Stat, is_array=True)
        version_format = EmbeddedStoreField(target="currentVersionFormat", store_class=Stat, is_array=True)

    # Without blocking search, other fields don't make sense anymore so there
    # they are just ignored.
    count = Field(target="numberOfResults")
    has_less = Field(target="hasLess")
    has_more = Field(target="hasMore")
    items = EmbeddedStoreField(target='results', store_class=DocumentItem, is_array=True)
    offset = Field(target="offset")
    stats = EmbeddedStoreField(target='relatedObjects', store_class=Stats)
    total_count = Field(target="totalNumberOfResults")


class SuggestionResult(Store):
    """Suggestions are very lightweight documents (few attributes are present).
    There is no suggestion item as for document search and basket.
    """
    documents = EmbeddedStoreField(target=False, store_class=Document, is_array=True)


class Search(RpcMixin):
    """Interface to various API search endpoints. Beware that this one is not
    a `Store`, which means that when calling its class methods,
    expect different types.
    """
    interface = 'WSSearchDocument'

    @classmethod
    def documents(cls, token, search_string, offset, number_of_results, sort=None, direction=None, include_search_fields=None, sources=None, related=None, options=None):
        """Returns documents for a given string."""
        invert = direction == 'desc'
        if not options:
            options = {'resultType': 'Object'}
        return cls.signature(method='searchDocuments', data_converter=DocumentResult,
            args=[token, search_string, sources, offset, number_of_results, sort, invert, related, include_search_fields, options])

    @classmethod
    def suggestions(cls, token, search_string, number_of_results, sources=None, highlight=None):
        """Returns document suggestions for a given string."""
        args = [token, search_string, sources, number_of_results]
        method = 'getSuggestionObjects'
        if highlight:
            method = 'getSuggestionObjectsWithHighlights'
            args.append(highlight)
        return cls.signature(method=method, data_converter=SuggestionResult, args=args)
