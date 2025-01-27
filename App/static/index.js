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



    function fetchDistance() {
      fetch('/distance')
          .then(response => {
              if (!response.ok) {
                  throw new Error('Network response was not ok');
              }
              return response.json();  // Parse the JSON response
          })
          .then(data => {
              if (data.distance) {
                  // Update your UI with the formatted distance
                  document.getElementById('distance').textContent = data.distance + '';
                  document.getElementById('status').textContent = data.status;
                  document.getElementById('status').className = data.status;  // Update the status class
              } else {
                  console.error('Invalid data format:', data);
              }
          })
          .catch(error => {
              console.error('Error fetching distance:', error);
          });
  }
  
  // Fetch distance data periodically
  setInterval(fetchDistance, 5000 );  // Update every 5 second
  
  // Initial fetch to populate data on page load
  fetchDistance();

  
})(jQuery);
