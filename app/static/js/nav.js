document.addEventListener('alpine:init', () => {
    Alpine.data('navHandler', () => ({
        isLoggedIn: false,

        init() {
            // Controlliamo se esiste il token in uno dei due storage
            const token = localStorage.getItem('Authorization') || sessionStorage.getItem('Authorization');
            this.isLoggedIn = !!token; // Trasforma il valore in booleano (true se esiste)
        },

        logout() {
            localStorage.removeItem('Authorization');
            sessionStorage.removeItem('Authorization');
            window.location.href = '/login';
        }
    }))
})