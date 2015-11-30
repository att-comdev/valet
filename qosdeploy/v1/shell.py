from heatclient.common import utils
import heatclient.exc as exc
import sys
import pdb
import inspect

from qosdeploy.qosorch import optimizer

@utils.arg('-f', '--template-file', metavar='<FILE>',
           help='Path to the template.')
@utils.arg('-c', '--create-timeout', metavar='<TIMEOUT>',
           default=60, type=int,
           help='Stack creation timeout in minutes. Default: 60.')
@utils.arg('name', metavar='<STACK_NAME>',
           help='Name of the stack to create.')
def do_stack_create(heat, hc, args):
    '''Create the stack.'''

    try:
        if hc.stacks.get(args.name):
            print("Stack already exists. Did you mean to Update?")
            sys.exit(1)
    except exc.HTTPNotFound:
        # Stack wasn't found. Good. We can create it.
        pass
    except:
        raise

    # Load template
    template = heat.load_template(args.template_file)

    # Place the resources
    opt = optimizer.Optimizer()
    template_with_placements = opt.place(template)
    template_string = utils.yaml.dump(template_with_placements)

    kwargs = {
        "stack_name": args.name,
        "template": template_string,
        "timeout_mins": args.create_timeout,
    }

    hc.stacks.create(**kwargs)
    do_stack_list(heat, hc)

@utils.arg('-f', '--template-file', metavar='<FILE>',
           help='Path to the template.')
@utils.arg('id', metavar='<NAME or ID>',
           help='Name or ID of stack to update.')
def do_stack_update(heat, hc, args):
    '''Update the stack.'''

    stack = hc.stacks.get(args.id)
    if stack.status != 'COMPLETE':
        print("Stack status must be COMPLETE in order to update.")
        sys.exit(1)

    # Get original template with AZ assignments, and the new template
    template = hc.stacks.template(args.id)
    template_update = heat.load_template(args.template_file)

    # Place the resources
    opt = optimizer.Optimizer()
    template_with_placements = opt.place(template, template_update)
    template_string = utils.yaml.dump(template_with_placements)

    kwargs = {
        "stack_id": args.id,
        "template": template_string,
    }

    hc.stacks.update(**kwargs)
    do_stack_list(heat, hc)

@utils.arg('id', metavar='<NAME or ID>', nargs='+',
           help='Name or ID of stack(s) to delete.')
def do_stack_delete(heat, hc, args):
    '''Delete the stack(s).'''

    failure_count = 0

    for sid in args.id:
        fields = {'stack_id': sid}
        try:
            hc.stacks.delete(**fields)
        except exc.HTTPNotFound as e:
            failure_count += 1
            print(e)
    if failure_count == len(args.id):
        raise exc.CommandError("Unable to delete any of the specified "
                               "stacks.")
    do_stack_list(heat, hc)

@utils.arg('-f', '--filters', metavar='<KEY1=VALUE1;KEY2=VALUE2...>',
           help='Filter parameters to apply on returned stacks. '
           'This can be specified multiple times, or once with parameters '
           'separated by a semicolon.',
           action='append')
@utils.arg('-l', '--limit', metavar='<LIMIT>',
           help='Limit the number of stacks returned.')
@utils.arg('-m', '--marker', metavar='<ID>',
           help='Only return stacks that appear after the given stack ID.')
def do_stack_list(heat, hc, args=None):
    '''List the user's stacks.'''
    kwargs = {}
    if args:
        kwargs = {'limit': args.limit,
                  'marker': args.marker,
                  'filters': utils.format_parameters(args.filters)}

    stacks = hc.stacks.list(**kwargs)
    fields = ['id', 'stack_name', 'stack_status', 'creation_time']

    if 'sortby_index' in inspect.getargspec(utils.print_list).args:
        # Juno and onward
        utils.print_list(stacks, fields, sortby_index=3)
    else:
        # Icehouse and earlier
        utils.print_list(stacks, fields, sortby=3)
