function auctionList() {
	return {
		auctions: [],
		loading: false,

		async fetchAuctions() {
			this.loading = true;
			try {
				// Sostituisci con il tuo endpoint API reale
				const response = await fetch("/api/v1/auctions");
				const data = await response.json(); // status -> success nelle api di Arcieri
				console.log("Aste recuperate:", data);
				console.log("data status:", data.status);
				console.log("data.data", data.data);
				// fare funzione che prende immagini da cartelle su webserver, con nome corrispondente all'id dell'asta, e le aggiunge agli oggetti delle aste
				//cicla su data.data, per ogni valore prendere il campo key di auction_Data
				data.data.forEach(element => {
					console.log("Elemento dell'array:", element.auction_data.key);
				});
				if (data.success === true) {
					//console.log("Aste recuperate con successo:", data.data);
					this.auctions = data.data.map(element => {
						return {
							id: element.auction_data.key
						};
					});
				}
				console.log(this.auctions.length)
			} catch (error) {
				console.error("Errore nel recupero delle aste:", error);
			} finally {
				this.loading = false;
			}
		},
	};
}
