def schematize(object):
    if hasattr(object, "sm_schematize"):
        return object.sm_schematize()
    if isinstance(object, str):
        return {"schema": "text", "value": object}
    if object is None:
        return {"schema": "nothing"}
    if isinstance(object, dict):
        if "schema" in object:
            return object

    return {"schema": "other", "description": f"{object}"}
