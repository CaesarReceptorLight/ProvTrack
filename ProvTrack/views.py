#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Author: Sheeba Samuel, Friedrich-Schiller University, Jena
Email: caesar@uni-jena.de
Date created: 20.11.2018
'''

from django.shortcuts import render
from django.utils.encoding import smart_str

from django.http import HttpResponse
from omeroweb.webclient.decorators import login_required
from omeroweb.webclient.decorators import render_response
import omero
import Ice
import IceImport

import experimentController

import json
import os
import os.path
import omero.java
import logging
import trackprov

import time
logger = logging.getLogger(__name__)


@login_required()
def provtrack(request,  conn=None, **kwargs):
    input_type = 'Experiment'
    all_experiments_choices = experimentController.get_options(conn, input_type)
    context={"all_experiments": all_experiments_choices}
    return render(request, 'ProvTrack/index.html', context)

def get_infobox_json(request, conn=None, **kwargs):
    if request.is_ajax():
        selected_value = request.GET.get('value', '')
        infobox_json = trackprov.get_node_properties(selected_value)
        return HttpJsonResponse(
            {
                'response': infobox_json
            },
            cls=DatetimeEncoder
        )

def get_provenance_json(request, conn=None, **kwargs):
    if request.is_ajax():
        selected_id = request.GET.get('id', '')
        if selected_id == '-1':
            infile = 'static/ProvTrack/data/experiment_example_provtrack.json'
            with open(infile) as json_file:
                experiment_json = json.load(json_file)
        else:
            experiment_json = trackprov.get_experiment_json(selected_id)
        return HttpJsonResponse(
            {
                'response': experiment_json
            },
            cls=DatetimeEncoder
        )
    else:
        data = 'fail'
    mimetype = 'application/json'
    return HttpResponse(data, mimetype)

class HttpJsonResponse(HttpResponse):
    def __init__(self, content, cls=json.JSONEncoder.default):
        HttpResponse.__init__(
            self, json.dumps(content, cls=cls),
            content_type="application/json"
        )


class DatetimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)
