from cms.models import Page
from django.utils.translation import ugettext_lazy as _

from apps.compact_url import reverse
from apps.prototypes.decorators import atom
from apps.site_conf.models import SiteConf
from .forms import PayNowForm


@atom('atoms/checkout/basket_empty.html')
def basket_empty(reaktor_user, store_path, wishlist_path):
    """Atom to render if basket is empty in the checkout plugin."""
    if reaktor_user.is_authenticated():
        is_authenticated = True
    else:
        is_authenticated = False

    wishlist_path = reverse('user-wishlist')

    return {
        'is_authenticated': is_authenticated,
        'wishlist_path': wishlist_path,
        'store_path': store_path,
        'wishlist_path': wishlist_path
    }


@atom('atoms/checkout/basket_list.html')
def basket_list(request, basket, instance, voucher_form, store_path, csrf_token, already_purchased_docs):
    """Atom to render the basket section (1) in the checkout plugin."""
    site_conf = SiteConf.on_site.get()
    if site_conf.add_to_basket:
        remove_url = reverse('basket-update-item')
    else:
        remove_url = reverse('basket')

    return {
        'request': request,
        'basket': basket,
        'remove_url': remove_url,
        'site_conf': site_conf,
        'instance': instance,
        'voucher_form': voucher_form,
        'store_path': store_path,
        'csrf_token': csrf_token,
        'already_purchased_docs': already_purchased_docs
    }


@atom('atoms/checkout/voucher_form.html')
def voucher_form(instance, basket, form, csrf_token):
    """Atom to render the voucher form in the checkout plugin."""
    return {
        'instance': instance,
        'basket': basket,
        'form': form,
        'csrf_token': csrf_token,
    }


@atom('atoms/checkout/user_form.html')
def user_form(request, reaktor_user, login_form, signup_form, signup_config, checkout_plugin, facebook):
    """Atom to render the user login/signup section (2) in the checkout plugin."""
    return {
        'request': request,
        'reaktor_user': reaktor_user,
        'login_form': login_form,
        'signup_form': signup_form,
        'signup_config': signup_config,
        'checkout_plugin': checkout_plugin,
        'facebook': facebook,
    }


@atom('atoms/checkout/address_form.html')
def address_form(reaktor_user, has_billing_address, form, disabled_fields, csrf_token, site_conf):
    """Atom to render the billing address section (3) in the checkout plugin."""
    settings = reaktor_user.settings
    prefix = 'com.bookpac.user.settings.shop.'
    address = {
        'firstname': settings.get(prefix + 'firstname', None),
        'lastname': settings.get(prefix + 'lastname', None),
        'address': settings.get(prefix + 'address1', None),
        'zipcode': settings.get(prefix + 'zipcode', None),
        'location': settings.get(prefix + 'location', None),
        'country': settings.get(prefix + 'country', None),
    }
    address2 = settings.get(prefix + 'address2', None)
    if address2 and address2.lower() != "null":
        address['address'] = u', '.join((address['address'], address2))
    state = settings.get(prefix + 'state', None)
    if state and state.lower() != "null":
        address['location'] = u', '.join((address['location'], state))

    address_empty = address.get('firstname') is None and address.get('lastname') is None and  address.get('address') is None and address.get('zipcode') is None and address.get('location') is None and address.get('country') is None

    return {
        'reaktor_user': reaktor_user,
        'address': address,
        'has_billing_address': has_billing_address,
        'form': form,
        'disabled_fields': disabled_fields,
        'csrf_token': csrf_token,
        'site_conf': site_conf,
        'address_empty': address_empty
    }


@atom('atoms/checkout/payment_form.html')
def payment_form(request, basket, has_billing_address, has_payment_data, payment_url, instance):
    """Atom to render the payment section (4) in the checkout plugin."""
    return {
        'has_billing_address': has_billing_address,
        'has_payment_data': has_payment_data,
        'payment_url': payment_url,
        'basket': basket,
        'instance': instance
    }


@atom('atoms/checkout/complete.html')
def complete(reaktor_user, basket, has_billing_address, has_payment_data, payment_url, csrf_token):
    """Atom to render the complete checkout section in the checkout plugin."""
    # check if we can enable the complete purchase button
    can_checkout = reaktor_user.is_authenticated() and (
            (has_billing_address and basket.total.amount) # normal checkout
         or (not basket.total.amount and not len(basket.vouchers)) # free book checkout
         or (has_billing_address and not basket.total.amount and len(basket.vouchers)) # normal checkout with vouchers making it a free checkout
    )


    if not basket.total.amount:
        label = _("Continue to Download")
        button_id = "free-pay-now"
    else:
        label = _("Complete Purchase")
        button_id = "pay-now"
        # If this becomes a more involved logic, it should be abstracted
        # by the model.
        if all(map(lambda d: d.is_preorder, basket.documents)):
            label = _('Complete Pre-order')

    try:
        terms_path = reverse('pages-details-by-slug', args=['terms'])
    except Page.DoesNotExist:
        terms_path = None

    return {
        'can_checkout': can_checkout,
        'has_payment_data': has_payment_data,
        'pay_now_form': PayNowForm(),
        'payment_url': payment_url,
        'basket': basket,
        'label': label,
        'button_id': button_id,
        'csrf_token': csrf_token,
        'terms_path': terms_path,
    }


@atom('atoms/checkout/your_purchase.html')
def your_purchase(request, basket, store_path, conversion_code, purchased_items):
    """Atom to render the your purchase section (after checkout complete) in the checkout plugin."""
    return {
        'request': request,
        'basket': basket,
        'library_path': reverse('user-library'),
        'library_page': Page.objects.on_site().published().get(reverse_id='my', publisher_is_draft=False),
        'store_path': store_path,
        'conversion_code': conversion_code,
        'purchased_items': purchased_items,
    }
