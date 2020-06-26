from collections import OrderedDict, defaultdict
from librec_auto.util import Files, utils, build_parent_path, xml_load_from_path
from lxml import etree
import copy
import logging
import itertools

# 2020-06-25 RB All new implementation


class LibrecTranslation:

    __instance = None

    def __new__(cls, files):
        if LibrecTranslation.__instance is None:
                LibrecTranslation.__instance = object.__new__(cls)
        return LibrecTranslation.__instance

    def __init__(self, files):
        self.read_rules(files)

    def read_rules(self, files):
        rules_path = self.files.get_rules_path()
        if (rules_path.exists()):
            rules_input = xml_load_from_file(rules_path)
            return rules_input
        else:
            return None

class LibrecProperties:

    def __init__(self, xml):
        self.properties = None
        self._xml_input = None
        self._rules_input = None
        self._xml_input = xml
        self.process_xml()

    def process_xml(self):
        logging.warning('Not implemented yet.')
        return None


# 2019-11-25 RB Configuration elements that aren't passed to LibRec are left in original XML format and handled
# later in a command-specific way. A better way might be to have "handler" mechanism so that each command can
# be associated its own configuration element and have code that is called when that element is encountered in the
# parse. Something to think about.
# def get_unparsed(self, type):
#    if type in self._unparsed:
#        return self._unparsed[type]
#    else:
#        None

# def get_rules_dict(self):
#    return self._rules_dict



# def process_config(self):
#     if type(self._xml_input) is etree.ElementTree:
#         if type(self._rules_dict) is etree.ElementTree:
#             self.process_aux(self._xml_input.xpath('librec-auto'),
#                              self._rules_dict.xpath('librec-auto-element-rules'))
#             self.compute_value_tuples()
#             self.ensure_sub_experiments()
#         else:
#             logging.error(f"Error processing element rules. Filename: {self._files.get_rules_path().as_posix()}")
#     else:
#         logging.error(f"Error processing configuration file. Filename: {self._files.get_config_path().as_posix()}")
#
# def process_aux(self, arg, rules):
#     for key in arg:
#         if key in rules:                                # If the entry corresponds to a rule
#             if "@action" in rules[key] and rules[key]['@action'] == 'no-parse': # If labeled "no parse"
#                 self._unparsed[key] = arg[key]          # Add to unparsed collection
#             elif type(arg[key]) is OrderedDict:         # If the config file has subelements
#                 if type(rules[key]) is OrderedDict:     # If the rules also have subelements
#                     self.process_aux(arg[key], rules[key]) # recursive call
#                 elif type(rules[key]) is list:          # If the rules have a list
#                     self._prop_dict = self.process_attr(arg[key], rules[key])  # We have an attribute
#                 elif 'value' in arg[key]:               # If the config file has a 'value' key
#                     self._var_data[rules[key]] = arg[key]['value'] # then we have variable data for multiple exps.
#             elif key in rules:                          # Config file doesn't have subelements
#                 if type(arg[key]) is list:              # Some properties have comma-separated values
#                     self._prop_dict[rules[key]] = ','.join(arg[key])
#                 elif type(rules[key]) == list:          # There are multiple LibRec keys in which map to this
#                     # LibRecAuto key. (e.g. 'l1-reg')
#                     for libRecKey in rules[key]:
#                         if type(libRecKey) is str:            # Otherwise, it is a compound rule that doesn't match arg
#                             self._prop_dict[libRecKey] = arg[key]
#                 else:
#                     self._prop_dict[rules[key]] = arg[key]  # Set property translation and value
#         # If the key isn't in the rules, ignore it but warn because it is probably an error.
#         else:
#             logging.warning("Key {} is not in element rules.", key)
#
#     return
#
# def get_string_rule(self, attr_rule):
#     for item in attr_rule:
#         if type(item) is str:
#             return item
#     return None
#
# # Assumes attribute name is first in ordered dictionary.
# def collect_attributes(self, attr_rule):
#     return [(list(item.keys())[0], item['#text'])
#             for item in attr_rule if type(item) is OrderedDict]
#
# def process_attr(self, elem, attr_rule):
#     # Scan rule for string
#     # Associate with elem #text
#     string_rule = self.get_string_rule(attr_rule)
#     if 'value' in elem:                             # Variable rules
#         self._var_data[string_rule] = elem['value']
#     else:
#         self._prop_dict[string_rule] = elem['#text']
#     # Scan rule for all attributes
#     # Assign
#     attrib_pairs = self.collect_attributes(attr_rule)
#     for attr_pair in attrib_pairs:
#         self._prop_dict[attr_pair[1]] = elem[attr_pair[0]]
#     return self._prop_dict
#
#     # TODO RB 2019-12-12 Should include some error-checking and better messages for badly-formed XML
#     def collect_scripts(self, script_type):
#         post_xml = self.get_unparsed(script_type)
#         script_xml = post_xml['script']
#         scripts = []
#         for entry in utils.force_list(script_xml):
#             script_path = utils.get_script_path(entry, script_type)
#             if 'param' in entry:
#                 param_dict = {}
#                 for elem_dict in utils.force_list(entry['param']):
#                     param_dict[elem_dict['@name']] = elem_dict['#text']
#                 scripts.append((script_path, param_dict))
#             else:
#                 scripts.append((script_path, None))
#
#         return scripts
#
#
#     def compute_value_tuples(self):
#         self.var_params = self._var_data.keys()
#         original_var_values = list(self._var_data.values())
#         if (len(original_var_values) == 1):
#             original_var_values = original_var_values[0]
#         var_values = []
#         for element in original_var_values:
#             if type(element) is list:
#                 # print(element)
#                 var_values.append(element)
#             else:
#                 var_values.append([element])
#         if len(self.var_params) == 1:
#             self._value_tuples = var_values
#         else:
#             self._value_tuples = list(itertools.product(*var_values))
#