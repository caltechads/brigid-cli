#!/usr/bin/env python
import json
import pprint
import sys

import click
import dateparser
from giturlparse import parse
from tabulate import tabulate

import brigid_cli
from brigid_api_client.client import AuthenticatedClient
from brigid_api_client.api.software import (
    software_list,
    software_import,
    software_sync,
    software_partial_update,
    software_retrieve
)
from brigid_api.software import SoftwareEndpoint
from .settings import Settings


def resolve_software_id(client, identifier):
    try:
        software_id = int(identifier)
    except ValueError:
        # This is a machine_name
        results = software_list.sync(client=client, machine_name=identifier).results
        if len(results) > 1:
            click.secho(f'More than one Software object matches "{identifier}".  Be more specific.', fg='red')
            return
        elif len(results) == 0:
            click.secho(f'Could not find a Software object that matches "{identifier}"',  fg='red')
            return
        else:
            software_id = results[0].id
    return software_id


@click.group(invoke_without_command=True)
@click.option('--version/--no-version', '-v', default=False, help="Print the current version and exit.")
@click.pass_context
def cli(ctx, version):
    """
    Command line interface for Brigid.
    """

    settings = Settings()
    ctx.obj['settings'] = settings
    ctx.obj['brigid_client'] = AuthenticatedClient(
        base_url=settings.brigid_base_url,
        token=settings.brigid_api_token,
        timeout=30.0
    )

    if version:
        print(brigid_cli.__version__)
        sys.exit(0)


@cli.command('settings', short_help="Print our application settings.")
@click.pass_context
def settings(ctx):
    """
    Print our settings to stdout.  This should be the completely evaluated settings including
    those imported from any environment variable.
    """
    pp = pprint.PrettyPrinter(indent=2)
    pp.pprint(ctx.obj['settings'].dict())


@cli.group('software', short_help="Work with Software objects.")
def software():
    pass


@software.command('list', short_help='List software objects')
@click.option(
    '--display',
    type=click.Choice(['short', 'raw']),
    default='short',
    help="Configure how to print out member information.  Choices: name_email, email, details, raw"
)
@click.option('--page-size', type=int, default=100, help="Limit requests to this number of items")
@click.option('--name', default=None, help="Filter by software whose human name contains this")
@click.option('--machine-name', default=None, help="Filter by software whose machine_name contains this")
@click.option('--author-username', default=None, help="Filter by software with authors whose username contains this")
@click.pass_context
def software_list_all(ctx, display, page_size, name, machine_name, author_username):
    api = SoftwareEndpoint(ctx.obj['brigid_client'])
    results = api.list(limit=page_size, name=name, machine_name=machine_name, author_username=author_username)
    if not results:
        click.secho('No software matched your filters.')
        return
    if display == 'short':
        table = []
        for s in results:
            table.append([
                s.id,
                s.machine_name,
                s.name,
                s.repo_created.strftime("%b %d, %Y %I:%M:%S %p"),
                s.repo_modified.strftime("%b %d, %Y %I:%M:%S %p")
            ])
        print(tabulate(table, headers=['ID', 'Machine name', 'Human name', 'Repo Created', 'Repo Modified']))
    else:
        pp = pprint.PrettyPrinter(indent=2)
        pp.pprint(results)


@software.command('update', short_help='Update fields on a Software object')
@click.argument('identifier')
@click.option('--trello-board-url', default="unset", help="Set the Trello Board URL")
@click.option('--documentation-url', default="unset", help="Set the Documentation URL")
@click.option('--name', default="unset", help="Set the human name")
@click.pass_context
def software_update(ctx, identifier, trello_board_url, documentation_url, name):
    """
    Print a detailed description of a piece of software.
    """
    api = SoftwareEndpoint(ctx.obj['brigid_client'])
    try:
        results = api.update(
            identifier,
            trello_board_url=trello_board_url,
            documentation_url=documentation_url,
            name=name
        )
    except SoftwareEndpoint.UpdateFailed as e:
        click.secho(e.msg, fg='red')
        for k, v in e.errors.items():
            click.secho(k + ':', fg='yellow')
            if isinstance(v, list):
                for error in v:
                    click.secho('    ' + error, fg='white')
            else:
                click.secho('    ' + v, fg='white')
    else:
        click.secho(f'Updated Software({identifier}):', fg='red')
        for k, v in results:
            click.secho(f'{k}={v}')


@software.command('details', short_help='Show details of one software object')
@click.argument('identifier')
@click.option(
    '--display',
    type=click.Choice(['details', 'raw']),
    default='details',
    help="Configure how to display the record.  Choices: details, raw"
)
@click.pass_context
def software_details(ctx, identifier, display):
    """
    Print a detailed description of a piece of software.
    """
    api = SoftwareEndpoint(ctx.obj['brigid_client'])
    try:
        software = api.retrieve(identifier, expand='software.applications,software.authors')
    except SoftwareEndpoint.DoesNotExist as e:
        click.secho(str(e), fg='red')
    except SoftwareEndpoint.OperationFailed as e:
        click.secho(e.msg, fg='red')
        for k, v in e.errors.items():
            click.secho(k + ':', fg='yellow')
            if isinstance(v, list):
                for error in v:
                    click.secho('    ' + error, fg='white')
            else:
                click.secho('    ' + v, fg='white')
    if display != 'raw':
        click.secho(f'\n{software.name}:', fg='cyan', bold=True)
        click.secho(f'  id          :     {software.id}', fg='white')
        click.secho(f'  machine_name:     {software.machine_name}', fg='white')
        click.secho(f'  description :     {software.description}', fg='white')
        click.secho(f'  created     :     {software.created.strftime("%b %d, %Y %I:%M:%S %p")}', fg='white')
        click.secho(f'  modified    :     {software.modified.strftime("%b %d, %Y %I:%M:%S %p")}', fg='white')
        click.secho('  Authors', fg='green')
        for author in software.authors:
            notes = ''
            if 'notes' in author and author['notes']:
                notes = f' [{author["notes"]}]'
            click.secho(f'    {author["fullname"]} <{author["email"]}>{notes}')
        click.secho('  Git repository', fg='green')
        click.secho(f'     repo url :     {software.git_repo_url}', fg='white')
        click.secho(f'     created  :     {software.repo_created.strftime("%b %d, %Y %I:%M:%S %p")}', fg='white')
        click.secho(f'     modified :     {software.repo_modified.strftime("%b %d, %Y %I:%M:%S %p")}', fg='white')
        click.secho('  Related URLs', fg='green')
        click.secho(f'     Docs     :     {software.trello_board_url}', fg='white')
        click.secho(f'     Trello   :     {software.documentation_url}', fg='white')
        click.secho(f'     Code drop:     {software.artifact_repo_url}', fg='white')
    else:
        pp = pprint.PrettyPrinter(indent=2)
        pp.pprint(software.to_dict())


@software.command('import', short_help='Import a repository into Brigid')
@click.argument('repository')
@click.pass_context
def software_do_import(ctx, repository):
    api = SoftwareEndpoint(ctx.obj['brigid_client'])
    try:
        software_id, created = api.import_repository(repository)
    except SoftwareEndpoint.OperationFailed as e:
        click.secho(f'{e.msg}: {e.errors}', fg='red')
    else:
        if created:
            click.secho(f"Success: created new Software(id={software_id})", fg='white')
        else:
            click.secho(f"Success: updated existing Software(id={software_id})", fg='cyan')


@software.command('sync', short_help='Sync data for an existing Software from its upstream git provider')
@click.argument('machine_name')
@click.pass_context
def software_do_sync(ctx, machine_name):
    results = software_list.sync(
        client=ctx.obj['brigid_client'],
        machine_name=machine_name
    ).results

    if len(results) > 1:
        click.secho(f'More than one Software object matches "{machine_name}".  Be more specific.', fg='red')
    elif len(results) == 0:
        click.secho(f'Could not find a Software object that matches "{machine_name}"',  fg='red')
    else:
        software_id = results[0].id
    response = software_sync.sync_detailed(client=ctx.obj['brigid_client'], id=software_id)
    try:
        results = json.loads(response.content.decode('utf8'))
    except json.decoder.JSONDecodeError:
        print(response.content)
    if response.status_code == 200:
        click.secho(f"Success: updated existing Software(id={results['id']})", fg='cyan')
    else:
        click.secho(f"Failed: {results['errors']}", fg='red')


def main():
    cli(obj={})


if __name__ == '__main__':
    main()
