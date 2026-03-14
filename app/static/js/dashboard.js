document.addEventListener("alpine:init", () => {
    Alpine.data("userDashboard", () => ({
        role: "",
        userId: "",
        errorMessage: "",
        allAuctions: [],
        ownAuctions: [],
        openOwnAuctions: [],
        participatedAuctions: [],
        userBids: [],
        maxUserBidByAuction: {},
        openAuctionBids: {},
        loading: {
            global: false,
            auctions: false,
            participations: false,
            openAuctionBids: false,
        },

        async init(role, userId) {
            this.role = role || "";
            this.userId = userId || "";
            await this.refreshAll();
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

        async refreshAll() {
            this.errorMessage = "";
            this.loading.global = true;
            await Promise.all([this.fetchAuctions(), this.fetchUserBids()]);
            this.computeDerivedData();
            if (this.role === "seller") {
                await this.fetchOpenAuctionBids();
            }
            this.loading.global = false;
        },

        async fetchAuctions() {
            this.loading.auctions = true;
            try {
                const response = await fetch("/api/v1/auctions", {
                    method: "GET",
                    headers: {
                        "Content-Type": "application/json",
                    },
                });
                const payload = await response.json();

                if (response.ok && payload?.status === "success") {
                    this.allAuctions = payload?.data?.auctions || [];
                } else {
                    this.errorMessage = payload?.data?.error || payload?.message || "Impossibile recuperare le aste.";
                    this.allAuctions = [];
                }
            } catch (error) {
                console.error(error);
                this.errorMessage = "Errore di rete durante il recupero delle aste.";
                this.allAuctions = [];
            } finally {
                this.loading.auctions = false;
            }
        },

        async fetchUserBids() {
            this.loading.participations = true;
            try {
                const headers = this.getAuthHeaders();
                if (!headers) {
                    return;
                }
                const response = await fetch("/api/v1/bids/user/", {
                    method: "GET",
                    headers,
                });
                const payload = await response.json();

                if (response.ok && payload?.status === "success") {
                    this.userBids = Array.isArray(payload?.data) ? payload.data : [];
                } else {
                    this.userBids = [];
                    if (!this.errorMessage) {
                        this.errorMessage = payload?.data?.error || payload?.message || "Impossibile recuperare le offerte utente.";
                    }
                }
            } catch (error) {
                console.error(error);
                this.userBids = [];
                if (!this.errorMessage) {
                    this.errorMessage = "Errore di rete durante il recupero delle offerte utente.";
                }
            } finally {
                this.loading.participations = false;
            }
        },

        computeDerivedData() {
            const normalizeId = (auction) => auction?.auction_id || auction?.id || null;

            this.ownAuctions = this.role === "seller"
                ? this.allAuctions.filter((auction) => (auction?.seller_id || "") === this.userId)
                : [];

            this.openOwnAuctions = this.ownAuctions.filter((auction) => (auction?.status || "").toLowerCase() === "active");

            const participatedAuctionIds = new Set();
            const maxBidByAuction = {};

            this.userBids.forEach((entry) => {
                const bidData = entry?.bid_data?.value || entry?.value || {};
                const auctionId = bidData?.auction_id;
                const amount = Number(bidData?.bid_amount || 0);

                if (auctionId) {
                    participatedAuctionIds.add(auctionId);
                    const previous = Number(maxBidByAuction[auctionId] || 0);
                    if (amount > previous) {
                        maxBidByAuction[auctionId] = amount;
                    }
                }
            });

            this.maxUserBidByAuction = maxBidByAuction;

            this.participatedAuctions = this.allAuctions.filter((auction) => participatedAuctionIds.has(normalizeId(auction)));
        },

        async fetchOpenAuctionBids() {
            this.loading.openAuctionBids = true;
            this.openAuctionBids = {};
            try {
                const requests = this.openOwnAuctions.map(async (auction) => {
                    const auctionId = auction?.auction_id || auction?.id;
                    if (!auctionId) {
                        return;
                    }

                    const response = await fetch(`/api/v1/auctions/bids/${auctionId}`, {
                        method: "GET",
                        headers: {
                            "Content-Type": "application/json",
                        },
                    });

                    const payload = await response.json();
                    if (response.ok && payload?.status === "success") {
                        this.openAuctionBids[auctionId] = payload?.data?.bids || [];
                    } else {
                        this.openAuctionBids[auctionId] = [];
                    }
                });

                await Promise.all(requests);
            } catch (error) {
                console.error(error);
                if (!this.errorMessage) {
                    this.errorMessage = "Errore nel recupero delle offerte sulle aste aperte.";
                }
            } finally {
                this.loading.openAuctionBids = false;
            }
        },

        extractBidValue(bid, key) {
            if (!bid) {
                return null;
            }
            return bid?.bid_data?.value?.[key] ?? bid?.value?.[key] ?? bid?.[key] ?? null;
        },

        formatDateTime(value) {
            if (!value) {
                return "-";
            }
            const date = new Date(value);
            if (Number.isNaN(date.getTime())) {
                return value;
            }
            return date.toLocaleString("it-IT", {
                day: "2-digit",
                month: "2-digit",
                year: "numeric",
                hour: "2-digit",
                minute: "2-digit",
            });
        },

        formatCurrency(value) {
            const num = Number(value || 0);
            if (!Number.isFinite(num)) {
                return "0,00";
            }
            return num.toLocaleString("it-IT", {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
            });
        },
    }));
});
