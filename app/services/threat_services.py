import re
import json
from datetime import datetime

from flask import current_app
import requests
from app import bcrypt
from app.services.guile_services import GuileService
from app.services.log_services import LogService
from app.models.models import LogType


class ThreatService:
    @staticmethod
    def _preprocess_logs(logs):
        """Preprocessing dei log per ridurne la dimensione e aumentare rilevanza.

        - Estrae solo campi essenziali
        - Raggruppa log simili
        - Filtra log meno rilevanti
        - Limita il payload totale
        """
        if not logs or not isinstance(logs, list):
            return []

        # Estrai solo campi essenziali
        essential_logs = []
        seen_signatures = set()

        for log in logs:
            if not isinstance(log, dict):
                continue

            # Estrai campi rilevanti per sicurezza
            essential = {
                "level": log.get("level", "INFO"),
                "method": log.get("method", "-"),
                "from_ip": log.get("from_ip", "-"),
                "message": log.get("message", ""),
                "user_agent": log.get("user_agent", "-")[:50],  # Limita user_agent
            }

            # Crea una firma per raggruppare log simili
            signature = (
                essential["level"],
                essential["method"],
                essential["from_ip"],
                essential["message"][:100],  # First 100 chars
            )

            # Evita duplicati esatti
            if signature not in seen_signatures:
                # Filtra log poco rilevanti (esempio: solo INFO da "system")
                if essential["level"] == "INFO" and essential["from_ip"] == "system":
                    continue

                essential_logs.append(essential)
                seen_signatures.add(signature)

        # Limitazione: prendi max 15 log più recenti
        preprocessed = essential_logs[-15:] if len(essential_logs) > 15 else essential_logs

        return preprocessed

    @staticmethod
    def analyze_logs(logs):
        """Chiama Ollama HTTP /api/generate per analizzare una lista di log e restituisce il risultato parsato.

        Si aspetta `logs` come lista di dizionari (come ritorna LogService.list_logs).
        """
        # Preprocessing: riduce il payload
        preprocessed_logs = ThreatService._preprocess_logs(logs)

        if not preprocessed_logs:
            return {"error": "no_relevant_logs", "detail": "Nessun log rilevante da analizzare"}

        # prompt = f"""
        # You are an AI security analyst monitoring the 'BuySellChain' platform.

        # CRITICAL INSTRUCTIONS:
        # 1. Base your analysis STRICTLY AND ONLY on the provided logs.
        # 2. DO NOT hallucinate or assume events (e.g., do not invent multiple login attempts if only one log is provided).
        # 3. Evaluate the logs against the specific System Baseline below. ANY deviation MUST be treated with suspicion.

        # BUYSELLCHAIN SYSTEM BASELINE & KNOWN THREATS:
        # - Normal Flows: Standard browser navigation, login, and bidding are normal. The canonical seller flow is Login -> Create Asset -> Create Auction.
        # - Unauthorized Access: Accessing protected routes (e.g., /auctions/create, /assets, /admin) without authentication, or bypassing the frontend, is a severe anomaly.
        # - Suspicious User Agents: Requests originating from tools like 'curl', 'sqlmap', 'Nmap', or non-standard browsers strongly indicate automated scripts, bots, or penetration testing.
        # - Credential Stuffing / Brute Force: Anomalous spikes in POST requests to /auth/login.
        # - Enumeration: Anomalous spikes in GET requests to /admin/users.
        # - DoS / Overflood: Sudden spikes in POST requests to /bids, /auctions, or /assets.
        # - Injection / XSS: Presence of HTML tags, JS scripts in descriptions, or escape characters in JSON payloads indicates XSS or Lisp Command Injection attempts.
        # - Network Anomalies: Unexpected traffic routing or bypassing the NGINX Reverse Proxy.

        # Analyze the provided application logs and return ONLY a JSON object with the following shape:

        # {{
        #   "severity": "INFO|LOW|MEDIUM|HIGH|ALERT|CRITICAL",
        #   "attack_type": "...",
        #   "confidence": 0.0,
        #   "explanation": "...",
        #   "reasoning": "...",
        #   "remediation": "..."
        # }}

        # Logs:
        # {json.dumps(logs)}
        # """

        prompt = f"""
        You are an AI security analyst monitoring the 'BuySellChain' platform.

        CRITICAL INSTRUCTIONS:
        1. Base your analysis STRICTLY AND ONLY on the provided logs.
        2. DO NOT hallucinate or assume events.
        3. Evaluate the logs against the System Baseline below.
        4. You MUST output EXACTLY ONE valid JSON object. If you detect multiple threats, AGGREGATE them into a single response, picking the highest severity and describing all of them in the 'explanation'.

        BUYSELLCHAIN SYSTEM BASELINE & KNOWN THREATS:
        - Normal Flows: Standard browser navigation, login, and bidding are normal. The canonical seller flow is Login -> Create Asset -> Create Auction The canonical buyer flow is Login -> Browse Auctions -> Place Bid.
        - Unauthorized Access: Accessing protected routes (e.g., /auctions/create, /assets, /admin) without authentication, or bypassing the frontend, is a severe anomaly.
        - Suspicious User Agents: Requests originating from tools like 'curl', 'sqlmap', 'Nmap', or non-standard browsers strongly indicate automated scripts, bots, or penetration testing.
        - Credential Stuffing / Brute Force: Anomalous spikes in POST requests to /auth/login. If the logs show multiple failed login attempts (at least 5) or a high volume of login requests from the same IP, this is a strong indicator of credential stuffing or brute force attacks.
        - Enumeration: Anomalous spikes in GET requests to /admin/users.
        - DoS / Overflood: Sudden spikes in POST requests to /bids, /auctions, or /assets.
        - Injection / XSS: HTML tags, JS scripts in descriptions, or escape characters in JSON payloads indicate XSS or Command Injection.

        Return ONLY ONE JSON object with this exact shape:
        {{
          "severity": "INFO|LOW|MEDIUM|HIGH|ALERT|CRITICAL",
          "attack_type": "...",
          "confidence": 0.0,
          "explanation": "...",
          "reasoning": "...",
          "remediation": "..."
        }}

        Logs:
        {json.dumps(preprocessed_logs)}
        """

        ollama_url = current_app.config.get("OLLAMA_URL")
        if not ollama_url:

            return {"error": "ollama_url_missing", "detail": "URL del servizio Ollama non configurato"}

        model_name = current_app.config.get("OLLAMA_MODEL_NAME", "qwen3.5")
        if isinstance(model_name, str):
            model_name = model_name.strip().strip('"').strip("'")

        timeout_seconds = int(current_app.config.get("OLLAMA_REQUEST_TIMEOUT", 60))

        payload = {
            "model": model_name,
            "prompt": prompt,
            "format": "json",
            "stream": False,
            "options": {
                "temperature": 0.1,
            },
        }

        try:
            response = requests.post(ollama_url, json=payload, timeout=timeout_seconds)
        except requests.exceptions.Timeout as e:
            LogService.record_log(message=f"ThreatService: Ollama HTTP timeout after {timeout_seconds}s", level=LogType.ALERT, from_ip="system", user_agent="system", method="POST")
            return {"error": "ollama_timeout", "detail": f"Timeout verso Ollama HTTP dopo {timeout_seconds}s"}
        except requests.exceptions.RequestException as e:
            LogService.record_log(message=f"ThreatService: Ollama HTTP request failed: {str(e)}", level=LogType.ALERT, from_ip="system", user_agent="system", method="POST")
            return {"error": "ollama_request_failed", "detail": str(e)}

        if response.status_code != 200:
            detail = None
            try:
                detail = response.json()
            except Exception:
                detail = response.text
            LogService.record_log(message=f"ThreatService: Ollama HTTP error {response.status_code}: {detail}", level=LogType.ALERT, from_ip="system", user_agent="system", method="POST")
            return {"error": "ollama_http_error", "detail": detail}

        try:
            response_json = response.json()
        except ValueError:
            ai_text = response.text.strip()
            if not ai_text:
                return {"error": "empty_ollama_output", "detail": "Nessun output da Ollama HTTP"}
            try:
                parsed = json.loads(ai_text)
                parsed["raw"] = ai_text
                return parsed
            except Exception:
                LogService.record_log(message="ThreatService: Ollama returned non-JSON text (HTTP)", level=LogType.INFO, from_ip="system", user_agent="system", method="POST")
                return {"raw": ai_text}

        # Se l'API Ollama restituisce un campo `response`, usalo come testo principale
        if isinstance(response_json, dict) and "response" in response_json:
            response_content = response_json.get("response")
            
            # AGGIUNTA: Gestione del comportamento di Qwen e modelli con "thinking"
            # Se 'response' è vuota ma c'è del testo in 'thinking', usiamo 'thinking'
            if (not response_content or str(response_content).strip() == "") and "thinking" in response_json:
                 thinking_content = response_json.get("thinking")
                 if thinking_content and str(thinking_content).strip():
                      response_content = thinking_content

            if isinstance(response_content, (dict, list)):
                ai_text = json.dumps(response_content, ensure_ascii=False)
            else:
                ai_text = str(response_content or "").strip()
            if ai_text:
                try:
                    # Rimuoviamo eventuali tag XML come <think> se presenti
                    import re
                    json_match = re.search(r'\{.*\}', ai_text, re.DOTALL)
                    text_to_parse = json_match.group(0) if json_match else ai_text

                    parsed = json.loads(text_to_parse)
                    parsed["raw"] = ai_text
                    
                    return parsed
                except Exception:
                    LogService.record_log(message="ThreatService: Ollama returned unparsed response field", level=LogType.INFO, from_ip="system", user_agent="system", method="POST")
                    return {"raw": ai_text, "meta": {"model": response_json.get("model"), "created_at": response_json.get("created_at")}}

        # Estrarre il testo di output dall'API Ollama (Fallback generico)
        def extract_ollama_text(data):
            if not isinstance(data, dict):
                return None

            choices = data.get("choices")
            if isinstance(choices, list) and len(choices) > 0:
                first = choices[0]
                if isinstance(first, dict):
                    message = first.get("message")
                    if message:
                        if isinstance(message, dict):
                            content = message.get("content")
                            if isinstance(content, str):
                                return content
                            if isinstance(content, list):
                                return "".join([item.get("text", "") for item in content if isinstance(item, dict)])
                    output = first.get("output")
                    if isinstance(output, str):
                        return output
                    if isinstance(output, list):
                        return "".join([item.get("text", "") for item in output if isinstance(item, dict)])
                    text = first.get("text")
                    if isinstance(text, str):
                        return text
            if isinstance(data.get("output"), str):
                return data.get("output")
            if isinstance(data.get("text"), str):
                return data.get("text")
            return None

        ai_text = extract_ollama_text(response_json)
        if ai_text:
            try:
                import re
                json_match = re.search(r'\{.*\}', ai_text, re.DOTALL)
                text_to_parse = json_match.group(0) if json_match else ai_text

                parsed = json.loads(text_to_parse)
                parsed["raw"] = ai_text
                
                return parsed
            except Exception:
                
                return {"raw": ai_text}

        # Se l'output non è direttamente parsabile, restituisci comunque il JSON della risposta
        return response_json