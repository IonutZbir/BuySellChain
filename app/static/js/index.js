function auctionList() {
	return {
		auctions: [],
		loading: false,

		async fetchAuctions() {
			this.loading = true;
			try {
				// Sostituisci con il tuo endpoint API reale
				const response = await fetch("/api/v1/auctions");
				const data = await response.json();

				if (data.status === "success") {
					this.auctions = data.data;
				}
			} catch (error) {
				console.error("Errore nel recupero delle aste:", error);
			} finally {
				this.loading = false;
			}
		},
	};
}
