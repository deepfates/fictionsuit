from supabase import create_client


def init_supa_client():
    from .. import config

    if config.UPLOAD_TO_SUPABASE:
        url: str = config.SUPABASE_URL
        key: str = config.SUPABASE_KEY
        client = create_client(url, key)
        return client
