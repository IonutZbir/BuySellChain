document.addEventListener("alpine:init", () => {
    Alpine.data("auctionManager", () => ({
        // Stato Globale
        assets: [],
        loading: false,
        message: '',
        assetId: '',

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

                const data = await response.json();
                console.log("Assets recuperati:", data);
                if (response.ok) {
                    this.assets = data.assets;
                    console.log("Assets aggiornati nello stato:", this.assets);
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
                const response = await fetch("/api/v1/assets", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": token
                    },
                    body: JSON.stringify({
                        title: this.title,
                        type: this.type,
                        locat: this.locat,
                        descr: this.descr,
                        size: this.size,
                        price: this.price
                    })
                });

                if (response.ok) {
                    this.message = '';
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