document.addEventListener("alpine:init", () => {
    Alpine.data("profileForm", () => ({
        loading: false,
        saving: false,
        message: "",
        isError: false,
        form: {
            id: "",
            name: "",
            surname: "",
            email: "",
            birthday: "",
            cellularNumber: "",
            role: "",
            taxCode: "",
        },

        getAuthHeaders() {
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
            await this.fetchProfile();
        },

        async fetchProfile() {
            this.loading = true;
            this.message = "";
            this.isError = false;

            try {
                const headers = this.getAuthHeaders();
                if (!headers) {
                    return;
                }

                const response = await fetch("/api/v1/auth/profile", {
                    method: "GET",
                    headers,
                });

                const payload = await response.json();

                if (response.ok && payload?.status === "success") {
                    const data = payload.data || {};
                    this.form.id = data.id || "";
                    this.form.name = data.name || "";
                    this.form.surname = data.surname || "";
                    this.form.email = data.email || "";
                    this.form.birthday = data.birthday || "";
                    this.form.cellularNumber = data.cellularNumber || "";
                    this.form.role = data.role || "";
                    this.form.taxCode = data.taxCode || "";
                } else {
                    this.isError = true;
                    this.message = payload?.data?.message || "Impossibile recuperare il profilo.";
                }
            } catch (error) {
                console.error(error);
                this.isError = true;
                this.message = "Errore di rete durante il recupero del profilo.";
            } finally {
                this.loading = false;
            }
        },
    }));
});
