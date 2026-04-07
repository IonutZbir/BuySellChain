document.addEventListener("alpine:init", () => {
	Alpine.data("navHandler", () => ({
		isLoggedIn: false,
		userInitials: "",

		getToken() {
			return (
				localStorage.getItem("Authorization") ||
				sessionStorage.getItem("Authorization")
			);
		},

		decodeTokenPayload(token) {
			if (!token) {
				return null;
			}

			try {
				const parts = token.split(".");
				if (parts.length < 2) {
					return null;
				}

				const base64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
				const padding = "=".repeat((4 - (base64.length % 4)) % 4);
				const payloadRaw = atob(base64 + padding);
				return JSON.parse(payloadRaw);
			} catch (err) {
				console.error("Errore nel parsing del token:", err);
				return null;
			}
		},

		computeInitials(payload) {
			const name = String(payload?.name || "").trim();
			const surname = String(payload?.surname || "").trim();

			if (name || surname) {
				const first = name ? name.charAt(0).toUpperCase() : "";
				const second = surname ? surname.charAt(0).toUpperCase() : "";
				return `${first}${second}` || "?";
			}

			const email = String(payload?.email || "").trim();
			if (email) {
				return email.charAt(0).toUpperCase();
			}

			return "?";
		},

		async refreshInitialsFromProfile(token) {
			try {
				const response = await fetch("/api/v1/auth/profile", {
					method: "GET",
					headers: {
						Authorization: token,
						"Content-Type": "application/json",
					},
				});

				const payload = await response.json();
				if (response.ok && payload?.status === "success") {
					this.userInitials = this.computeInitials(payload?.data || {});
					return true;
				}
			} catch (err) {
				console.error("Errore nel recupero profilo per iniziali:", err);
			}

			return false;
		},

		async init() {
			// Verifica se l'utente è autenticato
			const token = this.getToken();
			this.isLoggedIn = !!token;

			if (token) {
				const refreshed = await this.refreshInitialsFromProfile(token);
				if (!refreshed) {
					const payload = this.decodeTokenPayload(token);
					this.userInitials = this.computeInitials(payload);
				}
			}
		},

		async logout() {
			try {
				// Avvisa il server per pulire la sessione Flask
				await fetch("/api/v1/auth/logout", {
					method: "POST",
					headers: {
						Authorization: `${localStorage.getItem("Authorization") || sessionStorage.getItem("Authorization")}`,
					},
				});
			} catch (err) {
				console.error("Errore durante il logout lato server:", err);
			} finally {
				// Pulisce tutto e reindirizza
				localStorage.removeItem("Authorization");
				sessionStorage.removeItem("Authorization");
				this.isLoggedIn = false;
				this.userInitials = "";
				window.location.href = "/login";
				
			}
		},
	}));
});
