import {json} from 'd3';

function getCoord(address){
	// Generates a promise used to download a small json object with the user's coordiates based on the input address
	return new Promise(function(resolve, reject){
		// Make the request

		const requestUrl = `https://qyf1ag22mj.execute-api.us-east-1.amazonaws.com/production/locations?q=${encodeURI(address)}&userLocation=41.8337329,-87.7321555`
		const geoRequest = json(requestUrl)
		var request = new XMLHttpRequest();
		request.open('GET', requestUrl);

		request.onload = function(){
			if (request.status == 200){
				// success
				resolve(request.response);
			} else {
				// Failure
				reject(Error('ERROR!'));
				reject(TypeError('TYPE ERROR!'));
			}
		}
	    // Handle network errors
	    request.onerror = function() {
	      reject(Error("Network Error"));
	    };

	    // Make the request
	    request.send();
	});
}

module.exports = getCoord;