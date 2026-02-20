document.addEventListener("alpine:init", () => {
    Alpine.data("auctionManager", () => ({
        // Stato Globale
        assets: [],
        loading: false,
        message: '',
        assetId: '',
        showAssetForm: false,
        showModal: false,

        // Campi Form Asset
        title: '', type: '', locat: '', descr: '', size: '', price: '',

        // Campi Form Asta
        startTime: '', endTime: '', startPrice: '', minIncrement: '',

        // Funzione che parte all'avvio
        async init() {
            await this.fetchAssetsByUserID();
        },

        // Getter per comodità
        get hasAssets() {
            return this.assets.length > 0;
        },

        async fetchAssetsByUserID() {
            this.loading = true;
            try {
                const token = localStorage.getItem('Authorization') || sessionStorage.getItem('Authorization');
                if (!token) {
                    window.location.href = "/login";
                    return;
                }
                const response = await fetch("/api/v1/assets/user", {
                    method: "GET",
                    headers: {
                        "Authorization": token,
                        "Content-Type": "application/json"
                    }
                });

                const res_data = await response.json();
                // console.log(res_data);
                // console.log("Assets recuperati:", res_data.data.assets);
                // console.log("Response status:", response.status);
                if (response.status === 200 && res_data.status === "success") {
                    this.assets = res_data.data.assets;
                }
            } catch (error) {
                console.error("Errore nel recupero asset:", error);
            } finally {
                this.loading = false;
            }
        },

        async create_assets() {
            try {
                const token = localStorage.getItem('Authorization') || sessionStorage.getItem('Authorization');

                const fileInput = this.$refs.picture;
                const formData = new FormData();
                if (fileInput.files[0]) {
                    formData.append('picture', fileInput.files[0]);
                }
                formData.append('title', this.title);
                formData.append('type', this.type);
                formData.append('locat', this.locat);
                formData.append('descr', this.descr);
                formData.append('size', this.size);
                formData.append('price', this.price);

                const response = await fetch("/api/v1/assets", {
                    method: "POST",
                    headers: {
                        "Authorization": token
                    },
                    body: formData
                });

                
                if (response.ok) {
                    this.message = "Asset creato con successo! Ora puoi procedere a creare l'asta.";
                    this.showModal = true;
                    this.title = '';
                    this.type = '';
                    this.locat = '';
                    this.descr = '';
                    this.size = '';
                    this.price = '';
                    await this.fetchAssetsByUserID(); // Ricarica la lista e switcha il form
                } else {
                    this.message = "Errore nella creazione dell'asset";
                }
            } catch (error) {
                this.message = "Errore: " + error.message;
            }
        },

        async create_auction() {
            const token = sessionStorage.getItem("Authorization") || localStorage.getItem("Authorization");
            
            if (!this.assetId || !this.startTime || !this.endTime) {
                this.message = "Compila tutti i campi obbligatori";
                return;
            }

            try {
                const response = await fetch("/api/v1/auctions", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": token
                    },
                    body: JSON.stringify({
                        assetId: this.assetId,
                        startTime: this.startTime,
                        endTime: this.endTime,
                        startingPrice: parseFloat(this.startPrice),
                        minIncr: parseFloat(this.minIncrement)
                    })
                });
                
                if (response.ok) {
                    //window.location.href = "/auctions"; // Reindirizza alla pagina delle aste dopo la creazione
                    window.location.href = "/";
                } else {
                    this.message = "Errore nella creazione dell'asta";
                }
            } catch (error) {
                this.message = "Errore: " + error.message;
            }
        }
    }));
});