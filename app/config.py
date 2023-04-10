import os


class Config:
    DEBUG: bool = bool(os.environ.get('LFT_DEBUG', False))
    HOST: str = os.environ.get('LFT_HOST', 'localhost')
    PORT: int = int(os.environ.get('LFT_PORT', 8000))
    DATABASE_URI = os.environ.get(
        "LFT_DATABASE_URI",
        "postgresql://postgres:123456@localhost/list_family_trial",
    )
