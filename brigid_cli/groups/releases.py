#!/usr/bin/env python
import click

from brigid_cli.cli import cli
from brigid_api.software import ReleasesEndpoint
from .mixins import (
    ClickEndpointAdapter,
    TableRenderer,
    handle_endpoint_exceptions,
    print_render_exception,
)


@cli.group('releases', short_help="Work with Release objects.")
@click.pass_context
def releases(ctx):
    # Doing import_all can take a while, so increase the timeout
    ctx.obj['adapter'] = ClickReleasesEndpointAdapter(ctx.obj['brigid_client'].with_timeout(300))


class ReleasesTableRenderer(TableRenderer):

    def render_releaser_value(self, obj, column):
        return f'{obj.released_by["fullname"]} <{obj.released_by["email"]}>'


class ClickReleasesEndpointAdapter(ClickEndpointAdapter):

    endpoint_class = ReleasesEndpoint
    detail_template = 'release.tpl'
    list_result_columns = {
        'ID': 'id',
        'Software': 'software__name',
        'Version': 'version',
        'Released By': 'releaser',
        'Released': 'release_time',
    }
    list_expands = 'release.software,release.released_by'
    retrieve_expands = 'release.software,release.released_by'
    partial_update_allowed_attributes = [
        'sha',
        'changelog',
    ]

    @handle_endpoint_exceptions
    def import_release(self, identifier, version):
        release_id, created = self.endpoint.import_release(identifier, version)
        if created:
            return click.style(f"Success: created new {self.endpoint.object_repr(id=release_id)}", fg='white')
        else:
            return click.style(f"Success: updated {self.endpoint.object_repr(id=release_id)}", fg='cyan')

    @handle_endpoint_exceptions
    def import_all_releases(self, identifier):
        return self.endpoint.import_all_releases(identifier)

    @handle_endpoint_exceptions
    def sync(self, identifier):
        release_id = self.endpoint.sync(identifier)
        return click.style(f"Success: updated {self.endpoint.object_repr(id=release_id)}", fg='cyan')


ClickReleasesEndpointAdapter.list_renderer_classes['table'] = ReleasesTableRenderer


releases_create = ClickReleasesEndpointAdapter.add_create_click_command(releases)
releases_details = ClickReleasesEndpointAdapter.add_retrieve_click_command(releases)
releases_list_all = ClickReleasesEndpointAdapter.add_list_click_command(releases)
releases_update = ClickReleasesEndpointAdapter.add_partial_update_click_command(releases)
releases_delete = ClickReleasesEndpointAdapter.add_delete_click_command(releases)


@releases.command('import', short_help='Import a software release into Brigid')
@click.argument('identifier')
@click.argument('version')
@click.pass_context
@print_render_exception
def release_do_import(ctx, identifier, version):
    """
    Import a release for the Software identified by SOFTWARE_IDENTIFIER from its
    upstream git repository, and save the result as a Release.

    Usage:

        brigid releases import SOFTWARE_IDENTIFIER VERSION

    * SOFTWARE_IDENTIFIER is either a Software.id or a Software.name
    * VERSION is a version number like 1.2.3

    VERSION must exist as a tag in the upstream git repository.
    """
    click.secho(ctx.obj['adapter'].import_release(identifier, version))


@releases.command('import-all', short_help='Import a all releases for a Software into Brigid')
@click.argument('identifier')
@click.pass_context
@print_render_exception
def release_do_import_all(ctx, identifier):
    """
    Import all releases for the Software identified by SOFTWARE_IDENTIFIER from its
    upstream git repository, and save the result as a set of Releases.

    Usage:

        brigid releases import-all SOFTWARE_IDENTIFIER

    * SOFTWARE_IDENTIFIER is either a Software.id or a Software.name

    """
    click.secho(ctx.obj['adapter'].import_all_releases(identifier))


@releases.command('sync', short_help='Sync data for an existing Release from its upstream git provider')
@click.argument('identifier')
@click.pass_context
@print_render_exception
def release_do_sync(ctx, identifier):
    """
    Re-sync a Release object from its upstream git repository.

    Usage:

        brigid releases sync IDENTIFIER

    IDENTIFIER is either a Release.id or a string like "{Software.name}:{Release.version}"
    """
    click.secho(ctx.obj['adapter'].sync(identifier))
