#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: Sheeba Samuel, <sheeba.samuel@uni-jena.de> https://github.com/Sheeba-Samuel

import os
import os.path

import json

from rdflib import Graph
import nbformat
import nbformat.v4.nbbase as nbbase
import argparse

def create_node_link(**kwargs):
    node_link = {
        "nodeName" : kwargs['nodeName'],
        "name" : kwargs['name'],
        "type" : kwargs['type'],
        "ontologyClass" : kwargs['ontologyClass'],
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

def create_experiment_json(rdfgraph):
    experiment_json = {}
    experiment_json["tree"] = {}
    for row in rdfgraph.query(
        'select ?experiment ?prop ?object where { \
        ?experiment rdf:type repr:Experiment . \
        ?experiment ?prop ?object . \
        }'
    ):
        experiment = str(row.experiment)
        experiment_json["tree"]["nodeName"] = experiment.split('#')[1]
        experiment_json["tree"]["name"] = experiment
        experiment_json["tree"]["type"] = "entity"
        experiment_json["tree"]["ontologyClass"] = "Experiment"
        experiment_json["tree"]["value"] = experiment
        experiment_json["tree"][row.prop.split('#')[1]] = row.object

    notebooks = create_notebook_json(rdfgraph)
    subplans = create_subplans_json(rdfgraph)
    steps = create_experiment_steps(rdfgraph)
    experiment_children = notebooks + steps + subplans
    experiment_json["tree"]["children"] = experiment_children
    return experiment_json

def create_subplans_json(rdfgraph):
    subplans = []
    kwargs = {}
    print("create")
    for row in rdfgraph.query(
        'select ?subplan where { \
        ?subplan rdf:type repr:Protocol . \
        ?experiment rdf:type repr:Experiment . \
        ?subplan p-plan:isSubPlanOfPlan ?experiment  . \
        }'
    ):
        subplan = str(row.subplan)
        kwargs['nodeName'] = subplan.split('#')[1],
        kwargs['name'] = subplan
        kwargs['type'] = "plan"
        kwargs['ontologyClass'] = "Plan"
        kwargs['linkName'] = "p-plan:isSubPlanOfPlan"
        kwargs['linkNodeName'] = "p-plan:isSubPlanOfPlan"
        kwargs["direction"] = "ASYN"
        node_link = create_node_link(**kwargs)
        repr_node = 'repr:' + subplan.split('#')[1]
        for row in rdfgraph.query(
            'select ?prop ?object where { \
            ' + repr_node + ' ?prop ?object . \
            }'
        ):
            node_link[row.prop.split('#')[1]] = row.object
        subplans.append(node_link)

    return subplans

def create_experiment_steps(rdfgraph):
    steps = []
    kwargs = {}
    node_link = ''
    for row in rdfgraph.query(
        'select ?step ?prop ?object where { \
        ?experiment rdf:type repr:Experiment . \
        ?step p-plan:isStepOfPlan ?experiment . \
        }'
    ):
        step = str(row.step)
        kwargs['nodeName'] = step.split('#')[1],
        kwargs['name'] = step
        kwargs['type'] = "step"
        kwargs['ontologyClass'] = step
        kwargs['linkName'] = "p-plan:isStepOfPlan"
        kwargs['linkNodeName'] = "p-plan:isStepOfPlan"
        kwargs["direction"] = "ASYN"
        repr_step = 'repr:' + step.split('#')[1]
        experiment_steps_children = create_experiment_steps_children(rdfgraph, repr_step)
        node_link = create_node_link(**kwargs)
        node_link['children'] = experiment_steps_children

        for row in rdfgraph.query(
            'select ?prop ?object where { \
            ' + repr_step + ' ?prop ?object . \
            }'
        ):
            node_link[row.prop.split('#')[1]] = row.object
        steps.append(node_link)
    return steps

def create_experiment_steps_children(rdfgraph, repr_node):
    output_array = []

    for row in rdfgraph.query(
            'select * where { \
            ?output p-plan:isOutputVarOf ' + repr_node + ' . \
        }'
    ):
        kwargs = {}
        kwargs['nodeName'] = row.output.split('#')[1]
        kwargs['name'] = row.output
        kwargs['type'] = "variable"
        kwargs['ontologyClass'] = "Variable"
        kwargs['linkName'] = "p-plan:hasOutputVar"
        kwargs['linkNodeName'] = "p-plan:hasOutputVar"
        kwargs["direction"] = "ASYN"
        node_link = create_node_link(**kwargs)


        repr_node = 'repr:' + row.output.split('#')[1]

        for row in rdfgraph.query(
            'select ?prop ?object where { \
            ' + repr_node + ' ?prop ?object . \
            }'
        ):
        #     if row.prop.split('#')[1] in node_link:
        #         print("Already yhrte")
        #     else:
        #         print("not there")
            node_link[row.prop.split('#')[1]] = row.object
        node_link["children"] = create_image_properties(rdfgraph, repr_node)
        output_array.append(node_link)

    return output_array

def create_image_properties(rdfgraph, repr_node):
    children = []
    for row in rdfgraph.query(
            'select ?object_value ?object where { \
            ' + repr_node + ' ?prop ?object . \
            ?object rdf:value ?object_value . \
            }'
        ):
        kwargs = {}
        kwargs['nodeName'] = row.object.split('#')[1]
        kwargs['name'] = row.object
        kwargs['type'] = "variable"
        kwargs['ontologyClass'] = "Variable"
        kwargs['value'] = row.object_value
        kwargs['linkName'] = "repr:reference"
        kwargs['linkNodeName'] = "repr:reference"
        kwargs["direction"] = "ASYN"
        node_link = create_node_link(**kwargs)
        children.append(node_link)
    return children

def create_notebook_json(rdfgraph):
    notebooks = []
    for row in rdfgraph.query(
        'select ?experiment ?notebook where { \
        ?notebook rdf:type repr:Notebook . \
        ?experiment rdf:type repr:Experiment . \
        OPTIONAL { ?notebook p-plan:isSubPlanOfPlan ?experiment } . \
        }'
    ):
        notebook = str(row.notebook)
        notebook_cells = create_cell_json(rdfgraph, notebook)

        kwargs = {}
        kwargs['nodeName'] = notebook.split('#')[1],
        kwargs['name'] = notebook
        kwargs['type'] = "plan"
        kwargs['ontologyClass'] = "Notebook"
        kwargs['linkName'] = "p-plan:isSubPlanOfPlan"
        kwargs['linkNodeName'] = "p-plan:isSubPlanOfPlan"
        kwargs["direction"] = "ASYN"
        kwargs['children'] = notebook_cells
        node_link = create_node_link(**kwargs)
        notebooks.append(node_link)
    return notebooks

def create_cell_json(rdfgraph, notebook):
    notebook_cells = {}
    repr_notebook = 'repr:' + notebook.split('#')[1]
    notebook_cells = []
    cell_execution = []

    for row in rdfgraph.query(
            'select * where { \
            ?cell rdf:type p-plan:Step . \
            ?cell p-plan:isStepOfPlan ' + repr_notebook + '  . \
            ?cell repr:hasCellType ?cell_type . \
            ?cell repr:hasIndex ?cell_index . \
            OPTIONAL { ?cell repr:hasExecutionCount ?cell_execution_count } . \
        } ORDER BY xsd:integer(?cell_index)'
    ):
        cell_execution = create_cell_execution_json(rdfgraph, row.cell)
        cell_source = create_cell_source(rdfgraph, row.cell)
        cell_output = create_cell_output(rdfgraph, row.cell)
        cell_children = cell_execution + cell_source + cell_output

        kwargs = {}
        kwargs['nodeName'] = row.cell.split('#')[1]
        kwargs['name'] = row.cell
        kwargs['type'] = "step"
        kwargs['ontologyClass'] = "Cell"
        kwargs['linkName'] = "p-plan:isStepOfPlan"
        kwargs['linkNodeName'] = "p-plan:isStepOfPlan"
        kwargs["direction"] = "ASYN"
        kwargs['children'] = cell_children
        node_link = create_node_link(**kwargs)
        notebook_cells.append(node_link)

    return notebook_cells

def create_cell_source(rdfgraph, cell):
    cell_source_array = []
    repr_cell = 'repr:' + cell.split('#')[1]

    for row in rdfgraph.query(
            'select * where { \
            ' + repr_cell + ' p-plan:hasInputVar ?cell_source . \
            ?cell_source rdf:value ?cell_source_value . \
        }'
    ):
        kwargs = {}
        kwargs['nodeName'] = row.cell_source.split('#')[1]
        kwargs['name'] = row.cell_source
        kwargs['type'] = "variable"
        kwargs['ontologyClass'] = "Variable"
        kwargs['value'] = row.cell_source_value
        kwargs['linkName'] = "p-plan:hasInputVar"
        kwargs['linkNodeName'] = "p-plan:hasInputVar"
        kwargs["direction"] = "ASYN"
        node_link = create_node_link(**kwargs)
        cell_source_array.append(node_link)

    return cell_source_array

def create_cell_output(rdfgraph, cell):
    cell_output_array = []
    repr_cell = 'repr:' + cell.split('#')[1]

    for row in rdfgraph.query(
            'select * where { \
            ' + repr_cell + ' p-plan:hasOutputVar ?cell_output . \
            ?cell_output repr:hasSubOutput ?suboutput . \
            ?suboutput rdf:value ?output_value . \
        }'
    ):
        kwargs = {}
        kwargs['nodeName'] = row.suboutput.split('#')[1]
        kwargs['name'] = row.suboutput
        kwargs['type'] = "variable"
        kwargs['ontologyClass'] = "Variable"
        kwargs['value'] = [row.output_value]
        kwargs['linkName'] = "p-plan:hasOutputVar"
        kwargs['linkNodeName'] = "p-plan:hasOutputVar"
        kwargs["direction"] = "ASYN"
        node_link = create_node_link(**kwargs)

        cell_output_array.append(node_link)

    return cell_output_array

def create_cell_execution_json(rdfgraph, cell):
    cell_execution = []
    repr_cell = 'repr:' + cell.split('#')[1]

    for row in rdfgraph.query(
            'select * where { \
            ?cell_execution p-plan:correspondsToStep ' + repr_cell + ' . \
        }'
    ):
        cell_execution_source_array = create_cell_execution_source(rdfgraph, row.cell_execution)
        cell_execution_output_array = create_cell_execution_output(rdfgraph, row.cell_execution)
        cell_execution_children = cell_execution_source_array + cell_execution_output_array

        kwargs = {}
        kwargs['nodeName'] = row.cell_execution.split('#')[1]
        kwargs['name'] = row.cell_execution
        kwargs['type'] = "activity"
        kwargs['ontologyClass'] = "CellExecution"
        kwargs['linkName'] = "p-plan:correspondsToStep"
        kwargs['linkNodeName'] = "p-plan:correspondsToStep"
        kwargs["direction"] = "ASYN"
        kwargs['children'] = cell_execution_children
        node_link = create_node_link(**kwargs)
        cell_execution.append(node_link)

        cell_execution_source_array = []
        cell_execution_output_array = []
        cell_execution_children = []

    return cell_execution


def create_cell_execution_output(rdfgraph, cell_execution):
    repr_cell_execution = 'repr:' + cell_execution.split('#')[1]
    cell_execution_output_array = []
    for row in rdfgraph.query(
            'select * where { \
            ' + repr_cell_execution + ' prov:generated ?cell_execution_output . \
            ?cell_execution_output repr:hasSubOutput ?suboutput . \
            ?suboutput rdf:value ?output_value . \
        }'
    ):
        kwargs = {}
        kwargs['nodeName'] = row.suboutput.split('#')[1]
        kwargs['name'] = row.suboutput
        kwargs['type'] = "variable"
        kwargs['ontologyClass'] = "Output"
        kwargs['value'] = [str(row.output_value)]
        kwargs['linkName'] = "prov:generated"
        kwargs['linkNodeName'] = "prov:generated"
        kwargs["direction"] = "ASYN"
        node_link = create_node_link(**kwargs)

        cell_execution_output_array.append(node_link)

    return cell_execution_output_array

def create_cell_execution_source(rdfgraph, cell_execution):
    cell_execution_source = []
    repr_cell_execution = 'repr:' + cell_execution.split('#')[1]

    for row in rdfgraph.query(
            'select * where { \
            ' + repr_cell_execution + ' prov:used ?cell_execution_source . \
            ?cell_execution_source rdf:value ?source_value . \
        }'
    ):
        kwargs = {}
        kwargs['nodeName'] = row.cell_execution_source.split('#')[1]
        kwargs['name'] = row.cell_execution_source
        kwargs['type'] = "entity"
        kwargs['ontologyClass'] = "Source",
        kwargs['value'] = [str(row.source_value)]
        kwargs['linkName'] = "prov:used"
        kwargs['linkNodeName'] = "prov:used"
        kwargs["direction"] = "ASYN"
        node_link = create_node_link(**kwargs)

        cell_execution_source.append(node_link)
    return cell_execution_source

def get_experiment_json(rdfgraph):
    experiment_json = create_experiment_json(rdfgraph)

    return experiment_json


def convert_rdf_to_json(file_name):
    infile = file_name

    input_file = os.path.basename(infile)
    jsonfile_name, extension = os.path.splitext(input_file)
    input_file_directory = os.path.dirname(infile)
    output_file_extension = 'json'
    output_file = os.path.join(input_file_directory, jsonfile_name + "_rdf2json." + output_file_extension)
    print("Converting RDF file {0} to json {1}".format(input_file,output_file))

    notebook = open(infile).read()
    g = Graph()
    nbrdf = g.parse(infile, format="turtle")
    json_data = json.dumps(get_experiment_json(nbrdf))
    with open(output_file, 'w') as fout:
        fout.write(json_data)
        return fout
