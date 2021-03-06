from collections import OrderedDict, defaultdict
from librec_auto.core.util import Files, utils, build_parent_path, LibrecProperties, \
    xml_load_from_path, Library, LibraryColl, merge_elements, VarColl
from librec_auto.core.util.xml_utils import single_xpath
from lxml import etree
import copy
import logging
from pathlib import Path
from librec_auto.core.config_lib import ConfigLibCollection, ConfigLib
import re


class ConfigCmd:
    """
    Loads the configuration file, inserts appropriate library contents,
    identifies the parameter variations and creates separate configurations
    for all combinations.
    """

    _PARAM_NAME_PATH_RE = ".+\[@name='(.+)'\]"

    def __init__(self, config_file, target):

        self._files = Files()
        self._target = target

        self._files.set_study_path(target)
        self._files.set_config_file(config_file)

        self._xml_input = self.read_xml(self._files.get_config_file_path())
        #self._var_librec_data = defaultdict(list)
        #self._var_rerank_data = defaultdict(list)
        #self._var_params = []
        #self._var_tuples = []
        self._var_coll = VarColl()
        self._libraries = LibraryColl()

        self._key_password = None

    def get_target(self):
        return self._target

    def set_target(self, target):
        self._target = target

    def get_xml(self):
        return self._xml_input

    # def get_var_data(self):
    #     return self._var_data

    def get_key_password(self):
        return self._key_password

    def set_key_password(self, pw):
        self._key_password = pw

    def get_value_conf(self, subexp_no):
        return self._var_coll.var_confs[subexp_no]

    def get_sub_exp_count(self):
        exp_count = len(self._var_coll.var_confs)
        if exp_count == 0:
            return 1
        else:
            return exp_count

    def get_files(self):
        return self._files

    def read_xml(self, path_str):
        path = self._files.get_config_file_path()
        if (path.exists()):
            xml_input = xml_load_from_path(path)
            return xml_input
        else:
            return None

    def ensure_experiments(self):
        exp_count = len(self._var_coll.var_confs)
        if exp_count == 0:
            exp_count = 1
        self.get_files().ensure_exp_paths(exp_count)

    def load_libraries(self):
        lib_paths = []
        lib_elems = self._xml_input.xpath('/librec-auto/library')
        for elem in lib_elems:
            self._libraries.add_lib(
                Library(elem.text, elem.get('src'), self._files))

    # Process config takes the config file and produces a dictionary of the following form:
    # xpath-string => list of values
    # or xpath-string => (range-to, range-from) pair
    # Right now, we will assume the first
    def process_config(self):
        self._var_data = defaultdict(list)
        self.substitute_library()
        self.collect_vars()
        self.ensure_experiments()
        # self.label_repeats()

    # Have to wait to writes experiment-specific XML configurations to each exp directory
    # in case a purge is happening.
    def setup_exp_configs(self):
        self.write_exp_configs()

    def substitute_library(self):
        ref_elems = self._xml_input.xpath('//*[@ref]')
        for ref_elem in ref_elems:
            ref_name = ref_elem.get('ref')
            named_elem = self._libraries.get_elem(ref_name)
            if named_elem is not None:
                merged_elem = merge_elements(named_elem, ref_elem)
                ref_elem.getparent().replace(ref_elem, merged_elem)
            else:
                logging.warning(f"No such element in library {ref_name}")

    def collect_vars(self):
        self.collect_librec_vars()
        self.collect_rerank_vars()
        self._var_coll.compute_var_configurations()

    def collect_librec_vars(self):
        value_elems = self._xml_input.xpath(
            '/librec-auto/*[not(self::rerank)]/*/value')
        parents = [elem.getparent() for elem in value_elems]
        parents = list(set(parents))
        for parent in parents:
            vals = [elem.text for elem in parent.iterchildren(tag='value')]
            parent_path = build_parent_path(parent)
            self._var_coll.add_var('librec', parent_path, vals)

    def collect_rerank_vars(self):
        value_elems = self._xml_input.xpath('/librec-auto/rerank/*//value')
        parents = [elem.getparent() for elem in value_elems]
        parents = list(set(parents))
        for parent in parents:
            vals = [elem.text for elem in parent.iterchildren(tag='value')]
            parent_path = build_parent_path(parent)
            self._var_coll.add_var('rerank', parent_path, vals)

    # Write versions of the config file in which the parameters with multiple values are replaced with
    # a single value
    def write_exp_configs(self):
        configs = list(
            zip(self.get_files().get_exp_paths_iterator(),
                iter(self._var_coll.var_confs)))
        i = 0
        for exp, vconf in configs:
            vconf.exp_no = i
            vconf.exp_dir = exp.exp_name
            self.write_exp_config(exp, vconf)

    def write_exp_config(self, exp, vconf):
        new_xml = copy.deepcopy(self._xml_input)
        # Remove libraries. All substitutions have already happened.
        for lib in new_xml.xpath('/librec-auto/library'):
            lib.getparent().remove(lib)

        pat = re.compile(ConfigCmd._PARAM_NAME_PATH_RE)
        for vinfo in vconf.vars:
            var_elem = new_xml.xpath(vinfo.path)[0]
            var_elem.clear()
            var_elem.text = str(vinfo.val)
            var_elem.set("var", "true")
            if var_elem.tag == 'param':  # params are distinguished by name attributes
                mat = pat.match(vinfo.path)
                var_elem.attrib['name'] = mat.group(1)
        new_xml.append(
            etree.Comment(
                'This configuration file was automatically generated by librec-auto. '
                +
                'Editing may produce unpredictable results and is not recommended.'
            ))
        outpath = exp.get_path('conf') / Files.DEFAULT_CONFIG_FILENAME
        logging.info('Writing config file ' + str(outpath))
        new_xml.getroottree().write(outpath.absolute().as_posix(),
                                    pretty_print=True)

        if vconf.ref_config is None:
            props = LibrecProperties(new_xml, self._files)
            exp.add_to_config(props.properties, 'result')
            props.save(exp)
        else:
            path = exp.get_ref_exp_flag_path()
            with path.open(mode='w') as fh:
                fh.write(vconf.ref_config.exp_dir)
                fh.write('\n')

    def has_rerank(self):
        rerank_elems = self._xml_input.xpath('/librec-auto/rerank')
        return len(rerank_elems) > 0

    def has_post(self):
        post_elems = self._xml_input.xpath('/librec-auto/post')
        return len(post_elems) > 0

    def cross_validation(self):
        model_elem = single_xpath(self._xml_input, '/librec-auto/splitter/model')
        if model_elem.text == 'kcv':
            return int(model_elem.get('count'))
        else:
            return 1

    def is_valid(self):
        return self._xml_input is not None

    def thread_count(self):
        thread_elems = self._xml_input.xpath('/librec-auto/thread-count')
        if len(thread_elems) == 0:
            return 1
        else:
            return int(thread_elems[0].text)

def read_config_file(config_file, target):
    config = ConfigCmd(config_file, target)
    if config.is_valid():
        config.load_libraries()
        config.process_config()
    return config
