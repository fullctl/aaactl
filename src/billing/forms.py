from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext as _
from django_countries.fields import CountryField

import billing.payment_processors
from billing.models import PaymentMethod, Product


class BillingSetupInitForm(forms.Form):
    product = forms.CharField(widget=forms.HiddenInput(), required=False)
    subscription_cycle = forms.CharField(widget=forms.HiddenInput(), required=False)
    redirect = forms.CharField(widget=forms.HiddenInput(), required=False)

    def clean(self):
        cleaned_data = super().clean()
        prod_name = cleaned_data.get("product")

        try:
            product = Product.objects.get(name=prod_name)
        except Product.DoesNotExist:
            raise forms.ValidationError(_("Unknown product: {}").format(prod_name))

        self.prod_instance = product

        try:
            self.recurring_instance = product.recurring_product
        except ObjectDoesNotExist:
            self.recurring_instance = None

        return cleaned_data


class SelectPaymentMethodForm(forms.Form):
    payment_method = forms.ModelChoiceField(
        queryset=PaymentMethod.objects.all(),
        required=False,
        label=_("Saved payment method"),
    )

    def __init__(self, org, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["payment_method"].queryset = PaymentMethod.get_for_org(org)


class CreatePaymentMethodForm(forms.Form):
    processor = forms.ChoiceField(
        choices=billing.payment_processors.choices(), widget=forms.HiddenInput()
    )


class BillingAddressForm(forms.Form):
    holder = forms.CharField(label=_("Full Name"))
    email = forms.EmailField(label=_("Email Address"))
    country = CountryField().formfield(initial="US", label=_("Country"))
    city = forms.CharField(label=_("City"))
    address1 = forms.CharField(label=_("Address"))
    address2 = forms.CharField(label=_("Address (2)"), required=False)
    postal_code = forms.CharField(label=_("Postal Code"))
    state = forms.CharField(label=_("State"), required=False)


class BillingAgreementsForm(forms.Form):
    agreement_tos = forms.BooleanField(label=_("I agree to the Terms of Service"))


class BillingContactForm(forms.Form):
    name = forms.CharField(
        label=_("Name"), widget=forms.TextInput(attrs={"readonly": True})
    )
    email = forms.EmailField(label=_("Email Address"))
