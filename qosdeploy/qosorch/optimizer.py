'''
CloudQoS Optimizer
'''

from planner.placement import Optimization
import simplejson
import os
import sys

import pdb
DEBUG = True

class Optimizer(object):
    '''
    CloudQoS Optimizer
    '''

    SUPPORTED_RESOURCE_TYPES = [
        'ATT::QoS::DeploymentPlan',
        'ATT::QoS::DiversityZone',
        'ATT::QoS::Pipe',
        'OS::Nova::Server',
        'OS::Cinder::Volume',
        'OS::Cinder::VolumeAttachment',
        'OS::Trove::Instance',
    ]

    def __init__(self):
        ''' Initialization. '''
        return

    def _param_default(self, param_dict, param_name):
        ''' Get default parameter value '''
        default = ''
        for name, settings in param_dict.iteritems():
            if name == param_name and isinstance(settings, dict):
                for key, value in settings.iteritems():
                    if key == 'default':
                        default = value
                        break
        return default

    def _filter_resources(self, resources, strip_availability_zones=True):
        ''' Filter out resources not required by the Optimizer. '''
        filtered = {}
        for resource_name, values in resources.iteritems():
            if values['type'] in self.SUPPORTED_RESOURCE_TYPES:
                new_values = values.copy()
                if strip_availability_zones and 'properties' in new_values:
                   properties = new_values['properties']
                   if 'availability_zone' in properties:
                       properties.pop('availability_zone', None)

                # Capitalize type and properties.
                # Heat would normally do this on its own.
                # Also, as a result, the CloudQoS optimizer expects it too.
                new_values['Type'] = new_values['type']
                new_values.pop('type', None)
                if 'properties' in new_values:
                    new_values['Properties'] = new_values['properties']
                    new_values.pop('properties', None)

                filtered[resource_name] = new_values
        return filtered

    def _parse_function(self, dictionary, param_dict):
        '''
        Given a dict of length 1, parse it as if it were a Heat intrinsic.

        This only emulates Heat's get_resource and get_param intrinsics.

        Because the preview occurs before stack-create takes place,
        get_resource simply resolves to the resource name.
        '''
        if not isinstance(dictionary, dict):
            raise TypeError("Input is not a dictionary")
        if len(dictionary) == 1:
            name = dictionary.keys()[0]
            value = dictionary.values()[0]
            if name == 'get_resource':
                return value
            elif name == 'get_param':
                return self._param_default(param_dict, value)
            else:
                raise KeyError("Unknown function name %s" % name)
        else:
            raise LookupError("Dictionary is not of length 1")

    def _parse_resources(self, resource_dict, param_dict):
        '''
        Bare bones preview of resources in a Heat template.
        This takes a resource and parameter dictionary as input.
        It returns a parsed dictionary as output.

        No validity checking takes place. That is, it's possible
        to pass in a template with a get_resource call to an
        undefined resource. Validity should be checked upstream.
        '''
        parsed_dict = {}
        for key, value in resource_dict.iteritems():
            if isinstance(value, list):
                # Parse the list first ...
                parsed_list = []
                for element in value:
                    if isinstance(element, dict):
                        try:
                            # If it's an intrinsic, append the result to our list.
                            result = self._parse_function(element, param_dict)
                            parsed_list.append(result)
                        except:
                            # Nope. Append the parsed resources. Yay recursion!
                            parsed_list.append(
                                self._parse_resources(element, param_dict)
                            )
                    else:
                        parsed_list.append(element)

                # ... then set the key to the parsed list.
                parsed_dict[key] = parsed_list
            elif isinstance(value, dict):
                # Just parse the dictionary.
                try:
                    # If it's an intrinsic, add the result to our parsed dict.
                    result = self._parse_function(value, param_dict)
                    parsed_dict[key] = result
                except:
                    # Nope. Set the key to the parsed resources. Yay recursion!
                    parsed_dict[key] = self._parse_resources(value, param_dict)
            else:
                # It must be a string. Easy peasy.
                parsed_dict[key] = value
        return parsed_dict

    def _preview(self, template):
        ''' Bare bones preview of a template '''
        if 'resources' in template:
            resources = template['resources']
            parameters = None
            if 'parameters' in template:
                parameters = template['parameters']
            return self._parse_resources(resources, parameters)
        return None

    def place(self, template, template_update=None):
        ''' Place resources within a new or updated template. '''
        if template is None:
            return None

        # If we are creating (no template update), strip out AZs.
        strip = (template_update == None)

        # Get resources from each template.
        # Filter out the ones we care about.
        resources = self._preview(template)
        resources_filtered = self._filter_resources(
            resources, strip_availability_zones=strip
        )

        if template_update:
            action = 'update'
            resources_update = self._preview(template_update)
            resources_filtered_update = self._filter_resources(
                resources_update, strip_availability_zones=True
            )
            modified_template = template_update
        else:
            action = 'create'
            modified_template = template

        # Optimizer API version
        version = '0.1'

        payload = {
            'version': version,
            'action': action,
            'resources': resources_filtered,
        }
        if action == 'update':
            payload['resources_update'] = resources_filtered_update

        try:
            umask = os.umask(0000)

            # Create a JSON payload for the Optimizer
            payload_json = simplejson.dumps(
                payload, sort_keys=True, indent=2 * ' '
            )

            # Log to a file if needed.
            if DEBUG:
                #LOG.info(_('Planner request: %s') % payload_json)

                log = open('/tmp/deploy-dump.txt', 'w')
                print >>log, "===Payload==="
                print >>log, payload_json
                log.close()

            # Call the Optimizer
            optimizer = Optimization()
            result = optimizer.place(payload_json, False)

            # Log to a file if needed.
            if DEBUG:
                #LOG.info(_('Planner response: %s') % result)

                log = open('/tmp/deploy-dump.txt', 'a')
                print >>log, "===Result==="
                print >>log, result
                log.close()

            # Load our response.
            response = simplejson.loads(result)
        except:
            raise
        finally:
            os.umask(umask)

        if response['status']['type'] != 'ok':
            print "Optimizer error: %s" % response['status']['message']
            sys.exit(1)

        # Update the original template with any resource
        # changes returned by the optimizer module.
        # modified_template is either the original or updated template.
        if 'resources' in response:
            for key, val in response['resources'].iteritems():
                if 'properties' in val:
                    res = modified_template['resources'][key]
                    res['properties'].update(val['properties'])

        return modified_template
