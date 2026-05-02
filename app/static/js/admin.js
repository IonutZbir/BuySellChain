document.addEventListener("alpine:init", () => {
    Alpine.data("adminDashboard", () => ({
        stats: {},
        auctions: [],
        users: [],
        logs: [],
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
                const payload = await response.json();

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
    }));
});
