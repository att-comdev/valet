#!/usr/bin/python
import argparse
import cli_config as config
import json
import requests


class ResponseError(Exception):
    pass


class ConnectionError(Exception):
    pass


def add_to_parser(service_sub):
    parser = service_sub.add_parser('group', help='Group Management',
                                    formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=30,
                                                                                        width=120))
    parser.add_argument('--version', action='version', version='%(prog)s 1.0')
    parser.add_argument('--host', type=str, help='hostname or ip of valet server')
    parser.add_argument('--port', type=str, help='port number of valet server')
    parser.add_argument('--timeout', type=int, help='request timeout in seconds (default: 10)')
    parser.add_argument('-v', '--verbose', help='show details', action="store_true")
    subparsers = parser.add_subparsers(dest='subcmd', metavar='<subcommand> [-h] <args>')

    # create group
    parser_create_group = subparsers.add_parser('create_group',
                                                help='--name <group name> --type <group type>'
                                                '[--description <group description>]')
    parser_create_group.add_argument('--name', type=str, help='group name')
    parser_create_group.add_argument('--type', type=str, help='group type (exclusivity)')
    parser_create_group.add_argument('--description', type=str, help='group description')

    # update group
    parser_update_group = subparsers.add_parser('update_group', help='<group id> --description <group description>')
    parser_update_group.add_argument('groupid', type=str, help='<group id>')
    parser_update_group.add_argument('--description', type=str, help='group description')

    parser_update_group_members = subparsers.add_parser('update_group_members', help='<group id> --members <member id>')
    parser_update_group_members.add_argument('groupid', type=str, help='<group id>')
    parser_update_group_members.add_argument('--members', type=str, help='member id')

    # list group
    subparsers.add_parser('list_groups')

    # show group details
    parser_show_group_details = subparsers.add_parser('show_group_details', help='<group id> ')
    parser_show_group_details.add_argument('groupid', type=str, help='<group id>')

    # delete group
    parser_delete_group = subparsers.add_parser('delete_group', help='<group id>')
    parser_delete_group.add_argument('groupid', type=str, help='<group id>')

    # delete group member
    parser_delete_group_member = subparsers.add_parser('delete_group_member', help='<group id> <member id>')
    parser_delete_group_member.add_argument('groupid', type=str, help='<group id>')
    parser_delete_group_member.add_argument('memberid', type=str, help='<member id>')

    # delete all group members
    parser_delete_all_group_members = subparsers.add_parser('delete_all_group_members', help='<group id>')
    parser_delete_all_group_members.add_argument('groupid', type=str, help='<group id>')

    parser.add_argument('--name', type=str, help='group name')
    parser.add_argument('--description', type=str, help='group description')
    parser.add_argument('--type', type=str, help='group type (exclusivity)')
    return parser


def preparm(p):
    return ('' if len(p) else '?') + ('&' if len(p) else '')


def cmd_details(args):
    if args.subcmd == 'create_group':
        return requests.post, ''
    elif args.subcmd == 'update_group':
        return requests.put, '/%s' % args.groupid
    elif args.subcmd == 'update_group_members':
        return requests.put, '/%s/members' % args.groupid
    elif args.subcmd == 'delete_group':
        return requests.delete, '/%s' % (args.groupid)
    elif args.subcmd == 'delete_all_group_members':
        return requests.delete, '/%s/members' % (args.groupid)
    elif args.subcmd == 'delete_group_member':
        return requests.delete, '/%s/members/%s' % (args.groupid, args.memberid)
    elif args.subcmd == 'show_group_details':
        return requests.get, '/%s' % (args.groupid)
    elif args.subcmd == 'list_groups':
        return requests.get, ''


def get_token_from_keystone_v3():
    headers = {
        'Content-Type': 'application/json',
    }
    url = 'http://%s/v3/auth/tokens' % config.keystone_ip_and_port
    data = '''
{
    "auth": {
        "identity": {
            "methods": ["password"],
            "password": {
                "user": {
                    "name": "%s",
                    "domain": { "id": "default" },
                    "password": "%s"
                }
            }
        }
    }
}''' % (config.auth_name, config.password)
    try:
        resp = requests.post(url, data=data, headers=headers)
    except Exception as e:
        print(e)
        exit(1)
    return resp.headers['X-Subject-Token']


def get_token(timeout, args):
    headers = {
        'Content-Type': 'application/json',
    }
    url = '%s/v2.0/tokens' % config.keystone_ip_and_port
    data = '''
{
"auth": {
    "tenantName": "%s",
    "passwordCredentials": {
        "username": "%s",
        "password": "%s"
        }
    }
}''' % (config.tenant_name, config.auth_name, config.password)
    if args.verbose:
        print("Getting token:\ntimeout: %d\ndata: %s\nheaders: %s\nurl: %s\n" % (timeout, data, headers, url))
    try:
        resp = requests.post(url, timeout=timeout, data=data, headers=headers)
        if resp.status_code != 200:
            raise ResponseError(
                'Failed in get_token: status code received {}'.format(
                    resp.status_code))
        return resp.json()['access']['token']['id']

    except Exception as e:
        message = 'Failed in get_token'
        # logger.log_exception(message, str(e))
        print(e)
        raise ConnectionError(message)


def run(args):
    host = args.host if args.host else config.valet_host
    port = args.port if args.port else config.valet_port
    timeout = args.timeout if args.timeout else 10
    rest_cmd, cmd_url = cmd_details(args)
    url = 'http://%s:%s/v1/groups' % (host, port) + cmd_url
    auth_token = get_token(timeout, args)
    headers = {
        'content-type': 'application/json',
        'X-Auth-Token': auth_token
    }

    body_args_list = ['name', 'type', 'description', 'members']
    # assign values to dictionary (if val exist). members will be assign as a list
    body_dict = {}
    for body_arg in body_args_list:
            if hasattr(args, body_arg):
                body_dict[body_arg] = getattr(args, body_arg) if body_arg != 'members' else [getattr(args, body_arg)]
    # remove keys without values
    filtered_body_dict = dict((k, v) for k, v in body_dict.iteritems() if v is not None)
    # convert body dictionary to json format
    body_json = json.dumps(filtered_body_dict)

    try:
        if len(body_json) > 2:
            # send body only if exist
            if args.verbose:
                print("Sending API:\ntimeout: %d\ndata: %s\nheaders: %s\ncmd: %s\nurl: %s\n"
                      % (timeout, body_json, headers, rest_cmd.__name__, url))
            resp = rest_cmd(url, timeout=timeout, data=body_json, headers=headers)
        else:
            if args.verbose:
                print("Sending API:\ntimeout: %d\nheaders: %s\ncmd: %s\nurl: %s\n"
                      % (timeout, headers, rest_cmd.__name__, url))
            resp = rest_cmd(url, timeout=timeout, headers=headers)
    except Exception as e:
        print(e)
        exit(1)

    if not 200 <= resp.status_code < 300:
        content = resp.json() if resp.status_code == 500 else ''
        print('API error: %s %s (Reason: %d)\n%s' % (rest_cmd.func_name.upper(), url, resp.status_code, content))
        exit(1)

    # if resp.status_code == 204:  # no content
    #    exit(0)

    rj = resp.json()
    if rj == 'Not found':
        print('No output was found')
    else:
        print(rj)
