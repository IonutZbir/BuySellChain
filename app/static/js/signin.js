document.addEventListener('alpine:init', () => {
    Alpine.data('signinForm', () => ({
        name: '',
        surname: '',
        email: '',
        password: '',
        birthday: '',
        cellularNumber: '',
        message: '',

        get emailError() {
			if (!this.email) return "";
			return !/^\S+@\S+\.\S+$/.test(this.email) ? "Email non valida" : "";
		},

        async signin_request() {
            const payload = {
                name: this.name,
                surname: this.surname,
                email: this.email,
                cellularNumber: this.cellularNumber,
                password: this.password,
                birthday: this.birthday
            };

            try {
                const response = await fetch('/api/v1/auth/signin', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                const result = await response.json();
                
                if (response.status == 400 || response.status == 409){
                    this.message = result.data.message;
                    return
                }else if (!response.ok) {
                    this.message = "Errore del server. Riprova più tardi.";
                    return;
                }
                if (result.data.authorization) {
                    sessionStorage.setItem('Authorization', `Bearer ${result.data.authorization}`);
                }

                window.location.href = '/';
            } catch (error) {
                console.error("Errore durante la registrazione:", error);
                this.message = "Errore di connessione.";
            }
        }
    }))
})