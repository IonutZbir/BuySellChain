async function sendGetRequest() {
    try {
        const response = await fetch("/api/v1/auth/test", {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': localStorage.getItem('Authorization') || sessionStorage.getItem('Authorization')
            }
        });

        if (!response.ok) {
            console.log(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log(data);
        console.log(localStorage.getItem('Authorization'))
        return data;
    } catch (error) {
        console.error('There was a problem with the fetch operation:', error);
        throw error;
    }
}