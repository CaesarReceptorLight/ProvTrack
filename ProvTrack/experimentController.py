#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Author: Sheeba Samuel, Friedrich-Schiller University, Jena
Email: caesar@uni-jena.de
Date created: 20.11.2018
'''

import omero
from omero.rtypes import *
import logging
import json
import os
import utilities
import re
from shutil import copy

class AccessRights:
    PRIVATE, READ_ONLY, READ_ANNOTATE, READ_WRITE = range(4)


def getAccessRights(rlobject, conn):
    """ Get Access Rights of ReceptorLight experimental data
        @param rlobject ReceptorLight Object
        @param conn OMERO gateway
    """
    if rlobject is None:
        return AccessRights.PRIVATE

    userIDOfRLObject = rlobject.getOwnerId().getValue()
    userID = conn.getUserId()

    if userIDOfRLObject == userID:
        return AccessRights.READ_WRITE

    return getAccessRightInGroup(userIDOfRLObject, conn)


def getAccessRightInGroup(userIDOfRLObject, conn):
    """ Get Access Rights of ReceptorLight experimental data in the OMERO group
        @param rlobject ReceptorLight Object
        @param conn OMERO gateway
    """
    groupOfRlObject = conn.getDefaultGroup(userIDOfRLObject)

    if groupOfRlObject is None:
        return AccessRights.PRIVATE

    groupPermissionOfRlObject = groupOfRlObject.getDetails().getPermissions()

    groupOfUser = conn.getDefaultGroup(conn.getUserId())
    groupPermissionOfUser = groupOfUser.getDetails().getPermissions()

    if (groupPermissionOfUser.isGroupWrite() and groupPermissionOfRlObject.isGroupWrite()):
        return AccessRights.READ_WRITE

    if (groupPermissionOfUser.isGroupAnnotate() and groupPermissionOfRlObject.isGroupAnnotate()):
        return AccessRights.READ_ANNOTATE

    if (groupPermissionOfUser.isGroupRead() and groupPermissionOfRlObject.isGroupRead()):
        return AccessRights.READ_ONLY

    return AccessRights.PRIVATE


def get_experiment_id_from_dataset(conn, datasetId):
    """ Get experiment id from the dataset with ReceptorLight Service
        @param rlService ReceptorLight Service
        @param datasetId Dataset Id to which the experiment belongs
        @type datasetId Integer
    """
    rlService = utilities.get_receptor_light_service(conn)
    exp = rlService.getExperimentByDatasetId(datasetId)
    if exp:
        if int(exp.getStatus().getValue()) == 1:
            return int(exp.getUId().getValue())
    else:
        return None


def get_metadata_json(type):
    """ Get metadata of ReceptorLight experimental object  and
        load from the file based on the type.
        @param rlobject ReceptorLight Object
        @param conn OMERO gateway
    """
    metadata_file = get_metadata_json_file(type)
    with open(metadata_file) as data_file:
        data = json.load(data_file)
    return data


def get_metadata_json_file(type):
    """ Get the json file of ReceptorLight experimental object based on the type.
        @param type Type of ReceptorLight Object
    """
    model_type = type
    json_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'model'))
    if type.endswith('s'):
        model_type = type[:-1]
    metadata_file = json_path + '/' + model_type + '.json'
    return metadata_file


def get_method_name(key_name):
    """ Get method name of ReceptorLight experimental object based on the key_name
        @param key_name Name of the experiment data
    """
    return 'get' + key_name

def set_method_name(key_name):
    """ Get method name of ReceptorLight experimental object based on the key_name
        @param key_name Name of the experiment data
    """
    return 'set' + key_name


def get_rl_function_name(type):
    """ Get ReceptorLight function name based on the type.
        @param type ReceptorLight Object Type
    """
    return 'get' + type


def save_rl_function_name(type):
    """ Get ReceptorLight function name to save the object based on the type..
        @param type ReceptorLight Object Type
    """
    return 'save' + type


def delete_rl_function_name(type):
    """ Get ReceptorLight function name to delete the object based on the type.
        @param type ReceptorLight Object Type
    """
    return 'delete' + type


def get_create_rl_object_fn(type):
    """ Get ReceptorLight function name to create the object based on the type.
        @param type ReceptorLight Object Type
    """
    return 'create' + type


def get_rl_object(conn, type, id):
    """ Get ReceptorLight object based on the type.
        @param conn OMERO gateway
        @param type ReceptorLight Object Type
        @param id  Unique id of the ReceptorLight Object
    """
    rlService = utilities.get_receptor_light_service(conn)
    rl_function_name = get_rl_function_name(type)
    rlobject = getattr(rlService, rl_function_name)(id)
    return rlobject


def get_rl_object_name(conn, type, id):
    """ Get ReceptorLight object name based on the type.
        @param conn OMERO gateway
        @param type ReceptorLight Object Type
        @param id  Unique id of the ReceptorLight Object
    """
    rlService = utilities.get_receptor_light_service(conn)
    rl_function_name = get_rl_function_name(type)
    rlobject = getattr(rlService, rl_function_name)(id)
    rlobject_name = rlobject.getName().getValue()
    return rlobject_name


def delete_rl_object(conn, type, id):
    """ Delete ReceptorLight object based on the type.
        @param conn OMERO gateway
        @param type ReceptorLight Object Type
        @param id  Unique id of the ReceptorLight Object
    """
    rlService = utilities.get_receptor_light_service(conn)
    rl_function_name = delete_rl_function_name(type)
    delete_used_materials(conn, id)
    return getattr(rlService, rl_function_name)(id)

def delete_used_materials(conn, source_id):
    rlService = utilities.get_receptor_light_service(conn)
    used_materials = rlService.getUsedMaterialsBySourceId(source_id)
    for used_material in used_materials:
        used_material_id = used_material.getUId().getValue()
        if used_material.getTargetType().getValue() == 'RlFileInformation':
            fileId = used_material.getTargetID().getValue()
            fileService = utilities.get_receptor_light_file_service(conn)
            fileService.deleteFile(int(fileId))

        rlService.deleteUsedMaterial(int(used_material_id))


def get_all_exp_materials(conn, type, *args, **kwargs):
    """ Get ReceptorLight object list based on the type.
        @param conn OMERO gateway
        @param type ReceptorLight Object Type
    """
    if 'status' in kwargs:
        status = int(kwargs.get('status', -1))
    rlService = utilities.get_receptor_light_service(conn)
    exp_material_type = type + 's'
    rl_function_name = get_rl_function_name(exp_material_type)
    rlobjects = getattr(rlService, rl_function_name)()
    exp_materials = []
    for rlobject in rlobjects:
        if rlobject.getStatus().getValue() == status:
            exp_material = {}
            exp_material['name'] = rlobject.getName().getValue()
            exp_material['id'] = rlobject.getUId().getValue()
            exp_material['originalid'] = rlobject.getOriginalObjectId().getValue()
            exp_material['access_right'] = getAccessRights(rlobject, conn)
            exp_material['ownername'] = utilities.get_experimenter_name(conn, rlobject.getOwnerId().getValue())
            exp_material['status'] = rlobject.getStatus().getValue()
            if type == 'Experiment':
                exp_material['datasetId'] = rlobject.getDatasetId().getValue()
            exp_materials.append(exp_material)
    return exp_materials


def get_my_proposals(conn, type, *args, **kwargs):
    """ Get ReceptorLight object list based on the type.
        @param conn OMERO gateway
        @param type ReceptorLight Object Type
    """
    if 'status' in kwargs:
        status = int(kwargs.get('status', -1))
    if 'flag' in kwargs:
        flag = int(kwargs.get('flag', -1))
    current_user_id = conn.getUser().getId()
    rlService = utilities.get_receptor_light_service(conn)
    exp_material_type = type + 's'
    rl_function_name = get_rl_function_name(exp_material_type)
    rlobjects = getattr(rlService, rl_function_name)()
    exp_materials = []
    for rlobject in rlobjects:
        if rlobject.getStatus().getValue() == status and rlobject.getOwnerId().getValue() == current_user_id:
            exp_material = {}
            exp_material['name'] = rlobject.getName().getValue()
            exp_material['id'] = rlobject.getUId().getValue()
            exp_material['originalid'] = rlobject.getOriginalObjectId().getValue()
            exp_material['access_right'] = getAccessRights(rlobject, conn)
            exp_material['ownername'] = utilities.get_experimenter_name(conn, rlobject.getOwnerId().getValue())
            exp_material['status'] = rlobject.getStatus().getValue()
            if exp_material['status'] == 2:
                exp_material['status_text'] = 'Proposed'
            elif exp_material['status'] == (1 | 4):
                exp_material['status_text'] = 'Accepted'
            elif exp_material['status'] == 8:
                exp_material['status_text'] = 'Rejected'
            if type == 'Experiment':
                exp_material['datasetId'] = rlobject.getDatasetId().getValue()
            exp_materials.append(exp_material)
    return exp_materials


def get_proposals_on_mine(conn, type, *args, **kwargs):
    """ Get ReceptorLight object list based on the type.
        @param conn OMERO gateway
        @param type ReceptorLight Object Type
    """
    if 'status' in kwargs:
        status = int(kwargs.get('status', -1))
    if 'flag' in kwargs:
        flag = int(kwargs.get('flag', -1))
    current_user_id = conn.getUser().getId()
    rlService = utilities.get_receptor_light_service(conn)
    exp_material_type = type + 's'
    rl_function_name = get_rl_function_name(exp_material_type)
    rlobjects = getattr(rlService, rl_function_name)()
    exp_materials = []
    login_user_exp_ids = get_all_experimentids_of_login_user(conn, type, *args, **kwargs)
    for rlobject in rlobjects:
        if rlobject.getOriginalObjectId().getValue() in login_user_exp_ids and rlobject.getStatus().getValue() in (
                2, 4, 8):
            exp_material = {}
            exp_material['name'] = rlobject.getName().getValue()
            exp_material['id'] = rlobject.getUId().getValue()
            exp_material['originalid'] = rlobject.getOriginalObjectId().getValue()
            exp_material['access_right'] = getAccessRights(rlobject, conn)
            exp_material['ownername'] = utilities.get_experimenter_name(conn, rlobject.getOwnerId().getValue())
            exp_material['status'] = rlobject.getStatus().getValue()
            if exp_material['status'] == 2:
                exp_material['status_text'] = 'Proposed'
            elif exp_material['status'] == 4:
                exp_material['status_text'] = 'Accepted'
            elif exp_material['status'] == 8:
                exp_material['status_text'] = 'Rejected'
            if type == 'Experiment':
                exp_material['datasetId'] = rlobject.getDatasetId().getValue()
            exp_materials.append(exp_material)
    return exp_materials


def execute_proposal_action(conn, input_type, input_id, action_id):
    rlService = utilities.get_receptor_light_service(conn)
    rlobject = get_rl_object(conn, input_type, input_id)
    if int(action_id) == 1:
        rlobject.setStatus(omero.rtypes.rint(4))
    elif int(action_id) == 2:
        rlobject.setStatus(omero.rtypes.rint(8))
    current_user_id = conn.getUser().getId()
    rlobject.setOwnerId(omero.rtypes.rint(current_user_id))
    current_user_group_id = conn.getGroupFromContext().getId()
    rlobject.setOwnerGroupId(omero.rtypes.rint(current_user_group_id))
    save_rl_fn_name = save_rl_function_name(input_type)
    getattr(rlService, save_rl_fn_name)(rlobject)


def get_all_experimentids_of_login_user(conn, type, *args, **kwargs):
    current_user_id = conn.getUser().getId()
    rlService = utilities.get_receptor_light_service(conn)
    exp_material_type = type + 's'
    rl_function_name = get_rl_function_name(exp_material_type)
    rlobjects = getattr(rlService, rl_function_name)()
    rl_obj_ids = []
    for rlobject in rlobjects:
        if rlobject.getOwnerId().getValue() == current_user_id:
            rl_obj_ids.append(rlobject.getUId().getValue())
    return rl_obj_ids


def get_fieldsets_of_type(conn, type):
    rlService = utilities.get_receptor_light_service(conn)
    model_type = 'Rl' + str(type)
    if type == 'RestrictionEnzyme':
        model_type += 's'
    experiment_sections = rlService.uihelpGetSectionsOfType(model_type)
    fieldsets = []
    for section in experiment_sections:
        fields = []
        for element in rlService.uihelpGetElementsOfSections(model_type, section):
            elem_info = rlService.uihelpGetElementInfo(model_type, element)
            if elem_info.getIsVisible().getValue():
                fields.append(element)
        fieldset_values = {"fields": tuple(fields), "classes": ['collapse']}
        fieldsets.append((section, fieldset_values))
    fieldsets = tuple(fieldsets)
    return fieldsets


def get_json_from_server(conn, type):
    """ Get ReceptorLight object data in json based on the type.
        @param conn OMERO gateway
        @param type ReceptorLight Object Type
        @param id  Unique id of the ReceptorLight Object
    """
    rlService = utilities.get_receptor_light_service(conn)
    model_type = 'Rl' + str(type)
    if type == 'RestrictionEnzyme':
        model_type += 's'
    experiment_sections = rlService.uihelpGetSectionsOfType(model_type)
    rl_function_name = get_rl_function_name(type)

    experiment_object = {}
    for section in experiment_sections:
        experiment_object[section] = []
        for element in rlService.uihelpGetElementsOfSections(model_type, section):
            elem_info = rlService.uihelpGetElementInfo(model_type, element)
            e = {}
            e['key'] = element
            e['name'] = elem_info.getUiName().getValue()
            e['help'] = elem_info.getUiHelp().getValue()
            e['index'] = elem_info.getIndex().getValue()
            e['isVisible'] = elem_info.getIsVisible().getValue()
            experiment_object[section].append(e)
    return experiment_object


def get_sections_from_model(conn, type):
    rlService = utilities.get_receptor_light_service(conn)
    model_type = 'Rl' + str(type)
    if type == 'RestrictionEnzyme':
        model_type += 's'
    sections = rlService.uihelpGetSectionsOfType(model_type)
    return sections


def get_json(conn, type, id):
    """ Get ReceptorLight object data in json based on the type.
        @param conn OMERO gateway
        @param type ReceptorLight Object Type
        @param id  Unique id of the ReceptorLight Object
    """
    rlService = utilities.get_receptor_light_service(conn)
    model_type = 'Rl' + str(type)
    if type == 'RestrictionEnzyme':
        model_type += 's'
    metadata_json_data = get_metadata_json(type)
    rl_function_name = get_rl_function_name(type)
    rlobject = getattr(rlService, rl_function_name)(id)

    experiment_object = {}
    for section in metadata_json_data:
        experiment_object[section] = []
        for data in metadata_json_data[section]:
            e = {}
            e['key'] = data['key']
            e['name'] = data['name']
            e['help'] = data['help']
            e['index'] = data['index']
            e['isVisible'] = data['isVisible']
            e['uiType'] = data['uiType']
            if 'unit' in data:
                e['unit'] = data['unit']
            if data['uiType'] == 'weblink' and 'linkType' in data:
                e['linkType'] = data['linkType']
            method_name = 'get' + data['key']

            val = getattr(rlobject, method_name)()
            if hasattr(val, 'getValue'):
                value = val.getValue()
                # if data['key'] == 'ContactPerson':
                #     if isinstance(value, int):
                #         e['value'] = utilities.get_experimenter_name(conn, value)
                #     else:
                #         e['value'] = value
                if data['uiType'] == 'file':
                    fileService = utilities.get_receptor_light_file_service(conn)
                    if value:
                        fileInfo = fileService.getFileInformation(int(value))
                        if fileInfo:
                            e['value'] = str(fileInfo.getName().getValue())
                            e['fileId'] = int(value)
                else:
                    e['value'] = value if value else None
            if hasattr(val, 'copyValues'):
                val_list = val.copyValues()
                if data['uiType'] == 'multiplefiles':
                    fileService = utilities.get_receptor_light_file_service(conn)
                    e['value'] = {}
                    for v in val_list:
                        if v:
                            fileInfo = fileService.getFileInformation(int(v.getValue().getValue()))
                            if fileInfo:
                                e['value'][int(v.getValue().getValue())] = (str(fileInfo.getName().getValue()))
            if hasattr(val, '__class__'):
                value = val.__class__
                e['type'] = str(value)

            experiment_object[section].append(e)
    return experiment_object


def get_history(conn, type, id):
    """ Get history information of ReceptorLight object based on the type.
        @param conn OMERO gateway
        @param type ReceptorLight Object Type
        @param id  Unique id of the ReceptorLight Object
    """
    rlService = utilities.get_receptor_light_service(conn)
    metadata_json_data = get_metadata_json(type)
    rl_function_name = get_rl_function_name(type)
    rlobject = getattr(rlService, rl_function_name)(id)
    versions = [rlobject]
    parent_ids_list = get_all_parents_of_rlobject(rlService, rl_function_name, rlobject, versions)
    rlobject_versions = []
    if not parent_ids_list:
        parent_ids_list = versions
    for rlobject in parent_ids_list:
        if rlobject:
            history = {}
            history['name'] = rlobject.getName().getValue()
            history['id'] = rlobject.getUId().getValue()
            history['creation_time'] = rlobject.getCreationDateTime().getValue()
            history['ownername'] = utilities.get_experimenter_name(conn, rlobject.getOwnerId().getValue())
            rlobject_versions.append(history)
    return rlobject_versions


def get_difference_of_rlobjects(conn, type, id1, id2):
    rlService = utilities.get_receptor_light_service(conn)
    model_type = 'Rl' + str(type)
    if type == 'RestrictionEnzyme':
        model_type += 's'
    metadata_json_data = get_metadata_json(type)
    rl_function_name = get_rl_function_name(type)
    rlobject1 = getattr(rlService, rl_function_name)(id1)
    rlobject2 = getattr(rlService, rl_function_name)(id2)

    experiment_object = {}
    for section in metadata_json_data:
        experiment_object[section] = []
        for data in metadata_json_data[section]:
            e = {}
            e['key'] = data['key']
            e['name'] = data['name']
            e['help'] = data['help']
            e['index'] = data['index']
            e['isVisible'] = data['isVisible']
            e['uiType'] = data['uiType']
            if data['uiType'] == 'weblink' and 'linkType' in data:
                e['linkType'] = data['linkType']
            method_name = 'get' + data['key']

            val1 = getattr(rlobject1, method_name)()
            val2 = getattr(rlobject2, method_name)()

            e['value1'] = get_element_value(conn, val1, data)
            e['value2'] = get_element_value(conn, val2, data)
            if hasattr(val1, '__class__'):
                value = val1.__class__
                e['type'] = str(value)

            experiment_object[section].append(e)
    return experiment_object


def get_element_value(conn, value, data):
    elem_value = None
    if hasattr(value, 'getValue'):
        value = value.getValue()
        if data['uiType'] == 'file':
            fileService = utilities.get_receptor_light_file_service(conn)
            if value:
                fileInfo = fileService.getFileInformation(int(value))
                if fileInfo:
                    elem_value = str(fileInfo.getName().getValue())
        else:
            elem_value = value if value else None
        return elem_value


def get_all_parents_of_rlobject(rlService, rl_function_name, rlobject, versions):
    """ Get ReceptorLight object's parent ids.
        A method that recursively finds all versions of an rlobject.
        @param rlService ReceptorLight Service
        @param rl_function_name ReceptorLight Function Name
        @param rlobject ReceptorLight Object
        @param versions Different versions of rlobject
    """
    if rlobject:
        id = rlobject.getOriginalObjectId().getValue()
        if id == 0:
            return None
        else:
            rlobject = getattr(rlService, rl_function_name)(id)
            versions.append(rlobject)
            get_all_parents_of_rlobject(rlService, rl_function_name, rlobject, versions)
            return versions

def create_new_from_parent_rlobject(conn, type, rlobject, *args, **kwargs):
    if 'rl_obj_name' in kwargs:
        rl_obj_name = str(kwargs.get('rl_obj_name', ''))
    if rl_obj_name == '':
        rl_obj_name = rlobject.getName().getValue()
    rlService = utilities.get_receptor_light_service(conn)
    create_rl_object_fn = get_create_rl_object_fn(type)
    new_rlobject = getattr(rlService, create_rl_object_fn)(rl_obj_name)
    new_rlobject_id = new_rlobject.getUId().getValue()
    new_rlobject_creation_time = new_rlobject.getCreationDateTime().getValue()
    new_rlobject_owner_id = new_rlobject.getOwnerId().getValue()
    new_rlobject_owner_group_id = new_rlobject.getOwnerGroupId().getValue()
    rl_object_keys = getattr(rlService, 'getMemberNames')(new_rlobject)

    if rlobject:
        rl_object_id = rlobject.getUId().getValue()
        for rl_obj_key in rl_object_keys:
            set_fn = 'set' + rl_obj_key
            get_fn = 'get' + rl_obj_key
            rlobject_value = getattr(rlobject, get_fn)()
            getattr(new_rlobject, set_fn)(rlobject_value)
        new_rlobject.setUId(omero.rtypes.rint(new_rlobject_id))
        new_rlobject.setCreationDateTime(omero.rtypes.rstring(new_rlobject_creation_time))
        new_rlobject.setOwnerId(omero.rtypes.rint(new_rlobject_owner_id))
        new_rlobject.setOwnerGroupId(omero.rtypes.rint(new_rlobject_owner_group_id))
        used_materials = rlService.getUsedMaterialsBySourceId(rl_object_id)
        for used_material in used_materials:
            source_id = new_rlobject_id
            source_type = used_material.getSourceType().getValue().getValue()
            target_id = used_material.getTargetID().getValue()
            target_type = used_material.getTargetType().getValue().getValue()
            used_in_step = used_material.getUsedIn().getValue()
            add_to_used_material(conn, source_id, source_type, target_id, target_type, used_in_step)
    return new_rlobject

def save_rlobject_types(conn, new_rlobject_id, type, changed_dict, *args, **kwargs):
    if 'files' in kwargs:
        rl_files = kwargs.get('files', '')
    if 'root_folder_id' in kwargs:
        root_folder_id = int(kwargs.get('root_folder_id', -1))
    metadata_json_data = get_metadata_json(type)
    rlService = utilities.get_receptor_light_service(conn)
    new_rlobject = get_rl_object(conn, type, new_rlobject_id)
    for key, value in changed_dict.items():
        for categories in metadata_json_data:
            for data in metadata_json_data[categories]:
                if data['key'] == key:
                    if value:
                        if data['uiType'] == 'file':
                            for filename, file in rl_files.iteritems():
                                if filename == data['key'] and rl_files[filename]:
                                    if type == 'Experiment':
                                        omero_value_object = save_file_information(conn, rl_files[filename], data['key'],
                                                                      root_folder_id=root_folder_id,
                                                                      input_id=new_rlobject_id, input_type=type)
                                    else:
                                        omero_value_object = save_file_information(conn, rl_files[filename], data['key'],
                                                                      input_id=new_rlobject_id, input_type=type)
                        elif data['uiType'] == 'multiplefiles':
                            if type == 'Experiment':
                                omero_value_object = save_multiple_files(conn, rl_files, data['key'],
                                                                         root_folder_id=root_folder_id, input_id=new_rlobject_id, input_type=type)
                            else:
                                omero_value_object = save_multiple_files(conn, rl_files, data['key'], input_id=new_rlobject_id, input_type=type)
                        elif data['uiType'] == 'richText':
                            if type == 'Experiment':
                                omero_value_object = save_richText(conn, rl_files, value, data['key'],
                                                                   root_folder_id=root_folder_id, input_id=new_rlobject_id, input_type=type)
                            else:
                                omero_value_object = save_richText(conn, rl_files, value, data['key'], input_id=new_rlobject_id, input_type=type)
                        else:
                            omero_value_object = convert_value_to_omero_value(value, data['type'], data['uiType'],
                                                                              data['key'], conn)
                        function_name = convert_type_to_function(data['type'])
                        try:
                            if data['type'] == 'omero.rtypes.RDoubleI':
                                set_fn = 'set' + data['key']
                                getattr(new_rlobject, set_fn)(omero_value_object)
                            else:
                                new_rlobject = getattr(rlService, function_name)(new_rlobject, key, omero_value_object)
                        except Exception as e:
                            logging.info("Exception:(%s)", e)
                            return 0
    return new_rlobject


def save_rl_object(conn, type, changed_dict, form_data, *args, **kwargs):
    """ Save information of ReceptorLight object based on the type.
        @param conn OMERO gateway
        @param type ReceptorLight Object Type
        @param changed_dict  Changed information
        @param form_data the Form data
        @param args Args
        @param kwargs Request Args
    """
    try:
        save_rl_fn_name = save_rl_function_name(type)
        rlService = utilities.get_receptor_light_service(conn)
        parent_rlobject_id = None
        new_rlobject_id = None
        rlobject = None
        action = ''
        root_folder_id = -1
        if 'action' in kwargs:
            action = str(kwargs.get('action', ''))
        if 'input_name' in kwargs:
            rl_obj_name = str(kwargs.get('input_name', ''))
        if 'id' in kwargs:
            input_id = int(kwargs.get('id', -1))
        if input_id != -1:
            rlobject = get_rl_object(conn, type, input_id)
            parent_rlobject_id = rlobject.getUId()
            if type == 'Experiment':
                root_folder_id = rlobject.getRootFolderId().getValue()
                parent_datasetId = rlobject.getDatasetId().getValue()
            if action == '':
                rlobject.setStatus(omero.rtypes.rint(0))
                getattr(rlService, save_rl_fn_name)(rlobject)
        if 'files' in kwargs:
            rl_files = kwargs.get('files', '')
        new_rlobject = create_new_from_parent_rlobject(conn, type, rlobject, rl_obj_name=rl_obj_name)
        new_rlobject_id = new_rlobject.getUId().getValue()
        if type == 'Experiment':
            if input_id == -1:
                root_folder_id = getCreateRootFolder(conn, new_rlobject_id)
            new_rlobject.setRootFolderId(omero.rtypes.rint(root_folder_id))
        getattr(rlService, save_rl_fn_name)(new_rlobject)
        new_rlobject = save_rlobject_types(conn, new_rlobject_id, type, changed_dict, root_folder_id=root_folder_id, files=rl_files)

        if input_id != -1 and type == 'Experiment':
            new_rlobject.setDatasetId(omero.rtypes.rint(parent_datasetId))
        if parent_rlobject_id:
            new_rlobject.setOriginalObjectId(parent_rlobject_id)
        if action == 'propose':
            new_rlobject.setStatus(omero.rtypes.rint(2))
        else:
            new_rlobject.setStatus(omero.rtypes.rint(1))
        getattr(rlService, save_rl_fn_name)(new_rlobject)
        return 1
    except Exception as e:
        logging.info("Exception:(%s)", e)
        if new_rlobject_id:
            delete_rl_object(conn, type, new_rlobject_id)
        if rlobject:
            rlobject.setStatus(omero.rtypes.rint(1))
            getattr(rlService, save_rl_fn_name)(rlobject)
        return 0


def save_multiple_files(conn, rl_files, key, *args, **kwargs):
    intValList = omero.model.IntValueListI()
    for file in rl_files.getlist(key):
        if file:
            value = save_file_information(conn, file, key, *args, **kwargs)
            intVal = omero.model.IntValueI()
            intVal.setValue(omero.rtypes.rint(value))
            intValList.addIntValue(intVal)
    return intValList

def save_notebook(conn, newFileId, value, key, *args, **kwargs):
    user = conn.getUser()
    user_id = user.getId()
    user_name = user.getName()
    homePath = os.path.expanduser("~")
    user_directory = homePath + '/jupyternotebooks/' + str(user_id) + '_' + str(user_name)
    if not (os.path.isdir(user_directory)):
        os.mkdir(user_directory, 0755)

    originalFilePath = homePath + '/OMERO.data/RL_FILES/' + str(newFileId) + '_' + value.name
    copy(originalFilePath, user_directory)

def save_file_information(conn, value, key, *args, **kwargs):
    root_folder_id = -1
    fileService = utilities.get_receptor_light_file_service(conn)
    newFileId = fileService.createFile(value.name)
    if newFileId > 0:
        fileService.openFile(newFileId, True)
        for chunk in value.chunks():
            fileService.appendFileData(newFileId, chunk)
        newFileInfo = fileService.getFileInformation(newFileId)
        new_file_type = newFileInfo.getFileType()
        new_file_type.setValue(omero.rtypes.rstring("ReceptorLightFile"))
        newFileInfo.setFileType(new_file_type)
        fileService.setFileInformation(newFileId, newFileInfo)

        # adding the new files to the root folder of the experiment
        if 'root_folder_id' in kwargs:
            root_folder_id = int(kwargs.get('root_folder_id', -1))
            if root_folder_id != -1:
                parentFileInfo = fileService.getFileInformation(int(root_folder_id))
                oId = omero.model.IntValueI(1)
                oId.Value = omero.rtypes.rint(newFileId)

                parentFileInfo.getSubFileIds()._getValues().append(oId)
                fileService.setFileInformation(int(root_folder_id), parentFileInfo)

        if newFileId != -1:
            fileService.closeFile(newFileId)
        if str(value.name).endswith(".ipynb"):
            save_notebook(conn, newFileId, value, key, *args, **kwargs)
        if 'input_id' in kwargs and 'input_type' in kwargs:
            source_id = int(kwargs.get('input_id', -1))
            source_type = str(kwargs.get('input_type', ''))
            used_material = add_to_used_material(conn, source_id, source_type, newFileId, "RlFileInformation", key)
        return newFileId


def add_to_used_material(conn, source_id, source_type, target_id, target_type, used_in_step):
    rlService = utilities.get_receptor_light_service(conn)
    used_material = rlService.createUsedMaterial()
    source_type = get_used_material_type(source_type)

    used_material.setSourceID(omero.rtypes.rint(source_id))

    st = used_material.getSourceType()
    st.setValue(omero.rtypes.rstring(source_type))
    used_material.setSourceType(st)

    used_material.setTargetID(omero.rtypes.rint(target_id))
    tt = used_material.getTargetType()
    tt.setValue(omero.rtypes.rstring(target_type))
    used_material.setTargetType(tt)

    used_material.setUsedIn(omero.rtypes.rstring(used_in_step))
    return rlService.saveUsedMaterial(used_material)


def get_used_material_type(type):
    if 'Rl' in type:
        return type
    else:
        return 'Rl' + type


def convert_type_to_function(type):
    """ Get function name from the type to save the rlobject.
        @param type ReceptorLight Object Type
    """
    function_name = None
    if type == 'string' or type == 'omero.rtypes.RStringI':
        function_name = 'setMemberStringValue'
    elif type == 'int' or type == 'double' or type == 'omero.rtypes.RIntI' or type == 'omero.rtypes.RDoubleI':
        function_name = 'setMemberIntValue'
    elif type == 'ome.model.core.StringValueList' or type == 'ome.model.core.IntValueList' or type == 'omero.model.IntValueListI':
        function_name = 'setMemberIObjectValue'
    else:
        function_name = None
    return function_name


def save_richText(conn, rl_files, value, key, *args, **kwargs):
    root_folder_id = -1
    source_id = -1
    source_type = "UNKNOWN"
    if 'root_folder_id' in kwargs:
        root_folder_id = int(kwargs.get('root_folder_id', -1))
    if 'input_id' in kwargs and 'input_type' in kwargs:
        source_id = int(kwargs.get('input_id', -1))
        source_type = str(kwargs.get('input_type', ''))
    intValList = omero.model.IntValueListI()
    text_value = value[0]
    for file in rl_files.getlist(key + '_1'):
        if file:
            newFileId = save_file_information(conn, file, key, root_folder_id=root_folder_id)
            rl_object_pattern = "<<File:-1:" + file.name + ">>"
            regex = re.compile(rl_object_pattern)
            replc = "<<File:" + str(newFileId) + ":" + file.name + ">>"
            if isinstance(text_value, str):
                text_value = text_value.decode('utf-8')
            text_value = re.sub(regex, replc, text_value)
    get_used_materials_from_richtext(conn, text_value, source_id, source_type, key)
    if isinstance(text_value, str):
        return text_value.encode('utf-8')
    else:
        return text_value


def get_used_materials_from_richtext(conn, value, source_id, source_type, key):
    rl_object_pattern = "<<(.*?)>>"
    matches = re.compile(rl_object_pattern).findall(value)
    for match in matches:
        t=match.split(':')
        if len(t) == 3:
            if t[0] == 'File':
                used_material = add_to_used_material(conn, source_id, source_type, t[1], "RlFileInformation", key)
            else:
                model_type = t[0]
                if model_type.endswith('s'):
                    model_type = model_type[:-1]
                if model_type == 'RnaAmplifications' or model_type == 'RnaAmplification':
                    model_type = 'Rna'
                if model_type == 'DnaAmplifications' or model_type == 'DnaAmplification':
                    model_type = 'Dna'
                if model_type == 'Chemicals' or model_type == 'Chemical':
                    model_type = 'ChemicalSubstance'
                used_material = add_to_used_material(conn, source_id, source_type, t[1], get_used_material_type(model_type), key)


def convert_value_to_omero_value(value, type, uiType, key, conn):
    """ Get Value of each key of the rlobject and convert to a value so that it can be saved.
        @param value Value of the Key
        @param type ReceptorLight Object Type
    """
    if type == 'ome.model.core.StringValueList':
        strVal = omero.model.StringValueI()
        strVal.setValue(omero.rtypes.rstring(value))
        strValList = omero.model.StringValueListI()
        strValList.addStringValue(strVal)
        return strValList
    elif type == 'int' or type == 'omero.rtypes.RIntI':
        return int(value) if value else value
    elif type == 'double' or type == 'omero.rtypes.RDoubleI':
        return omero.rtypes.rdouble(value) if value else value

    elif type == 'ome.model.core.IntValueList' or type == 'omero.model.IntValueListI':
        intVal = omero.model.IntValueI()
        intVal.setValue(omero.rtypes.rint(value))
        intValList = omero.model.IntValueListI()
        intValList.addIntValue(intVal)
        return intValList
    elif uiType == 'date' or uiType == 'time':
        return str(value)
    elif uiType == 'dropdown':
        ids = ''
        for val in value:
            ids = ids + val + ','
        return ids[:-1]
    elif type == 'string' or type == 'omero.rtypes.RStringI':
        return value.encode('utf-8')
    else:
        return value


def convertRList(list):
    """ Convert the value from the list
        @param list list of values
    """
    # result = []
    for val in list:
        return val.getValue().getValue()
        # result.append(val.getValue().getValue())
        # return result


def get_options(conn, type):
    """ Get options of ReceptorLight object
        @param conn OMERO gateway
        @param type ReceptorLight Object Type
    """
    rlService = utilities.get_receptor_light_service(conn)
    exp_material_type = type + 's'
    rl_function_name = get_rl_function_name(exp_material_type)
    rlobjects = getattr(rlService, rl_function_name)()
    exp_materials = {}
    for rlobject in rlobjects:
        if rlobject.getStatus().getValue() == 1:
            exp_materials[rlobject.getUId().getValue()] = rlobject.getName().getValue()
    return exp_materials


def get_all_exp_materials_choices(conn):
    """ Get options of ReceptorLight object
        @param conn OMERO gateway
    """
    rlService = utilities.get_receptor_light_service(conn)
    exp_material_types = ['Proteins', 'Plasmids', 'Vectors', 'Dnas', 'Rnas', 'ChemicalSubstances', 'Solutions', 'FluorescentProteins', 'RestrictionEnzymes', 'Oligonucleotides', 'Sops']
    all_exp_materials_choices = {}
    for exp_material_type in exp_material_types:
        rl_function_name = get_rl_function_name(exp_material_type)
        rlobjects = getattr(rlService, rl_function_name)()
        exp_materials = {}
        for rlobject in rlobjects:
            if rlobject.getStatus().getValue() == 1:
                exp_materials[rlobject.getUId().getValue()] = rlobject.getName().getValue()
        all_exp_materials_choices[exp_material_type[:-1]] = exp_materials
    return all_exp_materials_choices


def get_all_experimenters(conn):
    """ Get options of ReceptorLight object
        @param conn OMERO gateway
    """
    experimenterList = utilities.get_experimenters_list(conn)
    all_experimenter_choices = []
    for experimenter in experimenterList:
        all_experimenter_choices.append((experimenter.id, experimenter.getFullName()))
    return all_experimenter_choices


def get_rlobject_name_value_from_class_type(conn, type, id):
    """ Get name of the ReceptorLight project
        @param conn OMERO gateway
        @param type ReceptorLight Object Type
        @param id Unique id of the ReceptorLight Project
    """
    rl_object = get_rl_object(conn, type, id)
    name = rl_object.getName().getValue()
    return name


def get_search_results(conn, search_query):
    """ Get search results based on the search query.
        @param conn OMERO gateway
        @param search_query Search Query
    """
    rlSearchService = utilities.get_receptor_light_search_service(conn)
    search_results = rlSearchService.search(search_query)
    search_results_json = get_search_results_json(search_results)
    return search_results_json


def get_search_results_json(search_results):
    """ Get search results based on the search query in json
        @param search_results Search Results from the ReceptorLight Search Service
    """
    result_json = []
    for result in search_results:
        json_obj = {}
        if result.getStatus().getValue() == 1:
            json_obj['name'] = result.getName().getValue()
            json_obj['id'] = result.getUId().getValue()
            json_obj['type'] = (result.getTypeName().getValue()).title()
            json_obj['found_in'] = result.getMemberName().getValue()
            result_json.append(json_obj)
    return result_json


def getCreateRootFolder(conn, expId):
    fileService = utilities.get_receptor_light_file_service(conn)
    rootId = -1
    if fileService is not None:
        rootId = fileService.createFile("Root")
        if rootId > 0:
            # root must be a folder
            fileInfo = fileService.getFileInformation(rootId)
            if fileInfo is not None:
                ft = fileInfo.getFileType()
                ft.setValue(omero.rtypes.rstring("Folder"))
                fileInfo.setFileType(ft)
                fileService.setFileInformation(rootId, fileInfo)
    return rootId


# def get_choice_id_name_by_type(conn, rl_type):
#     """ Get options of ReceptorLight object
#         @param conn OMERO gateway
#     """
#     rlService = utilities.get_receptor_light_service(conn)
#     all_choices = {}
#     rl_function_name = get_rl_function_name(rl_type)
#     rlobjects = getattr(rlService, rl_function_name)()
#     all_choices = {}
#     for rlobject in rlobjects:
#         if rlobject.getStatus().getValue() == 1:
#             all_choices[rlobject.getUId().getValue()] = rlobject.getName().getValue()
#     return all_choices
