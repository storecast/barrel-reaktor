# -*- coding: utf-8 -*-
import re
from collections import defaultdict
from babel import Locale
from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.localflavor.ca.forms import CAProvinceField, CAProvinceSelect
from django.contrib.localflavor.ca.ca_provinces import PROVINCE_CHOICES as CA_PROVINCE_CHOICES
from django.contrib.localflavor.de.forms import DEZipCodeField
from django.contrib.localflavor.us.forms import USStateField, USStateSelect, USZipCodeField
from django.contrib.localflavor.us.us_states import STATE_CHOICES as US_STATE_CHOICES
from django.http import QueryDict
from django.utils.translation import ugettext, ugettext_lazy as _

from apps.reaktor_auth.forms import CustomErrorList
from apps.reaktor.forms import ReaktorForm
from apps.reaktor.mapper import WST_MAP_EMPTY_VALUE_VARIANTS
from apps.reaktor_users import get_current_reaktor_user
from apps.reaktor_users.mapper import SETTINGS_FROM_API, SETTINGS_TO_API
from apps.reaktor_users.models import ReaktorUser
from libs.own.holon import ReaktorApiError

from .models import VoucherItem, Basket


##############################################################################
# BillingAddressForm start
##############################################################################


class BillingAddressForm(ReaktorForm):
    """
    Form for the billing address used in the checkout plugin.
    """
    first_name = forms.CharField(required=True,
        label = _('First Name'),
        widget=forms.TextInput(attrs={'placeholder': _('First Name')}))
    last_name = forms.CharField(required=True,
        label = _('Last Name'),
        widget=forms.TextInput(attrs={'placeholder': _('Last Name')}))
    address = forms.CharField(required=True,
        label = _('Address'),
        widget=forms.TextInput(attrs={'placeholder': _('Address')}))
    address_continued = forms.CharField(required=False,
        label =_('Address continued'),
        widget=forms.TextInput(attrs={'placeholder': _('Address continued')}))
    zipcode = forms.CharField(required=True,
        label = _('Zip code'),
        widget=forms.TextInput(attrs={'placeholder': _('Zip code')}))
    city = forms.CharField(required=True,
        label = _('City'),
        widget=forms.TextInput(attrs={'placeholder': _('City')}))
    # hidden fields
    billing_address_form = forms.BooleanField(required=True, widget=forms.HiddenInput)

    disabled_for_facebook_users = False
    disabled_fields_for_facebook_users = True
    reaktor_changed = False

    def _get_territories(self, territories):
        """Filter Babel territories to exclude non ISO 3166-2 territories.

        :param territores: Babel territories
        :return: filtered territories
        """
        result = {
            k: v for k, v in territories.items() if re.match(r'[a-zA-Z]{2}', k)
        }
        return result

    def _get_country_choices(self, country_code):
        """
        Get the available country choices.

        :param country_code: the shop's home country code
        :return: available country choices
        """
        # get the current locale
        if self.request.LANGUAGE_CODE:
            locale = Locale.parse(self.request.LANGUAGE_CODE, sep="-")
        else:
            locale = Locale.parse('en-us', sep="-")

        if country_code != 'WO': # international store
            return [(country_code,
                locale.territories.get(country_code, country_code))]

        # get choices for all countries
        territories = self._get_territories(locale.territories)
        codes = territories.keys()
        # compile list of choices
        choices = [(code, territories.get(code, code)) for code in codes]
        # sort the list of countries alphabetically
        choices.sort(key=lambda x:x[1])
        return choices

    def _init_country(self):
        """Initialise the country field."""
        country_code = self.request.nature.home_country.upper()
        choices = self._get_country_choices(country_code)
        self.fields['country'] = forms.ChoiceField(required=True,
            choices=choices,
            label=_('Country'),
            initial=country_code)

    def _prepend_state_select_hint(self, label):
        """Prepend the state select with a 'please select' hint."""
        if not 'state' in self.fields:
            return

        choices = self.fields['state'].widget.choices
        if choices[0][0] != '':
            choices.insert(0, ('', '--- ' + label))

    def __init__(self, *args, **kwargs):
        if isinstance(args[0], ReaktorUser):
            initial = self.get_initial_data(args[0])
            kwargs.update({'initial': initial})
            args = args[1:]
        elif isinstance(args[0], QueryDict):
            initial = args[0]
        else:
            initial = None

        self.request = kwargs.pop('request', None)
        kwargs.update({'error_class': CustomErrorList})

        super(BillingAddressForm, self).__init__(*args, **kwargs)
        self._init_country()

    def get_initial_data(self, user):
        """Get initial form data for given user.

        :param user: ReaktorUser to get form data for
        :return: form-compatible user (settings) data
        """
        return self._reaktor_settings_to_form(user.settings)

    def _reaktor_settings_to_form(self, settings):
        """Convert the Reaktor user settings to the format used in the form.

        :param settings: ReaktorUser settings
        :return: form-compatible user (settings) data
        """
        data = { 'billing_address_form': True, }
        for reaktor_name, form_name in SETTINGS_FROM_API.items():
            data[form_name] = settings.get(reaktor_name, '')

        # handle state differently to amend https://jira.txtr.com/browse/BACKEND-3835
        if data['state'] in WST_MAP_EMPTY_VALUE_VARIANTS:
            data['state'] = ''

        return data

    def _reaktor_errors(self, result):
        """Check if the Reaktor returned errors.

        Registers form errors and adds a Django message if required.

        :param result: Reaktor result of change settings call
        :return: if there had been errors detected by the Reaktor
        """
        # field possibly doesn't exist if validation succeeded
        is_valid = result['settings'].get(SETTINGS_TO_API['valid'], '')
        is_valid = is_valid == 'true'

        if not is_valid:
            for error in result['validationErrors']:
                # barf if the field is yet unknown to Skins
                field = SETTINGS_FROM_API[error['userSetting']]
                # reasons seen so far: 'Invalid Setting'
                # SKINSTXTRCOM-3576 : display nicer message.
                # self.register_errors(field, [_(error['reason'])])
                self.register_errors(field, [ugettext("We cannot validate this entry. Please enter a valid address.")])
            messages.add_message(self.request, messages.ERROR,
                ugettext('Your billing address has errors, please correct them.'))
            return True

        return False

    def _reaktor_changed_settings(self, result, fields=None):
        """Check if the form-supplied address data is equal to the Reaktor user settings.

        :param result: Reaktor result of change settings call
        :param fields: fields to check the partial equivalence
        :return: if user settings are equal to the form-supplied data.
        """
        is_equal = True
        address_form = self.cleaned_data
        address_reaktor = self._reaktor_settings_to_form(result['settings'])
        address_reaktor.pop('billing_address_form')
        # need a copy of the request's QueryDict to be able to modify
        self.data = self.data.copy()

        # iterate over keys(), otherwise get RuntimeError for changed dict
        for field in address_form.keys():
            try:
                if (address_form[field] != address_reaktor[field] and not fields) or (address_form[field] != address_reaktor[field] and fields and field in fields):
                    # set data of bound field (!)
                    self.data[field] = address_reaktor[field]
                    self.fields[field].widget.attrs['data-reaktor'] = 'changed'
                    is_equal = False
                    self.reaktor_changed = True
            # just in case some form fields are not in Reaktor settings
            except KeyError:
                pass

        return is_equal

    def execute(self, fields=None):
        """
        This execute method also takes a keyword argument 'fields', which in
        case it is a list of form field names leads to partial execution of the
        form in the scope of the fields.
        This is useful for devices with small screens, where this long form is
        divided over two pages.
        Note that this method returns True if the form is valid for the given
        fields, each taken for itself, even if there are non-field-errors or
        errors in other fields.

        :param fields: fields to partially validate
        :return: if execution was successful
        """
        is_valid = self.is_valid()
        if not is_valid and fields: # check for fields, maybe partially valid
            is_valid = (len(set(self.errors.keys()).intersection(set(fields)))==0)
            if is_valid and not hasattr(self, 'cleaned_data'):
                self.cleaned_data = {}
                super(BillingAddressForm, self).clean()
                for f in fields:
                    if not self.cleaned_data.has_key(f):
                        self.cleaned_data[f] = self.data.get(f)

        if not is_valid:
            return False

        # now handle Reaktor
        result = ReaktorUser.mapper.change_settings_from_form(self, fields)
        if self._reaktor_errors(result) or not self._reaktor_changed_settings(result, fields):
            return False
        else:
            self.success_message = ugettext('Your billing address has been changed successfully.')
            return True

    def is_empty(self):
        """Checks if the address is 'empty'."""
        settings_keys = get_current_reaktor_user().settings.keys()
        prefix = 'com.bookpac.user.settings.shop.'
        fields = ['firstname', 'lastname', 'address1', 'address2', 'location', 'state', 'country']
        keys = [prefix + f for f in fields]
        return len(set(keys) & set(settings_keys)) == 0


class BillingAddressFormUS(BillingAddressForm):
    state = USStateField(required=True, widget=USStateSelect)
    zipcode = USZipCodeField(required=True,
        label=_('Zip code'),
        widget=forms.TextInput(attrs={'placeholder': _('Zip code')}))

    def __init__(self, *args, **kwargs):
        super(BillingAddressFormUS, self).__init__(*args, **kwargs)
        self._prepend_state_select_hint(ugettext('Select your state'))


class BillingAddressFormCA(BillingAddressForm):
    state = CAProvinceField(required=True,
        widget=CAProvinceSelect, label=_('Province'))


    def __init__(self, *args, **kwargs):
        super(BillingAddressFormCA, self).__init__(*args, **kwargs)
        self._prepend_state_select_hint(ugettext('Select your province'))


class BillingAddressFormDE(BillingAddressForm):
    zipcode = DEZipCodeField(required=True,
        label=_('Zip code'),
        widget=forms.TextInput(attrs={'placeholder': _('Zip code')}))


def get_billing_address_form(data, request):
    """Returns the country-specific (or generic) billing address form.

    :param data: data to supply to the form, request.POST or Reaktor user (our initial)
    :param request: request object
    :return: a BillingAddressForm, possibly country specific
    """
    home_country = request.nature.home_country.upper()
    try:
        cls = eval('BillingAddressForm' + home_country)
    except NameError: # country doesn't have a specific form class
        cls = BillingAddressForm

    return cls(data, request=request)


##############################################################################
# BillingAddressForm end
##############################################################################


class PaymentSettingsForm(ReaktorForm):
    """
    Form for changing payment settings.
    """
    recurring_payment = forms.BooleanField(label=_('Save data for future payments.'), initial=True, widget=forms.CheckboxInput)
    payment_settings_form = forms.BooleanField(required=True, widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        kwargs.update({'initial': self.get_initial_data()})
        kwargs.pop('initial_data', None) # clean up
        super(PaymentSettingsForm, self).__init__(*args, **kwargs)

    def execute(self):
        return self.is_valid()

    def get_initial_data(self):
        return {'recurring_payment':True,
                'payment_settings_form':True}


class PayNowForm(ReaktorForm):
    basket_id = forms.CharField(required=True, widget=forms.HiddenInput)
    pay_now_form = forms.BooleanField(required=True, widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        kwargs.update({'initial': self.get_initial_data()})
        kwargs.pop('initial_data', None) # clean up
        super(PayNowForm, self).__init__(*args, **kwargs)

    def execute(self):
        return self.is_valid()

    def get_initial_data(self):
        return {'pay_now_form': True}


class ClearBasketForm(ReaktorForm):
    basket_id = forms.CharField(required=True, widget=forms.HiddenInput)
    clear_basket_form = forms.BooleanField(required=True, widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        kwargs.update({'initial': self.get_initial_data()})
        kwargs.pop('initial_data', None) # clean up
        super(ClearBasketForm, self).__init__(*args, **kwargs)

    def execute(self):
        return self.is_valid()

    def get_initial_data(self):
        return {'clear_basket_form': True}


class VoucherForm(ReaktorForm):
    basket_id = forms.CharField(required=True, widget=forms.HiddenInput)
    item_id = forms.CharField(label = _('Voucher code'), required=True) #voucher_code
    item_action = forms.CharField(required=True) # add or remove
    item_type = forms.CharField(required=True) #voucher, just a marker

    def __init__(self, *args, **kwargs):
        kwargs.update({'initial': self.get_initial_data(),
                       'error_class':CustomErrorList})
        super(VoucherForm, self).__init__(*args, **kwargs)
        self.fields['item_id'].widget.attrs['placeholder'] = _("Enter voucher code")

    def execute(self, token):
        form_is_valid = self.is_valid()
        result = False
        if form_is_valid: # execution only if form is valid
            if self.cleaned_data['item_action'] == 'remove':
                result = VoucherItem.remove(token, self.cleaned_data['item_id'], self.cleaned_data['basket_id'])
            if self.cleaned_data['item_action'] == 'add':
                result = VoucherItem.apply(token, self.cleaned_data['item_id'], self.cleaned_data['basket_id'])
            self.set_errors_from_result_code(result.code)
        return result.code

    def set_errors_from_result_code(self, error_code):
        #NOTE: `True` is the marker for success.
        codes = {
            'ILLEGAL_VOUCHER_CODE': _('This voucher is invalid. Please verify that you typed in the code correctly.'),
            'ONLY_ONE_VOUCHER_APPLICABLE': _('Only one voucher can be added to your basket. Remove the voucher first if you want to use a different one.'),
            'VOUCHER_ALREADY_ASSIGNED': _('A voucher with this code has already been added to your basket.'),
            'VOUCHER_ALREADY_REDEEMED': _('This voucher has already been used.'),
            'VOUCHER_BELONGS_TO_DIFFERENT_USER': _('This voucher is invalid. It belongs to another user already.'),
            'VOUCHER_APPLIED': True,
            'VOUCHER_REMOVED': True,
            'VOUCHER_EXPIRED': _('This voucher is expired.')
        }
        if not codes.get(error_code, None) is True:
            error_message = codes[error_code] if error_code in codes else _('An unknown error has occurred.')
            self._errors['item_id'] = self.error_class([error_message])

    def get_initial_data(self, **kwargs):
        return { 'voucher_form':True }

    def clean_basket_id(self):
        return self.data.get('basket_id')

    def clean_item_id(self):
        #TODO: check if voucher is valid!
        return self.data.get('item_id')

    def clean_item_action(self):
        return self.data.get('item_action')

    def clean_item_type(self):
        return self.data.get('item_type')


class CustomErrorForm(forms.Form):
    """Form that uses `CustomErrorList` to print the errors.
    Also sets the `error` class on fields input.
    """
    def __init__(self, *args, **kwargs):
        kwargs.update({'error_class': CustomErrorList})
        super(CustomErrorForm, self).__init__(*args, **kwargs)

    def is_valid(self):
        # overriding this method to style the fields properly.
        valid = super(CustomErrorForm, self).is_valid()
        for field in self:
            if field.errors:
                field.field.widget.attrs.update({'class': field.css_classes('error')})
        return valid


class CardCodeForm(CustomErrorForm):
    """Base form class for applying and removing Ebook voucher to / from basket."""

    _response_codes = {
        'VOUCHER_APPLIED': True,
        'VOUCHER_REMOVED': True,
        'ILLEGAL_VOUCHER_CODE': _("Your code should have at least 8 characters and may contain both numbers and letters."),
        'VOUCHER_BELONGS_TO_DIFFERENT_USER': _('This voucher is invalid. It belongs to another user already.'),
        'VOUCHER_ALREADY_REDEEMED': _("This code has already been activated. Please recheck your entry and try again."),
    }
    setting_name = 'preview_voucher_code'

    basket_id = forms.CharField(widget=forms.HiddenInput)

    def __init__(self, request, *args, **kwargs):
        super(CardCodeForm, self).__init__(*args, **kwargs)
        self.request = request
        self.response_codes = defaultdict(lambda: _("Your code can't be activated. Please contact us to resolve this issue."), self._response_codes)

    def get_basket(self):
        return getattr(self, '_basket', None)


class CardCodeAddForm(CardCodeForm):
    """Form that handles applying of Ebook voucher card to basket."""

    voucher_code = forms.CharField(
        label=_("eBook code"),
        widget=forms.TextInput(attrs={'placeholder': _("e.g. 12345abc")}),
        min_length=8,
        max_length=8,
        error_messages={
            'required': _("Your code should have at least 8 characters."),
            'min_length': _("Your code should have at least 8 characters."),
            'max_length': _("Your code should have 8 characters."),
        }
    )

    def clean(self):
        cleaned_data = super(CardCodeAddForm, self).clean()
        basket_id = cleaned_data.get('basket_id')
        voucher_code = cleaned_data.get('voucher_code')
        if basket_id and voucher_code:
            token = self.request.reaktor_user.token
            try:
                result = VoucherItem.apply(token, voucher_code, basket_id)
            except ReaktorApiError:
                msg = self.response_codes.default_factory()
            else:
                msg = self.response_codes[result.code]
            # reaktor returned an error result code
            if msg is not True:
                self._errors['voucher_code'] = self.error_class([msg])
                del cleaned_data['voucher_code']
            # reaktor returned basket in result in case of no errors
            else:
                self._basket = result.basket
                # save the voucher code either to user settings
                if self.request.reaktor_user.is_authenticated():
                    self.request.reaktor_user.settings['skins.' + self.setting_name] = voucher_code
                    ReaktorUser.mapper.change_settings_from_user_obj(token, self.request.reaktor_user)
                # or to session
                elif self.setting_name not in self.request.session:
                    self.request.session[self.setting_name] = voucher_code
        return cleaned_data


class CardCodeRemoveForm(CardCodeForm):
    """Form that handles removing of Ebook voucher card from basket."""

    voucher_code = forms.CharField(widget=forms.HiddenInput)

    def clean(self):
        cleaned_data = super(CardCodeRemoveForm, self).clean()
        basket_id = cleaned_data.get('basket_id')
        voucher_code = cleaned_data.get('voucher_code')
        if basket_id:
            token = self.request.reaktor_user.token
            try:
                result = VoucherItem.remove(token, voucher_code, basket_id)
            except ReaktorApiError:
                msg = self.response_codes.default_factory()
            else:
                msg = self.response_codes[result.code]
            # reaktor returned an error result code
            if msg is not True:
                raise forms.ValidationError(msg)
            # remove the document from the basket in case of no errors
            for item in result.basket.document_items:
                item.remove_from_basket(self.request.reaktor_user.token, result.basket.id, item.document.id)
            # since `WSDocMgmt.changeDocumentBasketPosition` returns void,
            # we need to do a separate call to get the updated basket
            self._basket = Basket.get_by_id(token, result.basket.id)
            # remove the voucher code either from user settings
            if self.request.reaktor_user.is_authenticated():
                self.request.reaktor_user.settings['skins.' + self.setting_name] = ''
                ReaktorUser.mapper.change_settings_from_user_obj(token, self.request.reaktor_user)
            # or from session
            else:
                del self.request.session[self.setting_name]
        return cleaned_data


class CardCodeRedeemForm(CardCodeForm):
    """Form that handles redeeming of Ebook voucher card."""

    _response_codes = {
        'SUCCESS': True,
        'FAILURE_FULFILLMENT_INDIVIDUAL_POSITION': _("The checkout failed because one basket position could not be fulfilled."),
        'FAILURE_INTERNAL_ERROR': _("The checkout failed with an internal error."),
        'FAILURE_PAYMENT_AUTHORIZATION_TIMED_OUT': _("The checkout failed because the payment provider could not be reached."),
        'FAILURE_PAYMENT_INFORMATION_INVALID': _("The checkout failed because the payment information are insufficient or invalid."),
        'FAILURE_PAYMENT_NOT_POSSIBLE': _("The checkout failed, because the payment is not possible."),
    }

    def clean(self):
        cleaned_data = super(CardCodeRedeemForm, self).clean()
        basket_id = cleaned_data.get('basket_id')
        if basket_id:
            token = self.request.reaktor_user.token
            if 'referral' in self.request.session:
                checkout_props = {'externalTransactionID': self.request.session['referral']}
            else:
                checkout_props = {}
            try:
                result = Basket.checkout(token, basket_id, None, checkout_props)
            except ReaktorApiError:
                msg = self.response_codes.default_factory()
            else:
                msg = self.response_codes[result.code]
            # reaktor returned an error result code
            if msg is not True:
                raise forms.ValidationError(msg)
            # reaktor returned basket in result in case of no errors
            self._basket = result.basket
        return cleaned_data
