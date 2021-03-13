import datetime
from functools import wraps
import pprint
import sys
import yaml
from pydoc import locate

import click
from tabulate import tabulate

from ..settings import jinja_env


# ========================
# Exceptions
# ========================

class RenderException(Exception):

    def __init__(self, msg, exit_code=1):
        self.msg = msg
        self.exit_code = exit_code


# ========================
# Decorators
# ========================

def handle_endpoint_exceptions(func):

    @wraps(func)
    def inner(self, *args, **kwargs):
        try:
            obj = func(self, *args, **kwargs)
        except self.endpoint_class.DoesNotExist as e:
            raise RenderException(click.style(str(e), fg='red'))
        except self.endpoint_class.MultipleObjectsReturned as e:
            raise RenderException(click.style(str(e), fg='red'))
        except self.endpoint_class.OperationFailed as e:
            lines = []
            lines.append(click.style(e.msg, fg='red'))
            for k, v in e.errors.items():
                lines.append(click.style(k + ':', fg='yellow'))
                if isinstance(v, list):
                    for error in v:
                        lines.append(click.style('    ' + error, fg='white'))
                else:
                    lines.append(click.style('    ' + v, fg='white'))
                raise RenderException('\n'.join(lines))
        return obj
    return inner


def print_render_exception(func):

    @wraps(func)
    def inner(*args, **kwargs):
        try:
            retval = func(*args, **kwargs)
        except RenderException as e:
            click.echo(e.msg)
            sys.exit(e.exit_code)
        return retval
    return inner


# ========================
# Renderers
# ========================

class AbstractRenderer:

    def __init__(self, *args, **kwargs):
        pass

    def render(self, data):
        raise NotImplementedError


class TableRenderer(AbstractRenderer):
    """
    Render a list of results as an ASCII table.
    """

    DEFAULT_DATETIME_FORMAT = "%b %d, %Y %I:%M:%S %p"
    DEFAULT_DATE_FORMAT = "%b %d, %Y"
    DEFAULT_FLOAT_PRECISION = 2

    def __init__(self, columns, datetime_format=None, date_format=None, float_precision=None):
        """
        `columns` is a dict that determines the structure of the table, like so:

            {
                'ID': 'id',
                'Machine Name': 'machine_name',
                'Name': 'name',
            }

        The keys of `columns` will be used as the column header in the table, and the values in `columns`
        are the names of the attributes on our result objects that contain the data we want to render for that
        column.

        If the value has double underscores in it, e.g. "software__machine_name", this instructs TableRenderer to look
        at an attribute/key on a sub-object. In this case, at the `machine_name` attribute/key of the `software` object
        on our main object.

        :param columns dict(str, str): a dict that determines the structure of the table
        :param datetime_format Union[str, None]: if specified, use this to render any `datetime.datetime` objects we get
        :param date_format Union[str, None]: if specified, use this to render any `datetime.date` objects we get
        :param float_precision Union[int, None]: if specified, use this to determine the decimal precision
                                                 of any `float` objects we get

        """
        assert isinstance(columns, dict), 'TableRenderer: `columns` parameter to __init__ should be a dict'

        self.columns = list(columns.values())
        self.headers = list(columns.keys())
        self.datetime_format = datetime_format if datetime_format else self.DEFAULT_DATETIME_FORMAT
        self.date_format = date_format if date_format else self.DEFAULT_DATE_FORMAT
        self.float_precision = float_precision if float_precision else self.DEFAULT_FLOAT_PRECISION
        self.float_format = '{{:.{}f}}'.format(self.float_precision)

    def render_column(self, obj, column):
        """
        Return the value to put in the table for the attribute named `column` on `obj`, a data object.

        Normally this just does `getattr(obj, column)`, but there are special cases:

            * If the value is a `datetime.datetime`, render it with `.stftime(self.datetime_format)`
            * If the value is a `datetime.date`, render it with `.stftime(self.date_format)`
            * If the value is a `float`, render it with precision
            * If there we have method named `render_{column}_value`, execute that and return its value.

        :param obj: the data object
        :param column str: the attribute to access on the `obj`

        :rtype: str
        """

        if hasattr(self, f'render_{column}_value'):
            value = getattr(self, f'render_{column}_value')(obj, column)
        else:
            if '__' in column:
                refs = column.split('__')
                ref = refs.pop(0)
                while ref:
                    # Sub objects show up as dicts, while the top level object is a class instance,
                    # so we have to see what we have
                    if isinstance(obj, dict):
                        try:
                            obj = obj[ref]
                        except KeyError:
                            raise RenderException(
                                f'TableRenderer: {obj.__class__.__name__} has no attribute called "{column}"',
                            )
                    else:
                        try:
                            obj = getattr(obj, ref)
                        except AttributeError:
                            raise RenderException(
                                f'TableRenderer: {obj.__class__.__name__} has no attribute called "{column}"',
                            )
                    try:
                        ref = refs.pop(0)
                    except IndexError:
                        ref = None
                return obj   # the last one should be the value we're looking for
            else:
                try:
                    value = getattr(obj, column)
                except AttributeError:
                    raise RenderException(
                        f'TableRenderer: {obj.__class__.__name__} has no attribute called "{column}"',
                    )
                if isinstance(value, datetime.datetime):
                    value = value.strftime(self.datetime_format)
                elif isinstance(value, datetime.date):
                    value = value.strftime(self.date_format)
                elif isinstance(value, float):
                    value = self.float_format.format(value)
        return value

    def render(self, objects):
        table = []
        for obj in objects:
            row = []
            for column in self.columns:
                row.append(self.render_column(obj, column))
            table.append(row)
        return tabulate(table, headers=self.headers)


class JSONRenderer(AbstractRenderer):
    """
    This renderer just pretty prints whatever you give it with an indent of 2 spaces.
    """

    def render(self, data):
        return pprint.pformat(data, indent=2)


class TemplateRenderer(AbstractRenderer):
    """
    Given a template path, render an object with that template.
    """

    def __init__(self, template_file):
        self.template_file = template_file

    def render(self, obj):
        values = {}
        values['obj'] = obj
        template = jinja_env.get_template(self.template_file)
        return template.render(**values)


# ========================


class ClickEndpointAdapter:

    endpoint_class = None

    # Renderers
    datetime_format = None
    date_format = None
    float_precision = None
    detail_template = None

    list_result_columns = {}
    list_renderer_classes = {
        'table': TableRenderer,
        'json': JSONRenderer
    }
    list_expands = None

    retrieve_expands = None
    retrieve_renderer_classes = {
        'template': TemplateRenderer,
        'json': JSONRenderer
    }

    partial_update_allowed_attributes = None

    @classmethod
    def list_display_option_kwargs(cls):
        """
        Return the appropriate kwargs for `click.option('--display', **kwargs)` for the renderer options we've defined
        for the list endpoint.

        :rtype: dict
        """
        render_types = list(cls.list_renderer_classes.keys())
        default = render_types[0]
        kwargs = {
            'type': click.Choice(render_types),
            'default': default,
            'help': f"Render method for listing {cls.endpoint_class.object_class.__name__} objects."
                    f"Choices: {', '.join(render_types)}.  Default: {default}."
        }
        return kwargs

    @classmethod
    def retrieve_display_option_kwargs(cls):
        """
        Return the appropriate kwargs for `click.option('--display', **kwargs)` for the renderer options we've defined
        for the retrieve endpoint.

        :rtype: dict
        """
        render_types = list(cls.retrieve_renderer_classes.keys())
        default = render_types[0]
        kwargs = {
            'type': click.Choice(render_types),
            'default': default,
            'help': f"Render method for displaying single {cls.endpoint_class.object_class.__name__} objects."
                    f"Choices: {', '.join(render_types)}.  Default: {default}."
        }
        return kwargs

    @classmethod
    def add_list_click_command(cls, command_group):
        """
        Build a fully specified click command for listing objects, and add it to the click command group
        `command_group`.  Return the function object.

        :param command_group function: the click command group function to use to register our click command

        :rtype: function
        """
        def list_objects(ctx, *args, **kwargs):
            display = kwargs.pop('display')
            click.secho(ctx.obj['adapter'].list(display, **kwargs))
        object_name = cls.endpoint_class.object_class.__name__
        list_objects.__doc__ = f"""
List {object_name} objects in Brigid, possibly with filters.

Usage:

    brigid {command_group.name} list [--display=DISPLAY] [filter flags]
"""

        function = print_render_exception(list_objects)
        function = click.pass_context(function)
        for key, type_str in cls.endpoint_class.list_filters().items():
            option = f"--{key.replace('_', '-')}"
            if type_str == 'datetime.datetime':
                click_type = click.DateTime()
            else:
                click_type = locate(type_str)
            function = click.option(
                option,
                default=None,
                type=click_type,
                help=f"Filter results by {key}"
            )(function)
        function = click.option(
            '--limit',
            type=int,
            default=100,
            help="Limit paged list requests to this number of items"
        )(function)
        function = click.option('--display', **cls.list_display_option_kwargs())(function)
        function = command_group.command(
            'list',
            short_help=f'List {object_name} objects in Brigid, possibly with filters.'
        )(function)
        return function

    @classmethod
    def add_create_click_command(cls, command_group):
        """
        Build a fully specified click command for creating objects, and add it to the click command group
        `command_group`.  Return the function object.

        :param command_group function: the click command group function to use to register our click command

        :rtype: function
        """
        def create_object(ctx, *args, **kwargs):
            with open(kwargs['filename'], "r") as fd:
                file_data = fd.read()
            # Note as of PyYAML 5, the yaml parser will parse both JSON and YAML
            obj_data = yaml.safe_load(file_data)
            click.secho(ctx.obj['adapter'].create(**obj_data))
        object_name = cls.endpoint_class.object_class.__name__
        create_object.__doc__ = f"""
Create a new {object_name} object in Brigid from a file.

FILENAME can be either a JSON or YAML file, and should at least contain all the required
attributes for {object_name} objects.

Usage:

    brigid {command_group.name} create FILENAME
"""
        # Wrap our function with the approriate decorators
        function = print_render_exception(create_object)
        function = click.pass_context(function)
        function = click.argument('filename', type=click.Path(exists=True))
        function = command_group.command(
            'create',
            short_help=f'Create a {object_name} object in Brigid'
        )(function)
        return function

    @classmethod
    def add_retrieve_click_command(cls, command_group):
        """
        Build a fully specified click command for retrieving single objects, and add it to the click command group
        `command_group`.  Return the function object.

        :param command_group function: the click command group function to use to register our click command

        :rtype: function
        """
        def retrieve_object(ctx, *args, **kwargs):
            click.secho(ctx.obj['adapter'].retrieve(kwargs['identifier'], kwargs['display']))
        object_name = cls.endpoint_class.object_class.__name__
        retrieve_object.__doc__ = f"""
Get an existing {object_name} object from Brigid.

IDENTIFIER is one of {object_name}.id or {cls.endpoint_class.id_resolver_filter_format()}.

Usage:

    brigid {command_group.name} retrieve IDENTIFIER [--display=DISPLAY]
"""

        function = print_render_exception(retrieve_object)
        function = click.pass_context(function)
        function = click.option('--display', **cls.retrieve_display_option_kwargs())(function)
        function = click.argument('identifier')(function)
        function = command_group.command(
            'retrieve',
            short_help=f'Get a single {object_name} object from Brigid'
        )(function)
        return function

    @classmethod
    def add_partial_update_click_command(cls, command_group):
        """
        Build a fully specified click command for partial updating objects, and add it to the click command group
        `command_group`.  Return the function object.

        :param command_group function: the click command group function to use to register our click command

        :rtype: function
        """
        def partial_update_object(ctx, *args, **kwargs):
            identifier = kwargs.pop('identifier')
            click.secho(ctx.obj['adapter'].partial_update(identifier, **kwargs))
        object_name = cls.endpoint_class.object_class.__name__
        partial_update_object.__doc__ = f"""
Update attributes of an existing  a new {object_name} object in Brigid from a file.

IDENTIFIER is one of {object_name}.id or {cls.endpoint_class.id_resolver_filter_format()}.

Usage:

    brigid {command_group.name} update IDENTIFIER [--display=DISPLAY] [attributes]
"""

        function = print_render_exception(partial_update_object)
        function = click.pass_context(function)
        function = click.argument('identifier')(function)
        function = command_group.command(
            'update',
            short_help=f'Update attrbutes of a {object_name} object in Brigid'
        )(function)
        for key in cls.partial_update_allowed_attributes:
            # reverse the order, of course
            option = f"--{key.replace('_', '-')}"
            function = click.option(
                option,
                default=cls.endpoint_class.UNSET,
                help=f"Set {cls.endpoint_class.object_class.__name__}.{key}"
            )(function)
        return function

    @classmethod
    def add_delete_click_command(cls, command_group):
        """
        Build a fully specified click command for deleting objects, and add it to the click command group
        `command_group`.  Return the function object.

        :param command_group function: the click command group function to use to register our click command

        :rtype: function
        """
        def delete_object(ctx, *args, **kwargs):
            click.secho(ctx.obj['adapter'].delete(kwargs['identifier']))
        object_name = cls.endpoint_class.object_class.__name__
        delete_object.__doc__ = f"""
Delete an existing {cls.endpoint_class.object_class.__name__} object from Brigid.

IDENTIFIER is one of {object_name}.id or {cls.endpoint_class.id_resolver_filter_format()}.

Usage:

    brigid {command_group.name} delete IDENTIFIER
"""

        function = print_render_exception(delete_object)
        function = click.pass_context(function)
        function = click.argument('identifier')(function)
        function = command_group.command(
            'delete',
            short_help=f'Delete a {object_name} object from Brigid'
        )(function)
        return function

    def __init__(self, client):
        assert self.endpoint_class is not None, \
            f'{self.__class__.__name__}: please set the endpoint_class class attribute'
        self.client = client
        self.endpoint = self.endpoint_class(client)

    @property
    def object_class_name(self):
        return self.endpoint_class.object_class.__name__

    @handle_endpoint_exceptions
    def resolve_object_id(self, identifier):
        return self.endpoint.resolve_object_id(identifier)

    @handle_endpoint_exceptions
    def list(self, display, **kwargs):
        assert display in self.list_renderer_classes, \
            f'{self.__class__.__name__}.list(): "{display}" is not a valid list rendering option'
        if 'expand' not in kwargs:
            kwargs['expand'] = self.list_expands
        results = self.endpoint.list(**kwargs)
        if not results:
            return('No results matched your filters.')
        else:
            return self.list_renderer_classes[display](self.list_result_columns).render(results)

    @handle_endpoint_exceptions
    def retrieve(self, identifier, display, **kwargs):
        if 'expand' not in kwargs:
            kwargs['expand'] = self.retrieve_expands
        assert display in self.retrieve_renderer_classes, \
            f'{self.__class__.__name__}.retrieve(): "{display}" is not a valid retrieve rendering option'
        obj = self.endpoint.retrieve(identifier, **kwargs)
        return self.retrieve_renderer_classes[display](self.detail_template).render(obj)

    @handle_endpoint_exceptions
    def partial_update(self, identifier, **kwargs):
        if self.partial_update_allowed_attributes:
            allowed = set(self.partial_update_allowed_attributes)
            provided = set(kwargs)
            banned = list(provided - allowed)
            assert not banned, \
                f"{self.__class__.__name__}.partial_update(): these attribute are not allowed to be updated: {','.join(banned)}"   # noqa:E501
        results = self.endpoint.partial_update(identifier, **kwargs)
        lines = []
        lines.append(click.style(f'Updated {self.object_class_name}("{identifier}"):', fg='cyan'))
        for k, v in results.items():
            if kwargs[k] != self.endpoint_class.UNSET:
                lines.append(f'  {k}={v}')
        return '\n'.join(lines)

    @handle_endpoint_exceptions
    def delete(self, identifier):
        self.endpoint.delete(identifier)
        return click.style(f'Deleted {self.object_class_name}("{identifier}")', fg='cyan')
