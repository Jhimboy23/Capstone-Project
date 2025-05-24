(function ($) {
    "use strict";

    // Spinner
    var spinner = function () {
        setTimeout(function () {
            if ($('#spinner').length > 0) {
                $('#spinner').removeClass('show');
            }
        }, 1);
    };

    // Call the spinner function    
    spinner();

    // Fetch and display distance data
    function fetchDistance() {
        fetch('/distance')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.distance) {
                    // Convert distance to float with two decimal places
                    const distanceFloat = (parseFloat(data.distance) / 100).toFixed(2);

                    // Update your UI with the formatted distance
                    document.getElementById('distance').textContent = distanceFloat + ' m';
                    document.getElementById('status').textContent = data.status;
                    document.getElementById('status').className = data.status;
                } else {
                    console.error('Invalid data format:', data);
                }
            })
            .catch(error => {
                console.error('Error fetching distance:', error);
            });
    }

    // Fetch distance data periodically
    setInterval(fetchDistance, 25000);  // Update every 25 seconds

    // Initial fetch on page load
    fetchDistance();

})(jQuery);
