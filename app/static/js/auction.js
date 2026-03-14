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

document.addEventListener("DOMContentLoaded", () => {
    const timerCard = document.querySelector(".create-auction-timer-card");
    const countdownEl = document.getElementById("bidWindowCountdown");
    const statusEl = document.getElementById("bidWindowStatus");

    if (!timerCard || !countdownEl || !statusEl) {
        return;
    }

    const parseHourMinute = (timeValue, fallbackHour) => {
        if (typeof timeValue !== "string") {
            return { hour: fallbackHour, minute: 0 };
        }

        const [hourRaw, minuteRaw] = timeValue.split(":");
        const hour = Number.parseInt(hourRaw, 10);
        const minute = Number.parseInt(minuteRaw, 10);

        if (
            Number.isInteger(hour) &&
            Number.isInteger(minute) &&
            hour >= 0 &&
            hour <= 23 &&
            minute >= 0 &&
            minute <= 59
        ) {
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

        if (days > 0) {
            return `${days}g ${hh}:${mm}:${ss}`;
        }
        return `${hh}:${mm}:${ss}`;
    };

    const computeWindowTarget = (windowStart, windowEnd) => {
        const now = new Date();

        const startToday = new Date(now);
        startToday.setHours(windowStart.hour, windowStart.minute, 0, 0);

        const endToday = new Date(now);
        endToday.setHours(windowEnd.hour, windowEnd.minute, 0, 0);

        if (endToday <= startToday) {
            return {
                status: "Finestra offerte non valida.",
                target: now
            };
        }

        if (now < startToday) {
            return {
                status: "Le offerte aprono tra:",
                target: startToday
            };
        }

        if (now < endToday) {
            return {
                status: "Tempo rimanente per fare offerte oggi:",
                target: endToday
            };
        }

        const startTomorrow = new Date(startToday);
        startTomorrow.setDate(startTomorrow.getDate() + 1);

        return {
            status: "Finestra di oggi chiusa. Le offerte riaprono tra:",
            target: startTomorrow
        };
    };

    const updateCountdown = (windowStart, windowEnd) => {
        const { status, target } = computeWindowTarget(windowStart, windowEnd);
        const diff = target.getTime() - Date.now();

        statusEl.textContent = status;
        countdownEl.textContent = formatDuration(diff);
    };

    const initTimer = async () => {
        let windowStart = { hour: 8, minute: 0 };
        let windowEnd = { hour: 22, minute: 0 };

        try {
            const response = await fetch("/api/v1/bids/allowed_timeframe", {
                method: "GET",
                headers: {
                    "Content-Type": "application/json"
                }
            });

            const payload = await response.json();

            if (response.ok && payload?.status === "success") {
                const apiStart = payload?.data?.allowed_time_start;
                const apiEnd = payload?.data?.allowed_time_end;

                windowStart = parseHourMinute(apiStart, 8);
                windowEnd = parseHourMinute(apiEnd, 22);

                const hintEl = timerCard.querySelector(".create-auction-timer-hint");
                if (hintEl) {
                    hintEl.textContent = `Finestra valida offerte: ${String(windowStart.hour).padStart(2, "0")}:${String(windowStart.minute).padStart(2, "0")} - ${String(windowEnd.hour).padStart(2, "0")}:${String(windowEnd.minute).padStart(2, "0")}.`;
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