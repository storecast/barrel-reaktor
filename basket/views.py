from django.http import HttpResponse
from django.shortcuts import redirect
from babeldjango.templatetags.babel import currencyfmt
import simplejson as json

from txtr_skins.apps.jinja_lib.ext.djangojinja2 import get_env
from txtr_skins.apps.compact_url import reverse
from txtr_skins.apps.reaktor_auth.decorators import login_required_on_render
from . import get_basket_from_request, update_basket_for_request


HTML = """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="{{ LANGUAGE_CODE|e }}" lang="{{ LANGUAGE_CODE|e }}">
    <head>
        <title>Checkout Complete!</title>
        <meta http-equiv="content-type" content="text/html;charset=utf-8" />
    </head>
    <script type=text/javascript>
            function onComplete() {
                    if (window.parent) {
                            if (window.parent.checkout_plugin) {
                                messageBody = document.getElementById("message")
                                messageBody.textContent = window.parent.checkout_plugin.{{method}}();
                            }
                            else if (window.parent.{{method}}) {
                                messageBody = document.getElementById("message")
                                messageBody.textContent = window.parent.{{method}}();
                            }
                    }
            }
    </script>
    <body onload="onComplete()">
        <h4 id="message" style="font-family:Helvetica,sans-serif; text-align:center; color: #777777; vertical-align: middle; font-weight: normal;"></h4>
    </body>
</html>
"""


def checkout_complete(request):
    # called from the user settings form
    if request.session.get("validation_basket", None):
        request.session["payment-data-updated"] = True # used in the user settings to select the correct accordion panel
        if request.session.get("payment_validation_url", None):
            return redirect(request.session.pop("payment_validation_url"))
        else: # fallback behaviour
            return redirect('user-settings-payment-data')
    # called during the checkout
    elif request.session.get("checkout_basket", None):
        request.session["initiate_checkout"] = True
        # TODO: the checkout-complete should be removed when the new checkout works on ereader and web
        return redirect(reverse('basket', get={'checkout-complete': ''}))
    # what's that?
    else:
        return redirect("pages-root")


def checkout_cancel(request):
    env = get_env()
    template = env.from_string(HTML)
    return HttpResponse(template.render({
        'LANGUAGE_CODE': request.LANGUAGE_CODE,
        'method': 'checkoutCancel',
    }))


@login_required_on_render(anonymous_allowed=True)
def update_item(request):
    """Handles ajax request for basket update.
    Returns json response.
    Works with new API wrapper.
    """
    basket = get_basket_from_request(request)
    basket, document, updated = update_basket_for_request(request, basket)
    response = {'updated': updated, 'action': request.POST.get('item_action')}
    response['length'] = len(basket.items)
    response['amount'] = currencyfmt(float(basket.total.amount), basket.total.currency.code)
    if document:
        response["new_item"] = {}
        response["new_item"]["title"] = document.attributes.title
        response["new_item"]["subtitle"] = document.attributes.subtitle if hasattr(document.attributes, 'subtitle') else '' # subtitle is not always returned by reaktor
        response["new_item"]["author"] = document.attributes.author
        response["new_item"]["document_id"] = document.id
        response["new_item"]["price"] = currencyfmt(float(document.price.amount), document.price.currency.code)
        response["new_item"]["cover_url"] = document.attributes.normal_cover_url

    # ugly hack
    # if the basket is empty, we return json with url to redirect to - then `checkout_nju` plugin will handle the case
    # we should make a redirect in case of the free checkout as well - the `Proceed` link is different
    # this also covers the case when the basket is completely covered by voucher
    if not response['length'] or not basket.total.amount:
        response["redirect"] = reverse("basket")

    return HttpResponse(json.dumps(response), content_type="application/json")
