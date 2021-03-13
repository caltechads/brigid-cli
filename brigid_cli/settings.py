from pathlib import Path  # python3 only
from jinja2 import FileSystemLoader, Environment
from pydantic import BaseSettings

from .filters import color


templates_path = Path(__file__).parent / 'templates'
jinja_env = Environment(
    loader=FileSystemLoader(str(templates_path))
)
jinja_env.filters['color'] = color


class Settings(BaseSettings):
    """
    See https://pydantic-docs.helpmanual.io/#settings for details on using and overriding this.
    """
    brigid_api_token: str = None
    brigid_base_url: str = 'https://brigid-prod.api.caltech.edu/api/v1'

    debug: bool = False

    class Config:
        env_file = '.env'
        fields = {
            'brigid_api_token': {'env': 'BRIGID_API_TOKEN'},
            'brigid_base_url': {'env': 'BRIGID_BASE_URL'},
            'debug': {'env': 'DEBUG'},
        }
