import os


def environment_callback(request):
    env = os.getenv("ENV", "dev")
    env_mapping = {
        "prod": ["Produccion", "danger"],
        "staging": ["Staging", "warning"],
        "dev": ["Desarrollo", "info"],
        "local": ["Local", "success"],
    }
    return env_mapping.get(env, ["Unknown", "info"])
