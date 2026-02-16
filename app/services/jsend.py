from flask import jsonify

def jsend_response(status, data=None, message=None, code=200):
    response = {"status": status}
    if data is not None:
        response["data"] = data
    if message is not None:
        response["message"] = message
    return jsonify(response), code