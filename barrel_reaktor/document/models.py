from barrel import Store, Field, BooleanField, DateField, IntField, FloatField, EmbeddedStoreField
from barrel.rpc import RpcMixin
from holon import ReaktorArgumentError
from money import Money


COMMERCIAL_LICENSES = ['commercial-retailer-default', 'commercial-enduser-default', 'cc-publicdomain']


class Document(Store, RpcMixin):
    interface = 'WSDocMgmt'

    class Author(Store):
        first_name = Field(target='firstName')
        last_name = Field(target='lastName')

    class Attributes(Store):
        as_epub = BooleanField(target='available_as_epub') # should be deprecated soon
        as_pdf = BooleanField(target='available_as_pdf') # should be deprecated soon
        as_watermark = BooleanField(target='available_as_watermark') # should be deprecated soon
        audience = Field(target='audience')
        author = Field(target='author', default=u'')
        author_bio = Field(target='author_biography', default='')
        catalog_id = Field(target='catalog_document_id')
        content_provider_id = Field(target='content_provider_specific_id')
        content_provider_name = Field(target='content_provider_name')
        content_source_id = Field(target='content_source_id')
        cover_ratio = FloatField(target='cover_image_aspect_ratio')
        currency = Field(target='currency')
        description = Field(target='description')
        editors_comment = Field(target='editors_comment')
        extract = Field(target='extract')
        first_publication = Field(target='date_of_first_publication')
        fulfillment_id = Field(target='fulfillment_id')
        fulfillment_type = Field(target='fulfillment_type')
        hash = Field(target='binary_hash')
        _isbn = Field(target='isbn')
        imprint = Field(target='imprint', default='')
        language = Field(target='language')
        large_cover_url = Field(target='cover_image_url_large')
        medium_cover_url = Field(target='cover_image_url_medium')
        normal_cover_url = Field(target='cover_image_url_normal')
        pages = IntField(target='number_of_pages')
        price = FloatField(target='price')
        publication_date = DateField(target='publication_date')
        publication_status = DateField(target='publication_status')
        publisher = Field(target='publisher')
        size = IntField(target='size')
        subtitle = Field(target='subtitle')
        tax_group = Field(target='tax_group')
        title = Field(target='title', default=u'')
        undiscounted_price = FloatField(target='undiscounted_price')
        via_iap = BooleanField(target='available_via_iap') # should be deprecated soon
        with_adobe_drm = BooleanField(target='available_with_adobe_drm') # should be deprecated soon
        year = IntField(target='year')

        @property
        def isbn(self):
            return self._isbn.strip()

    class License(Store):
        key = Field(target='key')
        user_roles = Field(target='currentUserRoles')

    class Preview(Store):
        format = Field(target='format')

    id = Field(target='documentID')
    attributes = EmbeddedStoreField(target='attributes', store_class=Attributes)
    authors = EmbeddedStoreField(target='authors', store_class=Author, is_array=True)
    catalog_state = Field(target='catalogDocumentState')
    _categories = EmbeddedStoreField(target='contentCategories', store_class='barrel_reaktor.category.models.Category', is_array=True)
    category_ids = Field(target='contentCategoryIDs')
    creation_date = DateField(target='creationTime')
    creator = Field(target='creator')
    drm_type = Field(target='drmType')
    file_name = Field(target='fileName', default='')
    format = Field(target='format', default='')
    has_thumbnail = BooleanField(target='hasThumbnail')
    in_public_list = BooleanField(target='inPublicList')
    lang_code = Field(target='languageCode')
    licenses = EmbeddedStoreField(target='licenses', store_class=License, is_array=True)
    master_id = Field(target='documentMasterID')
    modification_date = DateField(target='modificationTime')
    name = Field(target='displayName')
    owner = Field(target='owner')
    previews = EmbeddedStoreField(target='documentPreviews', store_class=Preview, is_array=True)
    type = Field(target='type')
    user_state = Field(target='userDocumentState', default='?')
    user_tags = Field(target='userTags', default=[])
    version = IntField(target='version')
    version_access_type = Field(target='versionAccessType')
    version_size = IntField(target='versionSize')
    votes = IntField(target='numberOfVotes')
    cumulative_votes = IntField(target='cumulativeVotes:stars', default=0)
    personal_votes = IntField(target='personalVotes:stars', default=0)

    @property
    def price(self):
        return Money(amount=self.attributes.price, currency=self.attributes.currency)

    @property
    def undiscounted_price(self):
        return Money(amount=self.attributes.undiscounted_price, currency=self.attributes.currency)

    @property
    def is_preorder(self):
        return not self.is_user and self.catalog_state == 'PRE_RELEASE'

    @property
    def is_fulfilled(self):
        return self.user_state == 'FULFILLED' or self.is_upload

    @property
    def is_user(self):
        return self.type == 'USER'

    @property
    def is_upload(self):
        return self.user_state == 'UPLOADED_BY_USER'

    @property
    def is_commercial(self):
        return any([l.key in COMMERCIAL_LICENSES for l in self.licenses])

    @property
    def has_drm(self):
        return self.version_access_type == "ADEPT_DRM"

    @property
    def categories(self):
        """Builds a list of categories in tree order, from oldest ancestor to the leaf.
        It relies on both `category_ids` and `_categories` attributes.
        Note that according to reaktor, when viewing a document from a catalog that is not
        associated to the token nature, the information is not available.
        """
        if hasattr(self, '_category_trail'):
            return self._category_trail
        trail = []
        if self.category_ids:
            cats = dict([(c.id, c) for c in self._categories])
            current = cats.pop(self.category_ids[0], None)
            trail = [current]
            while current.parent_id:
                current = cats.pop(current.parent_id)
                trail.insert(0, current)
        self._category_trail = trail
        return trail

    @classmethod
    def get_by_id(cls, token, doc_id):
        """Returns `Document` instance for the given id."""
        document = cls.signature(method='getDocument', args=[token, doc_id])
        # reaktor call may return `None`
        # raise a proper exception in this case
        if not document:
            raise ReaktorArgumentError
        return document

    @classmethod
    def get_by_ids(cls, token, doc_ids):
        """Returns `Document` instance for the given ids."""
        return cls.signature(method='getDocuments', args=[token, doc_ids])

    @classmethod
    def get_user_doc_id(cls, token, doc_id):
        """Returns user document id for the catalog document id if any."""
        return cls.signature(method='getUserDocumentID', data_converter=lambda d: d, args=[token, doc_id])

    @classmethod
    def get_doc_path(cls, token, doc_id, is_user=False):
        """Returns the path to unzipped epub user document or catalog preview."""
        method = 'unzipEpubUserDocument' if is_user else 'unzipEpubPreview'
        return cls.signature(method=method, data_converter=lambda d: d, args=[token, doc_id])

    @classmethod
    def get_by_isbn(cls, token, isbn):
        """Returns a document by isbn, using search API endpoint since fetching doc by isbn requires extra rights."""
        def converter(data):
            if 'results' in data:
                return Document(data['results'][0]['searchResult'])
            # reaktor call may return `None`
            # raise a proper exception in this case
            else:
                raise ReaktorArgumentError
        args = [token, 'isbn:%s' % isbn, None, 0, 1, None, False, None, None, {'resultType': 'Object'}]
        return cls.signature(
            interface="WSSearchDocument", method='searchDocuments', data_converter=converter, args=args)

    @classmethod
    def get_related_by_id(cls, token, doc_id, offset=0, number_of_results=5):
        """Returns a list of `Documents` that are related to the given id."""
        return cls.signature(method='getDocumentsRelatedToDocument', args=[token, doc_id, offset, number_of_results])

    @classmethod
    def change_attributes(cls, token, doc_ids, attributes):
        return cls.signature(method='changeDocumentAttributes', args=[token, doc_ids, attributes])
