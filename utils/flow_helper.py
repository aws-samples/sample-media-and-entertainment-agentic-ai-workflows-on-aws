import json


def replace_placeholders(obj, helper_dict):
    """
    This recursive function replaces any templates that have been defined
    in the value of a dictionary or list item
    Args:
        obj: dictionary or list to be processed
        helper_dict: dictionary used to fill in templated value
         strings in JSON

    Returns:
        obj: dictionary or list with all templates replaced
    """
    if helper_dict is None:
        return obj
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, (dict, list)):
                replace_placeholders(value, helper_dict)
            elif isinstance(value, str):
                for placeholder, replacement in helper_dict.items():
                    if f"{{{placeholder}}}" in value:
                        obj[key] = value.format(**helper_dict)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            if isinstance(item, (dict, list)):
                replace_placeholders(item, helper_dict)
            elif isinstance(item, str):
                for placeholder, replacement in helper_dict.items():
                    if f"{{{placeholder}}}" in item:
                        obj[i] = item.format(**helper_dict)
    return obj


def load_and_fill_json(json_file_path, helper_dict):
    """
    This function loads a JSON file and passes it to a recursive
    function that replaces any templates that have been defined
    in the value of a dictionary or list item
    Args:
        json_file_path: path of JSON file
        helper_dict: dictionary used to fill in templated value
         strings in JSON

    Returns:

    """
    try:
        # Load the JSON file
        with open(json_file_path, 'r') as file:
            json_data = json.load(file)

        # Replace all placeholders in the JSON
        json_data = replace_placeholders(json_data, helper_dict)
        return json_data
    except Exception as e:
        print(f"Error loading or processing JSON file: {e}")
        return None


def make_connection(source_node, target_node):
    """
    Helper function to connect Bedrock Flow nodes.
    Note that this help function only works in simple cases.
    Args:
        source_node: source Flow node whose output needs to be connected
        target_node: source Flow node whose input needs to be connected

    Returns:
        A dictionary that is used to make connections between
        two Flow nodes, which have been procedurally created
    """
    return {
        "name": "_".join([source_node["name"], target_node["name"]]),
        "source": source_node["name"],
        "target": target_node["name"],
        "type": "Data",
        "configuration": {
            "data": {
                "sourceOutput": source_node["outputs"][0]["name"],
                "targetInput": target_node["inputs"][0]["name"]
            }
        }
    }
