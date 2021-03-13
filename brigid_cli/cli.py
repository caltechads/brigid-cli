#!/usr/bin/env python
import sys

import click

import brigid_cli
from brigid_api_client.client import AuthenticatedClient
from .settings import Settings


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
