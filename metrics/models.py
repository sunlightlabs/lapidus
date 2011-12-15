from django.db import models
from lapidus.metrics import daterange
from lapidus.metrics.validation import LIST_SCHEMA
import json
import uuid
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import validictory

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from django_extensions.db.fields.json import JSONField

# import the logging library
import logging
# Get an instance of a logger
logger = logging.getLogger(__name__)


CATEGORIES = (
    (1, 'web'),
    (2, 'api'),
    (3, 'content'),
    (4, 'other'),
)

PERIODS = (
    (1, 'hourly'),
    (2, 'daily'),
    (3, 'weekly'),
    (4, 'montly'),
    (5, 'yearly'),
    (6, 'other'),
)

# METRIC_TYPES = (
#     ('value', 'value'),
#     ('list', 'list'),
#     ('', 'other'),
# )

UNIT_TYPES = (
    ('count',       'Count'),
    ('seconds',     'Seconds'),    
    ('list',        'List'),    
    ('ratio',       'Ratio'),            
    ('percentage',  'Percentage'),            
)

UNIT_MAP = {
    'count': 'countobservation',
    'seconds': 'countobservation',
    'list': 'objectobservation',
    'ratio': 'ratioobservation',
    'percentage': 'ratioobservation'
    
}

unit_name, unit_model = zip(*UNIT_TYPES)

class Unit(models.Model):
    name = models.CharField(max_length=128)
    slug = models.SlugField(unique=True)
    category = models.IntegerField(choices=CATEGORIES)
    period = models.IntegerField(choices=PERIODS)
    observation_type = models.ForeignKey(ContentType, editable=False, blank=True, null=True,
                                            limit_choices_to= Q(
                                                Q(app_label='metrics'),
                                                Q(model='countobservation') | Q(model='objectobservation') | Q(model='ratioobservation')                                            
                                            ))
    observation_unit = models.CharField(max_length=255, default='count', choices=UNIT_TYPES)
    
    class Meta:
        ordering = ('name',)
    
    def __unicode__(self):
        return u"%s: %s" % (self.get_category_display(), self.name)
    
    def _set_observation_type_from_unit(self):
        model = UNIT_MAP[self.observation_unit]
        self.observation_type = ContentType.objects.get(app_label='metrics', model=model)
    
    def save(self, *args, **kwargs):
        self._set_observation_type_from_unit()
        super(Unit, self).save(*args, **kwargs)
        

class Project(models.Model):
    name = models.CharField(max_length=128)
    slug = models.SlugField(unique=True)
    url = models.URLField(blank=True, null=True, verify_exists=False, help_text="Optional url for project websites. used for grabbing shares from the Facebook Graph")
    api_key = models.CharField(max_length=128, blank=True)
    
    class Meta:
        ordering = ('name',)
    
    def __unicode__(self):
        return self.name
    
    def save(self, **kwargs):
        if not self.api_key:
            self.api_key = uuid.uuid4().hex
        super(Project, self).save(**kwargs)

class Annotation(models.Model):
    project = models.ForeignKey(Project, related_name="annotations")
    timestamp = models.DateTimeField(blank=True, null=True)
    text = models.TextField()

class Metric(models.Model):
    project = models.ForeignKey(Project, related_name="metrics")
    unit = models.ForeignKey(Unit, related_name="metrics")
    is_cumulative = models.BooleanField(default=False)
    _observations = None
    
    class Meta:
        ordering = ('project','unit')
    
    @property
    def related_observations(self):
        obs_class = self.unit.observation_type.model_class()
        if not self._observations:
           self._observations = obs_class.objects.select_related().filter(metric=self)
        return self._observations
    
    def __unicode__(self):
        return u"%s: %s" % (self.project.name, self.unit.name)

class Observation(models.Model):
    metric = models.ForeignKey(Metric, related_name="observations")
    from_datetime = models.DateTimeField()
    to_datetime = models.DateTimeField()
    
    class Meta:
        ordering = ('-from_datetime',)

class CountObservation(Observation):
    """Stores a metric observation whose value is a count of some unit"""
    value = models.IntegerField(blank=True, null=True)

    def __unicode__(self):
        return u"<{metric}: {value}>".format(metric=self.metric, value=self.value)

class ObjectObservation(Observation):
    """Stores a metric observation whose value is a data object stored as JSON. Currently limited as it validates against a 'ranked list' schema."""
    jsonvalue = JSONField()
    
    def _set_value(self, value):
        try:
            validictory.validate(value, LIST_SCHEMA)
            value = sorted(value, key=lambda x: x['rank'])
            self.jsonvalue = value
        except ValueError, e:
            raise e
    
    def _get_value(self):
        return self.jsonvalue
    
    value = property(_get_value, _set_value)
    
    def __unicode__(self):
        return u"<{metric}>".format(metric=self.metric)

class RatioObservation(Observation):
    """Relates two CountObservation objects to create a ratio (which can represent a percentage, etc)"""
    antecedent = models.ForeignKey(CountObservation, related_name="antecedents")
    consequent = models.ForeignKey(CountObservation, related_name="consequents")
    _value = False
    
    def _get_value(self):
        if isinstance(self._value, bool):
            if isinstance(self.antecedent.value, int) and isinstance(self.consequent.value, int):
                self._value = Decimal(self.antecedent.value)/Decimal(self.consequent.value)
            else:
                self._value = None
        return self._value
    value = property(_get_value)
    
    def save(self, *args, **kwargs):
        self.from_datetime = self.antecedent.from_datetime
        self.to_datetime = self.antecedent.to_datetime
        super(RatioObservation, self).save(*args, **kwargs)
        
    
    def __unicode__(self):
        return u"<{metric}: {antecedent}/{consequent}>".format(metric=self.metric, antecedent=self.antecedent, consequent=self.consequent)

