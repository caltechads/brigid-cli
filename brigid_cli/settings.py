from pydantic import BaseSettings


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
