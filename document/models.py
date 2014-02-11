from apps.barrel import Store, Field, BooleanField, DateField, IntField, FloatField, LongIntField, EmbeddedStoreField
from apps.barrel.rpc import RpcMixin
from money import Money


class Document(Store, RpcMixin):
    interface = 'WSDocMgmt'

    class Author(Store):
        first_name = Field(target='firstName')
        last_name = Field(target='lastName')

    class Attributes(Store):
        author = Field(target='author')
        as_epub = BooleanField(target='available_as_epub') # should be deprecated soon
        as_pdf = BooleanField(target='available_as_pdf') # should be deprecated soon
        as_watermark = BooleanField(target='available_as_watermark') # should be deprecated soon
        via_iap = BooleanField(target='available_via_iap') # should be deprecated soon
        with_adobe_drm = BooleanField(target='available_with_adobe_drm') # should be deprecated soon
        hash = Field(target='binary_hash')
        content_provider_name = Field(target='content_provider_name')
        content_provider_id = Field(target='content_provider_specific_id')
        content_source_id = Field(target='content_source_id')
        cover_ratio = FloatField(target='cover_image_aspect_ratio')
        currency = Field(target='currency')
        first_publication = Field(target='date_of_first_publication')
        description = Field(target='description')
        fulfillment_id = Field(target='fulfillment_id')
        fulfillment_type = Field(target='fulfillment_type')
        isbn = LongIntField(target='isbn')
        language = Field(target='language')
        pages = IntField(target='number_of_pages')
        price = FloatField(target='price')
        publication_date = DateField(target='publication_date')
        publisher = Field(target='publisher')
        size = IntField(target='size')
        subtitle = Field(target='subtitle')
        tax_group = Field(target='tax_group')
        title = Field(target='title')
        year = IntField(target='year')
        large_cover_url = Field(target='cover_image_url_large')
        normal_cover_url = Field(target='cover_image_url_normal')
        medium_cover_url = Field(target='cover_image_url_medium')
        undiscounted_price = FloatField(target='undiscounted_price')

    # probably should be moved outside of this class
    class Category(Store):
        id = Field(target='ID')
        name = Field(target='name')
        offset = IntField(target='offset')
        count = IntField(target='count')
        subtree_size = IntField(target='subtreeSize')
        children = Field(target='childrenIDs')
        parent = Field(target='parentID')
        filter = Field(target='filter')

    class License(Store):
        key = Field(target='key')
        user_roles = Field(target='currentUserRoles')

    id = Field(target='documentID')
    master_id = Field(target='documentMasterID')
    name = Field(target='displayName')
    lang_code = Field(target='languageCode')
    format = Field(target='format')
    version = IntField(target='version')
    attributes = EmbeddedStoreField(target='attributes', store_class=Attributes)
    votes = IntField(target='numberOfVotes')
    modification_date = DateField(target='modificationTime')
    creation_date = DateField(target='creationTime')
    owner = Field(target='owner')
    creator = Field(target='creator')
    in_public_list = BooleanField(target='inPublicList')
    version_size = IntField(target='versionSize')
    version_access_type = Field(target='versionAccessType')
    has_thumbnail = BooleanField(target='hasThumbnail')
    licenses = EmbeddedStoreField(target='licenses', store_class=License, is_array=True)
    category_ids = Field(target='contentCategoryIDs')
    categories = EmbeddedStoreField(target='contentCategories', store_class=Category, is_array=True)
    drm_type = Field(target='drmType')
    catalog_state = Field(target='catalogDocumentState')
    authors = EmbeddedStoreField(target='authors', store_class=Author, is_array=True)

    @property
    def price(self):
        return Money(amount=self.attributes.price, currency=self.attributes.currency)

    @property
    def undiscounted_price(self):
        return Money(amount=self.attributes.undiscounted_price, currency=self.attributes.currency)

    @classmethod
    def get_by_id(cls, token, doc_id):
        """Returns `Document` instance for the given id."""
        return cls.signature(method='getDocument', args=[token, doc_id])

    @classmethod
    def get_user_doc_id(cls, token, doc_id):
        """Returns user document id for the catalog document id if any."""
        return cls.signature(method='getUserDocumentID', data_converter=lambda d: d, args=[token, doc_id])
