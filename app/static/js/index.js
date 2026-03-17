function auctionList() {
	return {
		auctions: [],
		loading: false,

		async fetchAuctions() {
			this.loading = true;
			try {
				// Sostituisci con il tuo endpoint API reale
				const response = await fetch("/api/v1/auctions", {
					method: "GET",
					headers: {
						"Content-Type": "application/json",
					},
				});
				const res_data = await response.json(); // status -> success nelle api di Arcieri

				// fare funzione che prende immagini da cartelle su webserver, con nome corrispondente all'id dell'asta, e le aggiunge agli oggetti delle aste
				//cicla su data.data, per ogni valore prendere il campo key di auction_Data
				// console.log(res_data);
				console.log("Aste recuperate:", res_data.data.auctions);
				if (response.status === 200 && res_data.status === "success") {
					this.auctions = res_data.data.auctions;
				}
			} catch (error) {
				console.error("Errore nel recupero delle aste:", error);
			} finally {
				this.loading = false;
			}
		},
	};
}
