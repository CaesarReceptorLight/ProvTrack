#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: Sheeba Samuel, <sheeba.samuel@uni-jena.de> https://github.com/Sheeba-Samuel

import os
import os.path

import json

import argparse
from SPARQLWrapper import SPARQLWrapper, N3, JSON
import logging

caesar_sparql_endpoint = SPARQLWrapper("http://localhost:8125/rdf4j-server/repositories/FederationStore_RL_OMERO")


def create_node_link(**kwargs):
    node_link = {
        "nodeName" : kwargs['nodeName'],
        "name" : kwargs['name'],
        "ontologyClassType" : kwargs['ontologyClassType'],
        "link" : {
            "name" : kwargs['linkName'],
            "nodeName" : kwargs['linkNodeName'],
            "direction" : kwargs["direction"]
        }

    }
    if 'value' in kwargs and kwargs['value']:
        node_link["value"] = kwargs['value']
    if 'children' in kwargs and kwargs['children']:
        node_link["children"] = kwargs['children']
    return node_link

def get_experiment_json(selected_id):
    experiment_json = create_experiment_json(selected_id)
    return experiment_json

def get_sparql_query_prefix():
    prefix = "PREFIX : <https://w3id.org/reproduceme#> " + \
             "PREFIX p-plan: <http://purl.org/net/p-plan#> " + \
             "PREFIX prov: <http://www.w3.org/ns/prov#>" +\
             "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>"
    return prefix

def get_sparql_query_results(sparql_query):
    prefix = get_sparql_query_prefix()
    query = prefix + sparql_query

    caesar_sparql_endpoint.setQuery(query)

    caesar_sparql_endpoint.setReturnFormat(JSON)
    results = caesar_sparql_endpoint.query().convert()
    if not results['results']['bindings']:
        return

    return results


def create_experiment_json(selected_id):
    experiment_json = {}
    experiment_json["tree"] = {}
    experiment_children = []
    dataset = ''

    filter_query = "?id=" + str(selected_id)
    sparql_query = "select distinct ?experiment ?name ?dataset where { \
        ?experiment rdf:type :Experiment . \
        ?experiment :name ?name . \
        ?experiment :id ?id FILTER(" + filter_query + ") . \
        ?experiment :status ?status FILTER(?status=1). \
        ?experiment :hasDataset ?dataset .\
        }"
    results = get_sparql_query_results(sparql_query)
    if not results:
        return
    bindings = results['results']['bindings']

    experiment = bindings[0]['experiment']['value']
    experiment_json["tree"]["nodeName"] = experiment
    experiment_json["tree"]["nodeName"] = experiment.split('#')[1]
    experiment_json["tree"]["name"] = bindings[0]['name']['value']
    experiment_json["tree"]["ontologyClassType"] = "plan"
    experiment_json["tree"]["value"] = experiment
    dataset = bindings[0]['dataset']['value']

    # notebooks = create_notebook_json(selected_id)
    subplans = create_subplans_json(experiment)
    steps = create_experiment_steps(experiment)
    variables = create_experiment_variables(experiment)
    omero_properties = create_experiment_omero_properties(dataset)
    if subplans:
        experiment_children = experiment_children + subplans
    if steps:
        experiment_children = experiment_children + steps
    if variables:
        experiment_children = experiment_children + variables
    if omero_properties:
        experiment_children = experiment_children + omero_properties
    # if notebooks:
    #     experiment_children = experiment_children + notebooks

    experiment_json["tree"]["children"] = experiment_children
    return experiment_json


def create_experiment_omero_properties(dataset):
    kwargs = {}
    images = []
    sparql_query = "SELECT DISTINCT ?image ?name ?description WHERE { \
                ?image a :Image . <" + dataset + "> a :Dataset . <" + dataset + "> prov:hadMember ?image . \
                ?image :description ?description . \
                ?image :name ?name .\
                }"
    results = get_sparql_query_results(sparql_query)
    if not results:
        return
    bindings = results['results']['bindings']

    for uid, val in enumerate(bindings):
        image = val['image']['value'].split('#')[1]
        imageName = val['name']['value']
        kwargs['nodeName'] = image
        kwargs['name'] = imageName
        kwargs['ontologyClassType'] = "variable"
        kwargs['linkName'] = "p-plan:correspondsToVariable"
        kwargs['linkNodeName'] = "p-plan:correspondsToVariable"
        kwargs["direction"] = "ASYN"
        node_link = create_node_link(**kwargs)
        node_link['name'] = imageName
        node_link['description'] = val['description']['value']
        # node_link['prov:generatedAtTime'] = val['generatedAtTime']['value']
        node_link['isAvailableAt'] = 'https://sl-omero-test.med.uni-jena.de/webclient/img_detail/' + image.split('_')[1]
        node_link["children"] = create_instrument_properties(image)
        images.append(node_link)


    return images

def create_subplans_json(repr_node):
    subplans = []
    kwargs = {}
    sparql_query = "select distinct ?subplan ?description where { \
        ?subplan p-plan:isSubPlanOfPlan <" + repr_node + ">  . \
        ?subplan :description ?description . \
        }"
    results = get_sparql_query_results(sparql_query)
    if not results:
        return
    bindings = results['results']['bindings']


    for uid, val in enumerate(bindings):
        subplan = val['subplan']['value']
        kwargs['nodeName'] = subplan.split('#')[1]
        kwargs['name'] = subplan.split('#')[1]
        kwargs['ontologyClassType'] = "plan"
        kwargs['linkName'] = "p-plan:isSubPlanOfPlan"
        kwargs['linkNodeName'] = "p-plan:isSubPlanOfPlan"
        kwargs["direction"] = "ASYN"
        node_link = create_node_link(**kwargs)
        node_link['description'] = val['description']['value']
        subplan_steps = create_experiment_steps(subplan)
        if subplan_steps:
            node_link['children'] = subplan_steps
        # node_link = create_node_properties(node_link, subplan)
        subplans.append(node_link)

    return subplans

def get_node_properties(node):
    if '#' in node:
        node = node.split('#')[1]
    property_json = {}
    sparql_query = "select distinct ?prop ?object where { "\
                 + ":" + node + " ?prop ?object  }"
    results = get_sparql_query_results(sparql_query)
    if not results:
        return
    bindings = results['results']['bindings']


    for uid, val in enumerate(bindings):
        prop = val['prop']['value']
        if prop in property_json:
            property_json[prop].append(val['object']['value'])
        else:
            property_json[prop] = [val['object']['value']]
    return property_json


def create_node_properties(node_link, node):
    sparql_query = "select distinct ?prop ?object where { "\
                 + "<" + node + "> ?prop ?object . }"
    results = get_sparql_query_results(sparql_query)
    if not results:
        return
    bindings = results['results']['bindings']

    for uid, val in enumerate(bindings):
        node_link[val['prop']['value'].split('#')[1]] = val['object']['value']
    return node_link


def create_experiment_steps(repr_node):
    steps = []
    kwargs = {}
    node_link = ''
    kwargs = {}
    sparql_query = "select distinct ?step ?description where { \
        ?step p-plan:isStepOfPlan <" +  repr_node + "> . \
        ?step :description ?description . \
        }"
    results = get_sparql_query_results(sparql_query)
    if not results:
        return
    bindings = results['results']['bindings']

    for uid, val in enumerate(bindings):
        step = val['step']['value']
        kwargs['nodeName'] = step.split('#')[1]
        kwargs['name'] = step.split('#')[1]
        kwargs['ontologyClassType'] = "step"
        kwargs['linkName'] = "p-plan:isStepOfPlan"
        kwargs['linkNodeName'] = "p-plan:isStepOfPlan"
        kwargs["direction"] = "ASYN"
        # repr_step = 'repr:' + step.split('#')[1]
        experiment_steps_children = create_experiment_steps_children(step)
        node_link = create_node_link(**kwargs)
        if experiment_steps_children:
            node_link['children'] = experiment_steps_children
        node_link['description'] = val['description']['value']
        # node_link = create_node_properties(node_link, step)
        steps.append(node_link)
    return steps

def create_experiment_steps_children(repr_node):
    output_array = []
    node_link = ''
    sparql_query = "select distinct ?input where { " \
            "<" + repr_node + "> p-plan:hasInputVar ?input . }"
    results = get_sparql_query_results(sparql_query)
    if not results:
        return
    bindings = results['results']['bindings']

    for uid, val in enumerate(bindings):
        kwargs = {}
        input_val = val['input']['value']
        kwargs['nodeName'] = input_val.split('#')[1]
        kwargs['name'] = input_val.split('#')[1]
        kwargs['ontologyClassType'] = "variable"
        kwargs['linkName'] = "p-plan:hasInputVar"
        kwargs['linkNodeName'] = "p-plan:hasInputVar"
        kwargs["direction"] = "ASYN"
        node_link = create_node_link(**kwargs)
        # node_link = create_node_properties(node_link, input_val)
    output_array.append(node_link)

    return output_array

def create_experiment_variables(repr_node):
    variables = []
    kwargs = {}
    node_link = ''
    kwargs = {}
    sparql_query = "select distinct ?variable where { "\
        "<" + repr_node + "> p-plan:correspondsToVariable ?variable . \
        ?variable :name ?name FILTER(?name!='') . \
        }"
    results = get_sparql_query_results(sparql_query)
    if not results:
        return
    bindings = results['results']['bindings']
    kwargs['ontologyClassType'] = "variable"
    kwargs['linkName'] = "p-plan:correspondsToVariable"
    kwargs['linkNodeName'] = "p-plan:correspondsToVariable"
    kwargs["direction"] = "ASYN"

    for uid, val in enumerate(bindings):
        variable = val['variable']['value']
        name = variable.split('#')[1]
        kwargs['nodeName'] = name
        kwargs['name'] = name
        # experiment_steps_children = create_experiment_steps_children(variable)
        node_link = create_node_link(**kwargs)
        # if experiment_steps_children:
        #     node_link['children'] = experiment_steps_children
        # node_link = create_node_properties(node_link, variable)
    variables.append(node_link)
    return variables

def create_instrument_properties(repr_node):
    children = []
    kwargs = {}
    sparql_query = "select distinct ?instrument_part where { "\
            + "?instrument p-plan:correspondsToVariable :" + repr_node + " . \
            ?instrument_part :isPartOf ?instrument . \
            }"
    results = get_sparql_query_results(sparql_query)
    if not results:
        return
    bindings = results['results']['bindings']

    for uid, val in enumerate(bindings):
        instrument = val['instrument_part']['value'].split('#')[1]
        kwargs['nodeName'] = instrument
        kwargs['name'] = instrument
        kwargs['ontologyClassType'] = "entity"
        kwargs['value'] = str(val['instrument_part']['value'])
        kwargs['linkName'] = "p-plan:correspondsToVariable"
        kwargs['linkNodeName'] = "p-plan:correspondsToVariable"
        kwargs["direction"] = "ASYN"
        node_link = create_node_link(**kwargs)
        # node_link['children'] = create_instrument_settings(instrument)

        children.append(node_link)
    return children

def create_instrument_settings(repr_node):
    children = []
    kwargs = {}
    sparql_query = "select distinct ?setting_label ?setting_value where { "\
            + ":" + repr_node + " :hasSetting ?setting .  \
            ?setting rdfs:label ?setting_label ; prov:value ?setting_value FILTER(?setting_value!=''). \
            }"
    results = get_sparql_query_results(sparql_query, omero_sparql_endpoint)
    if not results:
        return
    bindings = results['results']['bindings']

    for uid, val in enumerate(bindings):
        setting = val['setting_label']['value']
        kwargs['nodeName'] = setting
        kwargs['name'] = setting
        kwargs['ontologyClassType'] = "entity"
        kwargs['value'] = val['setting_value']['value']
        kwargs['linkName'] = ":hasSetting"
        kwargs['linkNodeName'] = ":hasSetting"
        kwargs["direction"] = "ASYN"
        node_link = create_node_link(**kwargs)
        children.append(node_link)
    return children


def create_image_properties(repr_node):
    children = []
    kwargs = {}
    sparql_query = "select distinct ?object ?object_value where { "\
            + "<" + repr_node + "> ?prop ?object . \
            OPTIONAL { ?object prov:value ?object_value } . \
            }"
    results = get_sparql_query_results(sparql_query)
    if not results:
        return
    bindings = results['results']['bindings']


    for uid, val in enumerate(bindings):
        object_val = val['object']['value']
        kwargs['nodeName'] = object_val.split('#')[1]
        kwargs['name'] = object_val
        kwargs['ontologyClassType'] = "variable"
        kwargs['value'] = str(val['object_value']['value'])
        kwargs['linkName'] = "repr:reference"
        kwargs['linkNodeName'] = "repr:reference"
        kwargs["direction"] = "ASYN"
        node_link = create_node_link(**kwargs)
        children.append(node_link)
    return children

def create_notebook_json(selected_id):
    notebooks = []
    node_link = ''
    filter_query = "?id=" + str(selected_id)
    sparql_query = "select distinct ?notebook where { \
            ?notebook rdf:type :Notebook . \
            ?experiment rdf:type :Experiment . \
            ?experiment :id ?id FILTER(" + filter_query + ") . \
            ?experiment :status ?status FILTER(?status=1). \
            OPTIONAL { ?notebook p-plan:isSubPlanOfPlan ?experiment } . }"
    results = get_sparql_query_results(sparql_query)
    if not results:
        return
    bindings = results['results']['bindings']



    for uid, val in enumerate(bindings):

        notebook = val['notebook']['value']
        notebook_cells = create_cell_json(notebook)

        kwargs = {}
        kwargs['nodeName'] = notebook.split('#')[1],
        kwargs['name'] = notebook
        kwargs['ontologyClassType'] = "plan"
        kwargs['linkName'] = "p-plan:isSubPlanOfPlan"
        kwargs['linkNodeName'] = "p-plan:isSubPlanOfPlan"
        kwargs["direction"] = "ASYN"
        if notebook_cells:
            kwargs['children'] = notebook_cells
        node_link = create_node_link(**kwargs)
        notebooks.append(node_link)
    return notebooks

def create_cell_json(notebook):
    notebook_cells = {}
    notebook_cells = []
    cell_execution = []
    cell_children = ''
    sparql_query = 'select distinct ?cell where { \
            ?cell rdf:type p-plan:Step . \
            ?cell p-plan:isStepOfPlan <' + notebook + '>  . \
            }'
    results = get_sparql_query_results(sparql_query)
    if not results:
        return

    bindings = results['results']['bindings']


    for uid, val in enumerate(bindings):
        cell = val['cell']['value']
        kwargs = {}
        kwargs['nodeName'] = cell.split('#')[1]
        kwargs['name'] = cell
        kwargs['ontologyClassType'] = "step"
        kwargs['linkName'] = "p-plan:isStepOfPlan"
        kwargs['linkNodeName'] = "p-plan:isStepOfPlan"
        kwargs["direction"] = "ASYN"
        cell_execution = create_cell_execution_json(cell)
        cell_source = create_cell_source(cell)
        cell_output = create_cell_output(cell)
        if cell_source:
            cell_children = cell_source
        if cell_execution:
            cell_children = cell_children + cell_execution
        if cell_output:
            cell_children = cell_children + cell_output

        # cell_children = cell_execution + cell_source + cell_output
        if cell_children:
            kwargs['children'] = cell_children
        node_link = create_node_link(**kwargs)
        notebook_cells.append(node_link)
    return notebook_cells

def create_cell_source(cell):
    cell_source_array = []

    sparql_query = 'select distinct ?cell_source ?cell_source_value where { \
            ' +  '<' + cell + '> p-plan:hasInputVar ?cell_source . \
            ?cell_source rdf:value ?cell_source_value . \
        }'
    results = get_sparql_query_results(sparql_query)
    if not results:
        return


    bindings = results['results']['bindings']


    for uid, val in enumerate(bindings):
        cell_source = val['cell_source']['value']
        kwargs = {}
        kwargs['nodeName'] = cell_source.split('#')[1]
        kwargs['name'] = cell_source
        kwargs['ontologyClassType'] = "variable"
        kwargs['value'] = str(val['cell_source_value']['value'])
        kwargs['linkName'] = "p-plan:hasInputVar"
        kwargs['linkNodeName'] = "p-plan:hasInputVar"
        kwargs["direction"] = "ASYN"
        node_link = create_node_link(**kwargs)
        cell_source_array.append(node_link)

    return cell_source_array

def create_cell_output(cell):
    cell_output_array = []
    sparql_query = 'select distinct * where { \
            ' + '<' + cell + '> p-plan:hasOutputVar ?cell_output . \
            ?cell_output :hasSubOutput ?suboutput . \
            ?suboutput rdf:value ?output_value . \
        }'
    results = get_sparql_query_results(sparql_query)
    if not results:
        return


    bindings = results['results']['bindings']


    for uid, val in enumerate(bindings):
        suboutput = val['suboutput']['value']
        kwargs = {}
        kwargs['nodeName'] = suboutput.split('#')[1]
        kwargs['name'] = suboutput
        kwargs['ontologyClassType'] = "variable"
        kwargs['value'] = [str(val['output_value']['value'])]
        kwargs['linkName'] = "p-plan:hasOutputVar"
        kwargs['linkNodeName'] = "p-plan:hasOutputVar"
        kwargs["direction"] = "ASYN"
        node_link = create_node_link(**kwargs)

        cell_output_array.append(node_link)

    return cell_output_array

def create_cell_execution_json(cell):
    cell_executions = []

    sparql_query = 'select distinct ?cell_execution where { \
            ?cell_execution p-plan:correspondsToStep <' + cell + '> . \
        }'
    results = get_sparql_query_results(sparql_query)
    if not results:
        return

    bindings = results['results']['bindings']


    for uid, val in enumerate(bindings):
        cell_execution = val['cell_execution']['value']
        cell_execution_source_array = create_cell_execution_source(cell_execution)
        cell_execution_output_array = create_cell_execution_output(cell_execution)
        cell_execution_children = cell_execution_source_array + cell_execution_output_array

        kwargs = {}
        kwargs['nodeName'] = cell_execution.split('#')[1]
        kwargs['name'] = cell_execution
        kwargs['ontologyClassType'] = "activity"
        kwargs['linkName'] = "p-plan:correspondsToStep"
        kwargs['linkNodeName'] = "p-plan:correspondsToStep"
        kwargs["direction"] = "ASYN"
        kwargs['children'] = cell_execution_children
        node_link = create_node_link(**kwargs)
        cell_executions.append(node_link)

        cell_execution_source_array = []
        cell_execution_output_array = []
        cell_execution_children = []

    return cell_executions


def create_cell_execution_output(cell_execution):
    cell_execution_output_array = []
    sparql_query = 'select distinct ?suboutput ?output_value where { \
            ' + '<' + cell_execution + '> prov:generated ?cell_execution_output . \
            ?cell_execution_output :hasSubOutput ?suboutput . \
            ?suboutput rdf:value ?output_value . \
        }'
    results = get_sparql_query_results(sparql_query)
    if not results:
        return

    bindings = results['results']['bindings']


    for uid, val in enumerate(bindings):
        suboutput = str(val['suboutput']['value'])
        kwargs = {}
        kwargs['nodeName'] = suboutput.split('#')[1]
        kwargs['name'] = suboutput
        kwargs['ontologyClassType'] = "variable"
        kwargs['value'] = [str(val['output_value']['value'])]
        kwargs['linkName'] = "prov:generated"
        kwargs['linkNodeName'] = "prov:generated"
        kwargs["direction"] = "ASYN"
        node_link = create_node_link(**kwargs)

        cell_execution_output_array.append(node_link)

    return cell_execution_output_array

def create_cell_execution_source(cell_execution):
    cell_execution_sources = []
    sparql_query = 'select distinct ?cell_execution_source ?source_value where { \
            ' + '<' + cell_execution + '> prov:used ?cell_execution_source . \
            ?cell_execution_source rdf:value ?source_value . \
        }'
    results = get_sparql_query_results(sparql_query)
    if not results:
        return

    bindings = results['results']['bindings']
    for uid, val in enumerate(bindings):
        cell_execution_source = val['cell_execution_source']['value']
        kwargs = {}
        kwargs['nodeName'] = cell_execution_source.split('#')[1]
        kwargs['name'] = cell_execution_source
        kwargs['ontologyClassType'] = "entity"
        kwargs['value'] = [str(val['source_value'])]
        kwargs['linkName'] = "prov:used"
        kwargs['linkNodeName'] = "prov:used"
        kwargs["direction"] = "ASYN"
        node_link = create_node_link(**kwargs)

        cell_execution_sources.append(node_link)
    return cell_execution_source
