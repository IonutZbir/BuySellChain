document.addEventListener("alpine:init", () => {
    Alpine.data("bidForm", (initialAuctionId) => ({
        latestBid: 0,
        bidAmount: 0,
        message: '',
        auctionId: initialAuctionId,
        allBid: 0,
        total_rejected_bids: 0,
        total_valid_bids: 0,
        history: [],
        showHistory: false,
        formatTimestamp(rawTimestamp) {
            if (!rawTimestamp || rawTimestamp === "Unknown") {
                return "-";
            }
            
            const date = new Date(rawTimestamp);
            if (Number.isNaN(date.getTime())) {
                return "-";
            }

            const year = String(date.getUTCFullYear());
            const month = String(date.getUTCMonth() + 1).padStart(2, "0");
            const day = String(date.getUTCDate()).padStart(2, "0");
            const hours = String(date.getHours()).padStart(2, "0");
            const minutes = String(date.getUTCMinutes()).padStart(2, "0");
            const seconds = String(date.getUTCSeconds()).padStart(2, "0");
            const milliseconds = String(date.getUTCMilliseconds()).padStart(3, "0");
            
            return `${day}/${month}/${year} ${hours}:${minutes}:${seconds}.${milliseconds}`;
        },
        async init() {
            await this.fetchForLatestBid();
            await this.fetchForAllBids();
            await this.fetchBidsHistory();
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
                if (response.status === 200 && res_data.status === "success") {
                    
                    this.latestBid = res_data.data.latest_bid;
                }
                
            } catch (error) {
                console.error("Errore nel recupero dell'offerta più recente:", error);
            }
        },
        async fetchForAllBids() {
            this.allBid = 0; // Reset allBid before fetching
            try {
                const token = localStorage.getItem('Authorization') || sessionStorage.getItem('Authorization');
                if (!token) {
                    window.location.href = "/login";
                    return;
                }
                const response = await fetch(`/api/v1/bids/total/${this.auctionId}`, {
                    method: "GET",
                    headers: {
                        "Authorization": token,
                        "Content-Type": "application/json"
                    }
                });

                const res_data = await response.json();
                if (response.status === 200 && res_data.status === "success") {
                    
                    this.allBid = res_data.data.total_bids;
                    this.total_rejected_bids = res_data.data.total_rejected_bids;
                    this.total_valid_bids = res_data.data.total_valid_bids;
                }
                
            } catch (error) {
                console.error("Errore nel recupero dell'offerta più recente:", error);
            }
        },

        async fetchBidsHistory() {
            this.history = []; // Reset history before fetching
            try {
                const token = localStorage.getItem('Authorization') || sessionStorage.getItem('Authorization');
                if (!token) {
                    window.location.href = "/login";
                    return;
                }
                const response = await fetch(`/api/v1/auctions/getAuctionHistory/${this.auctionId}`, {
                    method: "GET",
                    headers: {
                        "Authorization": token,
                        "Content-Type": "application/json"
                    }
                });

                const res_data = await response.json();
                if (response.status === 200 && res_data.status === "success") {
                    if (Array.isArray(res_data?.data?.history)) {
                        this.history = res_data.data.history;
                    } else if (Array.isArray(res_data?.data)) {
                        this.history = res_data.data;
                    } else {
                        this.history = [];
                    }
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

                const res_data = await response.json();
                
                if (response.status === 200 && res_data.status === "success") {
                    this.message = "Offerta effettuata con successo!";
                    // Aggiorna la pagina per riflettere la nuova offerta
                    setTimeout(() => location.reload(), 1500);
                } else {
                    
                    this.message = res_data.data.error || "Errore nell'effettuare l'offerta.";
                    setTimeout(() => location.reload(), 1500);
                }
            } catch (error) {
                console.error("Errore nel fare l'offerta:", error);
                this.message = "Errore di rete. Riprova più tardi.";
            }
        }
    })
)
});


document.addEventListener("DOMContentLoaded", () => {
    const timerCard = document.querySelector(".create-auction-timer-card");
    const countdownEl = document.getElementById("bidWindowCountdown");
    const statusEl = document.getElementById("bidWindowStatus");
    const submitButton = document.querySelector("form button[type='submit']");

    if (!timerCard || !countdownEl || !statusEl) {
        return;
    }

    const auctionId = timerCard.getAttribute("data-auction-id");
    const auctionStartStr = timerCard.getAttribute("data-auction-start");
    const auctionEndStr = timerCard.getAttribute("data-auction-end");
    
    // Lo stato iniziale che arriva dal database ('active', 'scheduled', 'locked', 'closed')
    let previousState = timerCard.getAttribute("data-auction-status");

    const auctionStartDate = new Date(auctionStartStr);
    const auctionEndDate = new Date(auctionEndStr);

    const parseHourMinute = (timeValue, fallbackHour) => {
        if (typeof timeValue !== "string") return { hour: fallbackHour, minute: 0 };
        const [hourRaw, minuteRaw] = timeValue.split(":");
        const hour = Number.parseInt(hourRaw, 10);
        const minute = Number.parseInt(minuteRaw, 10);
        if (Number.isInteger(hour) && Number.isInteger(minute) && hour >= 0 && hour <= 23 && minute >= 0 && minute <= 59) {
            return { hour, minute };
        }
        return { hour: fallbackHour, minute: 0 };
    };

    const formatDuration = (ms) => {
        const totalSeconds = Math.max(0, Math.floor(ms / 1000));
        const days = Math.floor(totalSeconds / 86400);
        const hours = Math.floor((totalSeconds % 86400) / 3600);
        const minutes = Math.floor((totalSeconds % 3600) / 60);
        const seconds = totalSeconds % 60;
        const hh = String(hours).padStart(2, "0");
        const mm = String(minutes).padStart(2, "0");
        const ss = String(seconds).padStart(2, "0");
        if (days > 0) return `${days}g ${hh}:${mm}:${ss}`;
        return `${hh}:${mm}:${ss}`;
    };

    const computeWindowTarget = (windowStart, windowEnd) => { 
        const now = new Date();

        // 1. Costruiamo le Date+Ore reali di Inizio e Fine assoluti dell'asta
        const absoluteStart = new Date(auctionStartDate);
        absoluteStart.setHours(windowStart.hour, windowStart.minute, 0, 0);

        const absoluteEnd = new Date(auctionEndDate);
        absoluteEnd.setHours(windowEnd.hour, windowEnd.minute, 0, 0);

        // Se l'orario attuale ha superato l'ultimo minuto dell'ultimo giorno
        if (now >= absoluteEnd) {
            return { status: "Asta conclusa.", target: absoluteEnd, locked: true, closed: true };
        }

        // Se l'orario attuale precede l'apertura del primissimo giorno
        if (now < absoluteStart) {
            return { status: "Asta programmata. Le offerte aprono tra:", target: absoluteStart, locked: true, closed: false };
        }

        // L'asta è in corso nei suoi giorni validi. Verifichiamo la finestra di OGGI.
        const todayStart = new Date(now);
        todayStart.setHours(windowStart.hour, windowStart.minute, 0, 0);

        const todayEnd = new Date(now);
        todayEnd.setHours(windowEnd.hour, windowEnd.minute, 0, 0);

        if (now < todayStart) {
            return { status: "Le offerte di oggi aprono tra:", target: todayStart, locked: true, closed: false };
        }

        if (now >= todayStart && now < todayEnd) {
            return { status: "Tempo rimanente per fare offerte oggi:", target: todayEnd, locked: false, closed: false };
        }

        // Se l'orario è oltre la chiusura di oggi, le offerte sono Locked e riaprono domani
        const tomorrowStart = new Date(now);
        tomorrowStart.setDate(tomorrowStart.getDate() + 1);
        tomorrowStart.setHours(windowStart.hour, windowStart.minute, 0, 0);

        return { status: "Finestra di oggi chiusa. Le offerte riaprono tra:", target: tomorrowStart, locked: true, closed: false };
    };

    const updateBlockchainStatus = async (endpoint) => {
        try {
            const token = localStorage.getItem('Authorization') || sessionStorage.getItem('Authorization');
            console.debug(`Chiamata Blockchain: ${endpoint}`);
            const response = await fetch(endpoint, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    ...(token && { "Authorization": token })
                }
            });
            const res_data = await response.json();
            if (response.ok && res_data.status === "success") {
                console.debug("Stato blockchain aggiornato con successo.");
                setTimeout(() => location.reload(), 1500); // Ricarica per far vedere i cambiamenti
            }
        } catch (error) {
            console.error("Errore di rete durante l'aggiornamento blockchain:", error);
        }
    };

    const updateCountdown = async (windowStart, windowEnd) => {
        const { status, target, locked, closed } = computeWindowTarget(windowStart, windowEnd);
        const diff = target.getTime() - Date.now();

        statusEl.textContent = status;
        
        if (submitButton) {
            submitButton.disabled = locked;
            submitButton.style.opacity = locked ? "0.5" : "1";
            submitButton.style.cursor = locked ? "not-allowed" : "pointer";
        }

        countdownEl.textContent = (diff <= 0 && closed) ? "00:00:00" : formatDuration(diff);

        // Logica a transizione di stato: invia alla blockchain solo quando c'è un cambiamento reale
        let currentState = closed ? 'closed' : (locked ? 'locked' : 'active');
        console.debug(`Stato asta: ${currentState}`);
        // Se è diventata LOCKED oggi, avvisa il backend
        if (previousState === 'active' && currentState === 'locked') {
            previousState = currentState; 
            await updateBlockchainStatus(`/api/v1/auctions/lock/${auctionId}`);
        } 
        // Se ha superato la finestra dell'ultimo giorno, chiudila
        else if (previousState !== 'closed' && currentState === 'closed') {
            previousState = currentState;
            console.debug("Asta chiusa, aggiorno blockchain...");
            await updateBlockchainStatus(`/api/v1/auctions/close/${auctionId}`);
        }
        // cambio da locked a active (riapertura finestra giornaliera)
        else if (previousState === 'locked' && currentState === 'active') {
            previousState = currentState;
            console.debug("Riapertura finestra offerte, aggiorno blockchain...");
            await updateBlockchainStatus(`/api/v1/auctions/active/${auctionId}`);
        }
    };

    const initTimer = async () => {
        let windowStart = { hour: 13, minute: 0 };
        let windowEnd = { hour: 13, minute: 45};

        try {
            const response = await fetch("/api/v1/bids/allowed_timeframe", {
                method: "GET",
                headers: { "Content-Type": "application/json" }
            });
            const payload = await response.json();

            if (response.ok && payload?.status === "success") {
                windowStart = parseHourMinute(payload.data.allowed_time_start, 13);
                windowEnd = parseHourMinute(payload.data.allowed_time_end, 13);

                const hintEl = timerCard.querySelector(".create-auction-timer-hint");
                if (hintEl) {
                    hintEl.textContent = `Finestra valida per offerte: ${String(windowStart.hour).padStart(2, "0")}:${String(windowStart.minute).padStart(2, "0")} - ${String(windowEnd.hour).padStart(2, "0")}:${String(windowEnd.minute).padStart(2, "0")}.`;
                }
            }
        } catch (error) {
            console.error("Errore nel recupero della finestra offerte:", error);
        }

        updateCountdown(windowStart, windowEnd);
        setInterval(() => updateCountdown(windowStart, windowEnd), 1000);
    };

    initTimer();
});