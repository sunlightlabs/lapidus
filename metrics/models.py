from django.db import models
from lapidus.metrics import daterange
from lapidus.metrics.validation import LIST_SCHEMA
import json
import uuid
import validictory

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

METRIC_TYPES = (
    ('value', 'value'),
    ('list', 'list'),
    ('', 'other'),
)

class Unit(models.Model):
    name = models.CharField(max_length=128)
    slug = models.SlugField(unique=True)
    category = models.IntegerField(choices=CATEGORIES)
    period = models.IntegerField(choices=PERIODS)
    
    class Meta:
        ordering = ('-category', 'name')
    
    def __unicode__(self):
        return u"%s: %s" % (self.get_category_display(), self.name)

class Project(models.Model):
    name = models.CharField(max_length=128)
    slug = models.SlugField(unique=True)
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
    type = models.CharField(max_length=16, choices=METRIC_TYPES, default='')
    is_cumulative = models.BooleanField(default=False)
    
    class Meta:
        ordering = ('project','unit')
    
    def __unicode__(self):
        return u"%s %s" % (self.project.name, self.unit.name)
    
    def date_range(self, start, end):
        
        if self.unit.period != 2:
            raise ValueError('cannot iterate over dates for a non-daily metric')
            
        obs = self.observations.filter(from_datetime__gte=start, from_datetime__lte=end)
        obs = dict((ob.from_datetime.date().isoformat(), ob) for ob in obs)
        
        return [(d, obs.get(d.date().isoformat(), None)) for d in daterange(start, end)]
        

class Observation(models.Model):
    metric = models.ForeignKey(Metric, related_name="observations")
    from_datetime = models.DateTimeField()
    to_datetime = models.DateTimeField()
    value = models.FloatField(blank=True, null=True)
    payload = models.TextField(blank=True)
    
    class Meta:
        ordering = ('-from_datetime',)
    
    def __unicode__(self):
        return u"%s" % self.value

    def save(self, **kwargs):
        if self.metric.type == 'list' and self.payload:
            data = json.loads(self.payload)
            validictory.validate(data, LIST_SCHEMA)
        super(Observation, self).save(**kwargs)

