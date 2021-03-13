#!/usr/bin/env python
import click

from brigid_cli.cli import cli
from brigid_api.software import SoftwareEndpoint
from .mixins import ClickEndpointAdapter, print_render_exception, handle_endpoint_exceptions


@cli.group('software', short_help="Work with Software objects.")
@click.pass_context
def software(ctx):
    ctx.obj['adapter'] = ClickSoftwareEndpointAdapter(ctx.obj['brigid_client'])


class ClickSoftwareEndpointAdapter(ClickEndpointAdapter):

    endpoint_class = SoftwareEndpoint
    detail_template = 'software.tpl'
    list_result_columns = {
        'ID': 'id',
        'Machine Name': 'machine_name',
        'Human Name': 'name',
        'Repo Created': 'repo_created',
        'Repo Modified': 'repo_modified',
    }
    retrieve_expands = 'software.applications,software.authors'
    partial_update_allowed_attributes = [
        'trello_board_url',
        'documentation_url',
        'name'
    ]

    @handle_endpoint_exceptions
    def import_repository(self, repository):
        software_id, created = self.endpoint.import_repository(repository)
        if created:
            return click.style(f"Success: created new {self.endpoint.object_repr(id=software_id)}", fg='white')
        else:
            return click.style(f"Success: updated {self.endpoint.object_repr(id=software_id)}", fg='cyan')

    @handle_endpoint_exceptions
    def sync(self, identifier):
        software_id = self.endpoint.sync(identifier)
        return click.style(f"Success: updated {self.endpoint.object_repr(id=software_id)}", fg='cyan')


software_details = ClickSoftwareEndpointAdapter.add_retrieve_click_command(software)
software_list_all = ClickSoftwareEndpointAdapter.add_list_click_command(software)
software_update = ClickSoftwareEndpointAdapter.add_partial_update_click_command(software)
software_delete = ClickSoftwareEndpointAdapter.add_delete_click_command(software)


@software.command('import', short_help='Import a repository into Brigid')
@click.argument('repository')
@click.pass_context
@print_render_exception
def software_do_import(ctx, repository):
    click.secho(ctx.obj['adapter'].import_repository(repository))


@software.command('sync', short_help='Sync data for an existing Software from its upstream git provider')
@click.argument('identifier')
@click.pass_context
@print_render_exception
def software_do_sync(ctx, identifier):
    click.secho(ctx.obj['adapter'].sync(identifier))
