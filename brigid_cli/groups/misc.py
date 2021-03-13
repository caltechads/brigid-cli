#!/usr/bin/env python
import pprint

import click

from brigid_cli.cli import cli


@cli.command('settings', short_help="Print our application settings.")
@click.pass_context
def settings(ctx):
    """
    Print our settings to stdout.  This should be the completely evaluated settings including
    those imported from any environment variable.
    """
    pp = pprint.PrettyPrinter(indent=2)
    pp.pprint(ctx.obj['settings'].dict())
