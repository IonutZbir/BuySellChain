document.addEventListener("alpine:init", () => {
    Alpine.data("bidForm", (initialAuctionId) => ({
        latestBid: 0,
        bidAmount: 0,
        message: '',
        auctionId: initialAuctionId,

        async init() {
            await this.fetchForLatestBid();
        },

        async fetchForLatestBid() {
            this.latestBid = 0; // Reset latestBid before fetching
            try {
                const token = localStorage.getItem('Authorization') || sessionStorage.getItem('Authorization');
                if (!token) {
                    window.location.href = "/login";
                    return;
                }
                const response = await fetch(`/api/v1/bids/latest/${this.auctionId}`, {
                    method: "GET",
                    headers: {
                        "Authorization": token,
                        "Content-Type": "application/json"
                    }
                });

                const res_data = await response.json();
                console.log("Response data for latest bid:", res_data);
                if (response.status === 200 && res_data.status === "success") {
                    
                    this.latestBid = res_data.data.latest_bid;
                    console.log("Latest bid amount:", this.latestBid);
                }
                
            } catch (error) {
                console.error("Errore nel recupero dell'offerta più recente:", error);
            }
        },

        async make_bid() {
            this.message = '';
            try {
                const token = localStorage.getItem('Authorization') || sessionStorage.getItem('Authorization');
                if (!token) {
                    window.location.href = "/login";
                    return;
                }
                const response = await fetch("/api/v1/bids", {
                    method: "POST",
                    headers: {
                        "Authorization": token,
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        auction_id: this.auctionId,
                        amount: this.bidAmount
                    })
                });

                console.log(JSON.stringify({
                        auction_id: this.auctionId,
                        amount: this.bidAmount
                    }));

                const res_data = await response.json();
                console.log("Response data:", res_data);
                
                if (response.status === 200 && res_data.status === "success") {
                    this.message = "Offerta effettuata con successo!";
                    // Aggiorna la pagina per riflettere la nuova offerta
                    setTimeout(() => location.reload(), 1500);
                } else {
                    
                    this.message = res_data.data.error || "Errore nell'effettuare l'offerta.";
                }
            } catch (error) {
                console.error("Errore nel fare l'offerta:", error);
                this.message = "Errore di rete. Riprova più tardi.";
            }
        }
    })
)
});