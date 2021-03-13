import click


def color(value, **kwargs):
    """
    Render the string with click.style().
    """
    return click.style(str(value), **kwargs)
