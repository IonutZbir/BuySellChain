document.addEventListener("alpine:init", () => {
	Alpine.data("signinForm", () => ({
		name: "",
		surname: "",
		email: "",
		password: "",
		birthday: "",
		cellularNumber: "",
		taxCode: "",
		isVendor: false,
		message: "",

		get isPhoneValid() {
			if (!this.cellularNumber) return true;
			// Regex basilare: accetta un eventuale + iniziale e poi solo numeri (da 8 a 15 cifre)
			const phoneRegex = /^\+?[0-9]{8,15}$/;
			return phoneRegex.test(this.cellularNumber);
		},

		get maxBirthday() {
			const today = new Date();
			const year = today.getFullYear() - 18;
			const month = String(today.getMonth() + 1).padStart(2, "0");
			const day = String(today.getDate()).padStart(2, "0");
			return `${year}-${month}-${day}`; // Formato YYYY-MM-DD
		},

		// Controlla se l'età è valida (per il messaggio di errore)
		get isAgeValid() {
			if (!this.birthday) return true;
			return this.birthday <= this.maxBirthday;
		},

		get emailError() {
			if (!this.email) return "";
			return !/^\S+@\S+\.\S+$/.test(this.email) ? "Email non valida" : "";
		},

		get isTaxCodeValid() {
			if (!this.isVendor) return true;
			if (this.taxCode === "") return true;

			const cfRegex = /^[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]$/i;
			return cfRegex.test(this.taxCode);
		},

		async signin_request() {
			const payload = {
				name: this.name,
				surname: this.surname,
				email: this.email,
				cellularNumber: this.cellularNumber,
				password: this.password,
				birthday: this.birthday,
				isVendor: this.isVendor,
				// Invia il codice fiscale solo se è un venditore
				taxCode: this.isVendor ? this.taxCode : null,
			};

			try {
				const response = await fetch("/api/v1/auth/signin", {
					method: "POST",
					headers: { "Content-Type": "application/json" },
					body: JSON.stringify(payload),
				});

				const result = await response.json();

				if (response.status == 400 || response.status == 409) {
					this.message = result.data.message;
					return;
				} else if (!response.ok) {
					this.message = "Errore del server. Riprova più tardi.";
					return;
				}
				if (result.data.authorization) {
					sessionStorage.setItem(
						"Authorization",
						`Bearer ${result.data.authorization}`,
					);
					localStorage.setItem(
						"Authorization",
						`Bearer ${result.data.authorization}`,
					);
				}

				window.location.href = "/";
			} catch (error) {
				console.error("Errore durante la registrazione:", error);
				this.message = "Errore di connessione.";
			}
		},
	}));
});
