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
				console.log("data status:", data.success);
				console.log("data.answer.keys", data.answer.keys);
				// fare funzione che prende immagini da cartelle su webserver, con nome corrispondente all'id dell'asta, e le aggiunge agli oggetti delle aste
				
				if (data.success === true) {
					//console.log("Aste recuperate con successo:", data.data);
					this.auctions = data.answer.keys.map(key => {
						return {
							id: key,
						};
					});
				}
			} catch (error) {
				console.error("Errore nel recupero delle aste:", error);
			} finally {
				this.loading = false;
			}
		},
	};
}
