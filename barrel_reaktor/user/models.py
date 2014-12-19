from barrel import Store, Field, BooleanField, DateField, EmbeddedStoreField
from barrel.rpc import RpcMixin


class User(Store, RpcMixin):
    interface = "WSUserMgmt"

    class Address(Store):
        country = Field(target='com.bookpac.user.settings.shop.country')
        firstname = Field(target='com.bookpac.user.settings.shop.firstname')
        is_valid = Field(target='com.bookpac.user.settings.shop.address.valid')
        lastname = Field(target='com.bookpac.user.settings.shop.lastname')
        location = Field(target='com.bookpac.user.settings.shop.location')
        state = Field(target='com.bookpac.user.settings.shop.state')
        street = Field(target='com.bookpac.user.settings.shop.address1')
        zipcode = Field(target='com.bookpac.user.settings.shop.zipcode')

    id = Field(target='userID')
    address = EmbeddedStoreField(target='settings', store_class=Address)
    company = Field(target='company')
    disabled = BooleanField(target='disabled')
    email = Field(target='EMail')
    image_url = Field(target='userImageUrl')
    level = Field(target='userLevel')
    locale = Field(target='settings:com.bookpac.user.settings.locale')
    name = Field(target='userName')
    nature = Field(target='userNature')
    private_name = Field(target='userPrivateName')
    roles = Field(target='roles')
    verified = BooleanField(target='emailVerified')

    def has_role(self, role):
        return role in self.roles

    @classmethod
    def get_by_token(cls, token):
        return cls.signature(method='getUser', args=[token])


class Auth(Store, RpcMixin):
    interface = "WSAuth"

    date = DateField(target="timestamp")
    result_code = Field(target="resultCode")
    service_name = Field(target="authenticationServiceName")
    token = Field(target="token")
    user = EmbeddedStoreField(target="user", store_class=User)

    @property
    def is_local(self):
        return self.service_name == 'LOCAL'

    @classmethod
    def authenticate_with_credentials(cls, name, hashed_pwd,
                                      nature, sticky=False):
        """Regular auth."""
        return cls.signature(method='authenticate',
                             args=[name, hashed_pwd, nature, sticky])

    @classmethod
    def authenticate_with_external_credentials(cls, token, service_name,
                                               params, sticky=False):
        """Auth using external credentials (e.g. Facebook)."""
        return cls.signature(method='authenticateWithExternalCredentials',
                             args=[token, service_name, params, sticky])

    @classmethod
    def authenticate_as_anonymous(cls, nature):
        return cls.signature(method='authenticateAnonymousUser', args=[nature])

    @classmethod
    def authenticate_anonymous(cls, token, name,
                               hashed_pwd, sticky=False):
        """Regular auth, for an anonymous user who wants to authenticate
        himself while retaining his anonymous data (e.g. his basket).
        """
        return cls.signature(method='authenticate',
                             args=[token, name, hashed_pwd, sticky])

    @classmethod
    def deauthenticate(cls, token):
        return cls.signature(method='deAuthenticate', args=[token])

    @classmethod
    def create_user_from_anonymous(cls, token, name, email, captcha_id,
                                   captcha_value, hashed_pwd1, hashed_pwd2):
        return cls.signature(method='promoteAnonymousUser',
                             args=[token, name, email, captcha_id,
                                   captcha_value, hashed_pwd1, hashed_pwd2])

    @classmethod
    def create_user(cls, name, email, hashed_pwd, settings, nature):
        return cls.signature(method='createUserWithSettings',
                             args=[name, email, hashed_pwd, settings, nature])

    @classmethod
    def request_user_creation(cls, name, email, hashed_pwd, settings, nature):
        return cls.signature(method='requestUserCreationWithSettings',
                             args=[name, email, hashed_pwd, settings, nature])

    @classmethod
    def request_password_reset(cls, name, nature):
        return cls.signature(method='requestPasswordResetForUser',
                             args=[name, nature])

    @classmethod
    def reset_password(cls, token, action, secret, hashed_pwd):
        return cls.signature(interface='WSActionRequestMgmt',
                             method='execute',
                             args=[token, action, secret, {'pw': hashed_pwd}])
