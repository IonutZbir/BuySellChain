from flask import jsonify

# Quando dobbiamo inviare un array di oggetti: data = {"nome_dato_plurale": array}
# Quando dobbiamo inviare uno solo: data = nome_dato_singolare

def jsend_response(status, data=None, message=None, code=200):
    response = {"status": status}
    if data is not None:
        response["data"] = data
    if message is not None:
        response["message"] = message
    return jsonify(response), code