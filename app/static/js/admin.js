document.addEventListener("alpine:init", () => {
    Alpine.data("adminDashboard", () => ({
        stats: {},
        auctions: [],
        users: [],
        logs: [],
        analysisResult: null,
        analysisRawOutput: "",
        analysisError: "",
        analysisLoading: false,
        analysisPopupOpen: false,
        analysisPopupStatus: "",
        popupTypedOutput: "",
        filterSeverity: "",
        filterText: "",
        selectAllLogs: false,
        selectedLogIds: [],
        globalLoading: false,
        errorMessage: "",
        loading: {
            stats: false,
            auctions: false,
            users: false,
            logs: false,
        },

        getAuthHeader() {
            const token = localStorage.getItem("Authorization") || sessionStorage.getItem("Authorization");
            if (!token) {
                window.location.href = "/login";
                return null;
            }
            return {
                Authorization: token,
                "Content-Type": "application/json",
            };
        },

        async init() {
            await this.refreshAll();
        },

        async refreshAll() {
            this.errorMessage = "";
            this.globalLoading = true;

            await Promise.all([
                this.fetchStats(),
                this.fetchAuctions(),
                this.fetchUsers(),
                this.fetchLogs(),
            ]);

            this.globalLoading = false;
        },

        async fetchStats() {
            this.loading.stats = true;
            try {
                const headers = this.getAuthHeader();
                if (!headers) {
                    return;
                }
                const response = await fetch("/api/v1/admin/stats", {
                    method: "GET",
                    headers,
                });
                const payload = await response.json();

                if (response.ok && payload?.status === "success") {
                    this.stats = payload?.data?.stats || {};
                    console.debug("Stats loaded:", this.stats);
                    return;
                }
                this.handleApiError(payload, "Impossibile caricare le statistiche.");
            } catch (error) {
                this.errorMessage = "Errore nel caricamento delle statistiche.";
                console.error(error);
            } finally {
                this.loading.stats = false;
            }
        },

        async fetchAuctions() {
            this.loading.auctions = true;
            try {
                const headers = this.getAuthHeader();
                if (!headers) {
                    return;
                }
                const response = await fetch("/api/v1/admin/auctions", {
                    method: "GET",
                    headers,
                });
                const payload = await response.json();

                if (response.ok && payload?.status === "success") {
                    this.auctions = payload?.data?.auctions || [];
                    return;
                }

                this.handleApiError(payload, "Impossibile caricare le aste.");
            } catch (error) {
                this.errorMessage = "Errore nel caricamento delle aste.";
                console.error(error);
            } finally {
                this.loading.auctions = false;
            }
        },

        async fetchUsers() {
            this.loading.users = true;
            try {
                const headers = this.getAuthHeader();
                if (!headers) {
                    return;
                }
                const response = await fetch("/api/v1/admin/users", {
                    method: "GET",
                    headers,
                });
                const payload = await response.json();

                if (response.ok && payload?.status === "success") {
                    this.users = payload?.data?.users || [];
                    return;
                }

                this.handleApiError(payload, "Impossibile caricare gli utenti.");
            } catch (error) {
                this.errorMessage = "Errore nel caricamento degli utenti.";
                console.error(error);
            } finally {
                this.loading.users = false;
            }
        },

        async fetchLogs() {
            this.loading.logs = true;
            try {
                const headers = this.getAuthHeader();
                if (!headers) {
                    return;
                }
                const response = await fetch("/api/v1/admin/logs", {
                    method: "GET",
                    headers,
                });
                const payload = await this.parseJsonSafely(response);

                if (response.ok && payload?.status === "success") {
                    this.logs = (payload?.data?.logs || []).map((entry) => ({
                        ...entry,
                        level: String(entry.level || "ok").toUpperCase(),
                    }));
                    return;
                }

                this.handleApiError(payload, "Impossibile caricare i log.");
            } catch (error) {
                this.errorMessage = "Errore nel caricamento dei log.";
                console.error(error);
            } finally {
                this.loading.logs = false;
            }
        },
        isTyping: false, // <-- Aggiungi questa variabile allo stato iniziale

        async analyzeLogs() {
            this.analysisError = "";
            this.analysisResult = null;
            this.analysisRawOutput = "";
            
            // AGGIUNTA: Messaggio di attesa per riempire il pop-up vuoto
            this.popupTypedOutput = "> Connessione al modello di AI in corso...\n> Lettura dei log e generazione dell'analisi (potrebbe richiedere alcuni secondi)...";
            
            this.analysisPopupOpen = true;
            this.analysisPopupStatus = "Sto pensando...";
            this.analysisLoading = true;
            try {
                const headers = this.getAuthHeader();
                if (!headers) {
                    this.analysisPopupStatus = "Errore: token mancante";
                    return;
                }

                if (!this.selectedLogIds.length) {
                    this.analysisError = "Seleziona almeno un log da analizzare.";
                    this.analysisPopupStatus = "Seleziona log prima di analizzare.";
                    return;
                }

                // Ordina i log selezionati in base all'ordine di selezione
                const selectedLogs = this.selectedLogIds
                    .map((id) => this.logs.find((entry) => entry.id === id))
                    .filter(Boolean);

                const response = await fetch("/api/v1/analyze/analyze-logs", {
                    method: "POST",
                    headers,
                    body: JSON.stringify({ logs: selectedLogs }),
                });
                const text = await response.text();
                const payload = this.safeParseJson(text);

                if (response.ok && payload?.status === "success") {
                    this.analysisResult = payload?.data?.analysis || payload?.data || null;
                    const rawOutput = this.analysisResult?.raw || this.analysisResult?.response || text || JSON.stringify(this.analysisResult, null, 2);
                    this.analysisRawOutput = rawOutput;
                    this.analysisPopupStatus = "Analisi completata";
                    
                    // Svuota il messaggio di attesa prima di far partire il typewriter vero
                    this.popupTypedOutput = ""; 
                    await this.animateTypewriter(this.analysisRawOutput);
                    
                    await this.fetchLogs();
                    return;
                }

                this.analysisError = payload?.data?.error || payload?.message || payload?.rawText || "Errore nell'analisi dei log.";
                this.analysisPopupStatus = "Analisi terminata con errore";
                this.analysisRawOutput = text;
                
                // Svuota il messaggio di attesa anche in caso di errore
                this.popupTypedOutput = ""; 
                await this.animateTypewriter(this.analysisRawOutput);
            } catch (error) {
                this.analysisError = "Errore nella chiamata all'analisi log.";
                this.analysisPopupStatus = "Errore di rete durante l'analisi";
                console.error(error);
            } finally {
                this.analysisLoading = false;
            }
        },

        async animateTypewriter(text) {
            this.popupTypedOutput = "";
            this.isTyping = true; // Attiva la modalità scrittura
            if (!text) {
                this.isTyping = false;
                return;
            }
            const chars = Array.from(text);
            for (let i = 0; i < chars.length; i += 1) {
                this.popupTypedOutput += chars[i];
                // Velocità leggermente aumentata (5ms) per non far aspettare troppo l'utente
                await new Promise((resolve) => setTimeout(resolve, 5)); 
            }
            this.isTyping = false; // Termina la modalità scrittura
        },

        safeParseJson(text) {
            if (!text) {
                return { status: "fail", message: "Empty response from server", rawText: text };
            }
            try {
                return JSON.parse(text);
            } catch (error) {
                return { status: "fail", message: "Invalid JSON response", rawText: text };
            }
        },

        async animateTypewriter(text) {
            this.popupTypedOutput = "";
            if (!text) {
                return;
            }
            const chars = Array.from(text);
            for (let i = 0; i < chars.length; i += 1) {
                this.popupTypedOutput += chars[i];
                await new Promise((resolve) => setTimeout(resolve, 20));
            }
        },

        syncSelectAllState() {
            const visibleIds = this.filteredLogs().map((entry) => entry.id);
            const allSelected = visibleIds.every((id) => this.selectedLogIds.includes(id)) && visibleIds.length > 0;
            this.selectAllLogs = allSelected;
        },

        toggleSelectAll() {
            const visibleIds = this.filteredLogs().map((entry) => entry.id);
            if (this.selectAllLogs) {
                this.selectedLogIds = Array.from(new Set([...this.selectedLogIds, ...visibleIds]));
            } else {
                const visibleSet = new Set(visibleIds);
                this.selectedLogIds = this.selectedLogIds.filter((id) => !visibleSet.has(id));
            }
        },

        selectedCount() {
            return this.selectedLogIds.length;
        },

        async parseJsonSafely(response) {
            const text = await response.text();
            return this.safeParseJson(text);
        },

        filteredLogs() {
            const filterSeverity = String(this.filterSeverity || "").trim().toUpperCase();
            const filterText = String(this.filterText || "").trim().toLowerCase();

            return this.logs.filter((entry) => {
                const severity = String(entry.level || "").toUpperCase();
                if (filterSeverity && severity !== filterSeverity) {
                    return false;
                }

                if (!filterText) {
                    return true;
                }

                const text = [
                    entry.message,
                    entry.from_ip,
                    entry.method,
                    entry.user_agent,
                    entry.level,
                ]
                    .filter(Boolean)
                    .join(" ")
                    .toLowerCase();

                return text.includes(filterText);
            });
        },

        handleApiError(payload, fallbackMessage) {
            const message =
                payload?.data?.error ||
                payload?.message ||
                fallbackMessage;
            this.errorMessage = message;
        },

        formatDateTime(value) {
            if (!value) {
                return "-";
            }

            const date = new Date(value);
            if (Number.isNaN(date.getTime())) {
                return value;
            }

            return date.toLocaleString("it-IT", {
                day: "2-digit",
                month: "2-digit",
                year: "numeric",
                hour: "2-digit",
                minute: "2-digit",
            });
        },

        formatCurrency(value) {
            const num = Number(value || 0);
            return Number.isFinite(num) ? num.toLocaleString("it-IT", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : "0,00";
        },

        prettyJson(value) {
            if (value === null || value === undefined) {
                return "";
            }
            try {
                return JSON.stringify(value, null, 2);
            } catch (error) {
                return String(value);
            }
        },
    }));
});
