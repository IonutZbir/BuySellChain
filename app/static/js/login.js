document.addEventListener("alpine:init", () => {
	Alpine.data("loginForm", () => ({
		email: "",
		password: "",
		remember: false,
		message: "",

        init() {
            // Pulizia sessioni precedenti per evitare conflitti
            localStorage.removeItem('Authorization');
            sessionStorage.removeItem('Authorization');
        },

		get emailError() {
			if (!this.email) return "";
			return !/^\S+@\S+\.\S+$/.test(this.email) ? "Email non valida" : "";
		},

		async login_request() {
			const payload = {
				email: this.email,
				password: this.password,
				remember: this.remember,
			};

			try {
				const response = await fetch("/api/v1/auth/login", {
					method: "POST",
					headers: {
						"Content-Type": "application/json",
					},
					body: JSON.stringify(payload),
				});

                
				const result = await response.json();

				if (response.status === 401) {
					this.message = result.data.message;
					return;
				} else if (!response.ok) {
					this.message = "Errore del server. Riprova più tardi.";
					return;
				}

				if (result.data.authorization) {
					const storage = this.remember
						? localStorage
						: sessionStorage;

					storage.setItem(
						"Authorization",
						`Bearer ${result.data.authorization}`,
					);
				}

				// Indirizza alla home dopo aver salvato il token
				window.location.href = "/";
			} catch (error) {
				console.error("Errore durante il login:", error);
				this.message = "Errore di connessione.";
			}
		},
	}));
});
