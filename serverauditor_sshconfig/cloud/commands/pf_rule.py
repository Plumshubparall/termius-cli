import re
from operator import attrgetter
from ...core.exceptions import (
    InvalidArgumentException, ArgumentRequiredException,
    TooManyEntriesException, DoesNotExistException,
)
from ...core.commands import DetailCommand, ListCommand
from ..models import Host, PFRule


class PFRuleCommand(DetailCommand):
    """Operate with port forwarding rule object."""

    allowed_operations = DetailCommand.all_operations
    model_class = PFRule

    @property
    # pylint: disable=no-self-use
    def binding_parsers(self):
        return {
            'D': BindingParser.dynamic,
            'L': BindingParser.local,
            'R': BindingParser.remote,
        }

    def get_parser(self, prog_name):
        parser = super(PFRuleCommand, self).get_parser(prog_name)
        parser.add_argument(
            '-H', '--host', metavar='HOST_ID or HOST_NAME',
            help='Create port forwarding rule for this host.'
        )
        parser.add_argument(
            '--dynamic', dest='type', action='store_const',
            const='D', help='Dynamic port forwarding.'
        )
        parser.add_argument(
            '--remote', dest='type', action='store_const',
            const='R', help='Remote port forwarding.'
        )
        parser.add_argument(
            '--local', dest='type', action='store_const',
            const='L', help='Local port forwarding.'
        )
        parser.add_argument(
            '--binding', metavar='BINDINDS',
            help=('Specify binding of ports and addresses '
                  '[bind_address:]port or [bind_address:]port:host:hostport')
        )
        parser.add_argument(
            'pr_rule', nargs='?', metavar='PF_RULE_ID or PF_RULE_NAME',
            help='Pass to edit exited port Forwarding Rule.'
        )
        return parser

    def parse_binding(self, pf_type, binding):
        return self.binding_parsers[pf_type](binding)

    def create(self, parsed_args):
        if not parsed_args.host:
            raise ArgumentRequiredException('Host is required.')

        self.create_instance(parsed_args)

    def serialize_args(self, args, instance=None):
        if instance:
            pfrule, host = instance, instance.host
        else:
            pfrule, host = PFRule(), self.get_host(args.host)
            if not args.type:
                raise ArgumentRequiredException('Type is required.')

        pfrule.pf_type = args.type or pfrule.pf_type
        pfrule.host = host
        if args.binding:
            binding_dict = self.parse_binding(pfrule.pf_type, args.binding)
            for key, value in binding_dict.items():
                setattr(pfrule, key, value)
        return pfrule

    def get_host(self, arg):
        try:
            host_id = int(arg)
        except ValueError:
            host_id = None
        try:
            return self.storage.get(Host, query_union=any,
                                    id=host_id, label=arg)
        except DoesNotExistException:
            raise ArgumentRequiredException('Not found any host.')
        except TooManyEntriesException:
            raise ArgumentRequiredException('Found to many hosts.')


class PFRulesCommand(ListCommand):
    """Manage port forwarding rule objects."""

    def take_action(self, parsed_args):
        pf_rules = self.storage.get_all(PFRule)
        fields = PFRule.allowed_fields()
        getter = attrgetter(*fields)
        return fields, [getter(i) for i in pf_rules]


class InvalidBinding(InvalidArgumentException):
    pass


class BindingParser(object):

    local_pf_re = re.compile(
        r'^((?P<bound_address>[\w.]+):)?(?P<local_port>\d+)'
        r':(?P<hostname>[\w.]+):(?P<remote_port>\d+)$'
    )
    dynamic_pf_re = re.compile(
        r'^((?P<bound_address>[\w.]+):)?(?P<local_port>\d+)'
        r'(?P<hostname>)(?P<remote_port>)$'
        # Regexp Groups should be the same for all rules.
    )

    @classmethod
    def parse(cls, regexp, binding_str):
        matched = regexp.match(binding_str)
        if not matched:
            raise InvalidBinding('Invalid binding format.')
        return matched.groupdict()

    @classmethod
    def local(cls, binding_str):
        return cls.parse(cls.local_pf_re, binding_str)
    remote = local

    @classmethod
    def dynamic(cls, binding_str):
        return cls.parse(cls.dynamic_pf_re, binding_str)
