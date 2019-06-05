#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Author: Sheeba Samuel, Friedrich-Schiller University, Jena
Email: caesar@uni-jena.de
Date created: 20.11.2018
'''

from django.conf.urls import *

from ProvTrack import views

urlpatterns = patterns('django.views.generic.simple',
    url( r'^$', views.provtrack, name='provtrack' ),
    url(r'^get_provenance_json/$', views.get_provenance_json, name="get_provenance_json"),
    url(r'^get_infobox_json/$', views.get_infobox_json, name="get_infobox_json"),
 )
