document.addEventListener("alpine:init", () => {
	Alpine.data("assetsForm", () => ({
        id: '',
        assetId: '',
        sellerId: '',
        startTime: '',
        endtime: '',
        startPrice: '',
        minIncrement: '',
        message: '',
        
        async create_assets(){
            console.log("Create Auction")
        },

        async get_auctions(){
            console.log("Get Auctions")
        },
        
        async get_auction_by_id(){
            console.log("Get Auction by Id")
        },
        
    }));
});
