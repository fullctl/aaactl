import json

def strip_api_fields(data):
    """
    created and updated fields will change with every test run
    so strip them out
    """
    if isinstance(data, dict):
        values = data.values()
    elif isinstance(data, list):
        values = data

    for v in values:
        if isinstance(v, dict):
            v.pop("created",None)
            v.pop("updated",None)
            v.pop("org_id", None)
            v.pop("id", None)
            strip_api_fields(v)
        if isinstance(v, list):
            strip_api_fields(v)
    return data


def assert_expected(response, expected):
    assert response.status_code == expected["status"]
    if isinstance(expected["response"], dict):
        print(json.dumps(strip_api_fields(response.json())))
        assert strip_api_fields(response.json()) == expected["response"]
    else:
        print(response.content.decode("utf-8"))
        assert response.content.decode("utf-8") == expected["response"]


