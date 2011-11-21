from django.db import models
from django import forms

from metrics.models import Unit

class UnitCollection(models.Model):
    """(UnitCollection description)"""
    name = models.CharField(blank=True, max_length=255)
    slug = models.SlugField(unique=True)
    units = models.ManyToManyField(Unit, through='OrderedMembership')

    def __unicode__(self):
        return "<UnitCollection: {name}>".format(name=self.name)
    
    def ordered_units(self):
        """returns a list of units ordered by their membership order value"""
        return self.orderedmembership_set.all()
    
    def list_of_units(self):
        """Return a string representation of units"""
        u_list = [u['name'] for u in self.units.order_by('orderedmembership__order').values()]
        return u', '.join(u_list)


class OrderedMembership(models.Model):
    """(OrderedCollection description)"""
    collection = models.ForeignKey(UnitCollection)
    unit = models.ForeignKey(Unit)
    order = models.SmallIntegerField(blank=False)
    
    class Meta:
        ordering = ['order',]
    
    def __unicode__(self):
        return u"<OrderedMembership: '{unit}' in {collection}>".format(collection=self.collection, unit=self.unit)


class DateRangeForm(forms.Form):
    """Form for date-range searches"""
    from_datetime = forms.DateField(widget=forms.DateInput(attrs={'class':'datefield'}))
    to_datetime = forms.DateField(widget=forms.DateInput(attrs={'class':'datefield'}), required=False)
        