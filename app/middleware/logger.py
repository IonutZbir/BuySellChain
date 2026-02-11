import time
from flask import request, g, current_app

def register_logger_middleware(app):
    """
    Registra i decoratori before e after request per loggare le performance.
    """

    @app.before_request
    def start_timer():
        # Salviamo il timestamp di inizio
        g.start_time = time.time()

    @app.after_request
    def log_request(response):
        # Evitiamo di loggare le richieste per i file statici (CSS, JS, immagini)
        # per non sporcare troppo il file app.log
        if request.path.startswith('/static'):
            return response

        # Calcoliamo la durata
        diff = time.time() - g.start_time
        duration = round(diff, 4)
        
        # Estraiamo le info
        status = response.status_code
        method = request.method
        path = request.path
        ip = request.remote_addr

        # Formattiamo il messaggio
        log_msg = f"[{ip}] {method} {path} - {status} ({duration}s)"

        if status >= 500:
            current_app.logger.error(log_msg)
        elif status >= 400:
            current_app.logger.warning(log_msg)
        else:
            current_app.logger.info(log_msg)

        return response