# Lapidus: Metrics Dashboard Tool #

## Overview ##

Lapidus is a Django-based tool for collecting and presenting analytics data across various types of projects.The goal for this tool is to make it easy to observe and analyze metric observations at a glance. In order to provide flexibility, Lapidus consists of separate apps for storing *metrics*, *loading* data from external sources, and presenting the data in a *dashboard*.

### The metrics app ###

Given the various possible sources for and types of metrics, the data models for the *metrics* app are generic. You can store CountObservations (integer values), create ratios from CountObservations, and store JSON objects (validating against a `LIST_SCHEMA` defined in validation.py). You also identify a category, period and unit\_type (which determines what Observation class is used to store data).

The *metrics* app has an API created via [tastypie](https://github.com/toastdriven/django-tastypie), so you can allow your projects to post directly to lapidus. You can post observations to project metrics using an API key assigned to that project. You cannot create new units/metrics via the API, so any project that will POST custom metrics to lapidus will need those metrics defined in lapidus first. Read tastypie's documentation on [interacting with the API](http://django-tastypie.readthedocs.org/en/latest/interacting.html) for further information.

### The loading app ###

In order to populate the metrics, the *loading* app contains a few management commands for pulling data from different sources. 

The **loadga** command loads data from Google Analytics (GA), using the data/ga.json file to configure which metrics to pull and how to match them to metrics in lapidus. The ga.json file also contains the slugs and GA profile ids needed to match between GA projects and lapidus projects. This may change in the future as configuration via the admin is fleshed out.

A **loadfacebook** command retrieves the *total\_count* for Facebook shares, likes, and comments (same number as the Like button embed counter). It pulls the url from the *metrics* app's Project model.

### The dashboard app ###

This contains all of the logic for the front-end display of the data.

The templates reside in the project-level templates directory rather than in an app-level templates directory. The `_render_observation.html` template may be of interest as it does the work of properly rendering an observation based on it's class and .unit\_type. Additionally, there is a `_render_observation_value.html` that attempts to output the value without html formatting. This one doesn't attempt to handle ObjectObservations.


## Installation ##

This is not a packaged application. Fork the code, or download a tag, and set up as you would a Django project. You can `pip install -r requirements.txt` for your python environment.

## Configuration & Getting Started ##

Copy `local_settings.example.py` to `local_settings.py` and customize to your system. This project has been developed against PostgreSQL, but doesn't contain any PostgreSQL-specific optimizations. Additionally, `gunicorn` is listed in installed apps, so if you aren't using `gunicorn`, you should comment that out.

`GA_EMAIL`, `GA_PASSWORD`, and `GA_CONFIG` allow you to connect your copy of lapidus to your Google Analytics account and projects. There is a default `config/ga.json` included, but you will need to edit the project slugs and GA profile ids to match your GA projects. 

You may also want to edit `config/ratios.json` for additional ratios you want to calculate and connect it using the `RATIOS_CONFIG` setting.

The `UNIT_COMPARE_PAST` tuple allows you to determine what units will render a color indicator when comparing one date range to the same timedelta immediately before it. Basically this was put in so we could visually indicate whether a 'visits' metric increased or decreased from the previous period. This will work with other CountObservations and RatioObservations, but not ObjectObservations.

Once you have your database created and GA configured, you can start populating lapidus with Projects and Units, and then you can create metrics. The **loadga** command will create units and metrics for projects as defined in `config/ga.json`, but you must create the Project records before you can run that command.

You can create a UnitList and assign it as default\_for for different categories (web, api, content, other) of metrics if you want to control which metrics appear on a dashboard. Otherwise, the dashboard will display all metrics for a particular category.