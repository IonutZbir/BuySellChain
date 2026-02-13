document.addEventListener("alpine:init", () => {
	Alpine.data("navHandler", () => ({
		isLoggedIn: false,

		init() {
			// Verifica se l'utente è autenticato
			const token =
				localStorage.getItem("Authorization") ||
				sessionStorage.getItem("Authorization");
			this.isLoggedIn = !!token;
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
				window.location.href = "/login";
			}
		},
	}));
});
