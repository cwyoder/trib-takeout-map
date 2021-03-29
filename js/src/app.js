import * as L from 'leaflet';
require('leaflet-providers');
import getCoord from './get-coord.js';
import * as utils from './geocoding-utils.js';

let userCoordinates = {};

//adding data attributes to divIcons
L.DataDivIcon = L.DivIcon.extend({
	createIcon: function(oldIcon) {
	  var div = L.DivIcon.prototype.createIcon.call(this, oldIcon);
	  if(this.options.data) {
	    for(var key in this.options.data) {
	      div.dataset[key] = this.options.data[key];
	    }
	  }
	  return div;
	}
});

L.dataDivIcon = function(options) {
	return new L.DataDivIcon(options);
}


//draw the map
function drawMap(mapContainer, data) {
	const map = L.map(mapContainer, {
		center: [41.87, -87.9],
		zoom: 10,
		minZoom: 3,
		maxZoom: 16,
		maxBounds: [[40.5,-89.5],[43,-86.5]],
		scrollWheelZoom: false
	});

	L.tileLayer.provider('CartoDB.Positron').addTo(map);

    const userIcon = new L.DivIcon({
        className: 'map__location-icon-user',
        iconSize: [6, 6]
    });

	data.forEach(location => {
		let customPopup = buildPopup(location);

		new L.Marker([parseFloat(location.lat), parseFloat(location.lng)], {
			icon: L.dataDivIcon({
				className: `map__location-icon`,
				html: `<span></span>`,
				iconSize: 10,
				data: {
					type: createValue(location.type),
					price: location.price.length
				}
			})
		}).addTo(map).bindPopup(customPopup);
	});

	// The submit button which should geocode and trigger a profile
    document.getElementById('search-address-submit').addEventListener('click', e => {
         
        // Quash the default behavior
        e.preventDefault();
  
        // // Get the input address from the form
        const address = document.getElementById('search-address').value;
        
        // show loading spinner
        utils.spinner('spinner');

        getCoord(address)
            .then(function(response) {
                // after address is pinged:

                const data = JSON.parse(response).resourceSets[0];
                if (data.estimatedTotal > 0) {
                    // if the geocoding returns at least one entry, then
                    // do this. This ain't no guarantee that the address 
                    // is the correct one, but at least we know it's a real address.
                     
                    // Start by clearing any existing error
                    utils.triggerWarning("clear")
  
                    userCoordinates =  {
                        address: data.resources[0].name,
                        coordinates:[
                            data.resources[0].geocodePoints[0].coordinates[1],
                            data.resources[0].geocodePoints[0].coordinates[0]
                        ]
                    }
                } else {
                    // If the geocoding returned no entries
                    // utils.triggerWarning("trigger", window.error_not_found)
                }
               
            }, function(error) {
                // error for the promise
                const userCoordinates = error;
            }).then(function(after){
                // finds the district
                L.marker([userCoordinates.coordinates[1],userCoordinates.coordinates[0]],{icon:userIcon}).addTo(map);
                map.flyTo([userCoordinates.coordinates[1],userCoordinates.coordinates[0]],12);
                console.log(userCoordinates.coordinates)
            }).then(function(after){
                utils.spinner('arrow');
            }).catch( function(error){
                // I really don't know what this does :(
                console.log('error', error, error.stack);
        });
    });
}

function buildPopup(location){
	let popUpText = `<div class="popup">
						<h4><span>${location.name}</h4>
						<ul>
							<li>${location.type} | ${location.cuisine}</li>
							<li>Price: ${location.price}</li>
							<li class='list-ital'>${location.address}, ${location.city}</li>
							<li><a href="javascript: document.getElementById('${location.id}').scrollIntoView({behavior:'smooth'});">More info</a></li>
						</ul>
					</div>`;
	return popUpText;
}

//create the options for the cuisine type dropdown menu
function populateDropdown(data){
	const dropdown = document.querySelector('#cuisineTypeSelect');

	const cuisineCategories = [... new Set(data.map(loc => loc.type))].sort();

	for (let i = 0; i < cuisineCategories.length; i++) {
		const newOption = document.createElement('option');
		const cuisineString = cuisineCategories[i];
		const cuisineValue = createValue(cuisineString);

		newOption.text = cuisineString;
		newOption.value = cuisineValue;

		dropdown.appendChild(newOption);
	}
}

//fixes the data attributes on the list items
function formatListData(){
	const listItems = document.querySelectorAll('.restaurant-container');

	for (const listItem of listItems){
		const currentType = listItem.dataset.type;
		listItem.dataset.type = createValue(currentType);
	}
}

//document load
document.addEventListener('DOMContentLoaded', function(e){
	const mapContainer = document.querySelector('#takeout-map');
	const takeoutData = window.takeout;

	Promise.all([takeoutData]).then(function(values) {
		drawMap(mapContainer, values[0]);
		populateDropdown(values[0]);
		formatListData();
	});
})

//create the cuisine value for dropdown/data attributes
function createValue(string){
	return string.toLowerCase().split('').filter(char => char !== ' ' && char !== '/').join('');
}

//creating a state for multiple filters
const filterState = {
	type: 'all',
	price: 'all',
}

//changing filters
document.querySelector('#cuisineTypeSelect').addEventListener('change', e => {
	filterState.type = e.target.value;
	renderShowHide();
})

document.querySelector('#priceSelect').addEventListener('change', e => {
	filterState.price = e.target.value;
	renderShowHide();
})

//changing show/hide of map markers and list items
function renderShowHide(){
	const mapIcons = document.querySelectorAll('.map__location-icon');
	let count = 0;
	for (const icon of mapIcons) {
		if ((filterState.type === 'all' || filterState.type === icon.dataset.type) &&
			(filterState.price === 'all' || filterState.price === icon.dataset.price)) {
			icon.style.display = 'block';
		} else {
			icon.style.display = 'none';
		}
	}

	const list = document.querySelectorAll('.restaurant-container');
	for (const item of list) {
		if ((filterState.type === 'all' || filterState.type === item.dataset.type) &&
			(filterState.price === 'all' || filterState.price === item.dataset.price)) {
			item.style.display = 'block';
			count++;
		} else {
			item.style.display = 'none';
		}
	}

	//update result number
	if (count === 100) {
		document.querySelector('#count-p').style.display = 'none';
	} else if (count === 1) {
		document.querySelector('#count-p').style.display = 'inline-block';
		document.querySelector('#count-p').innerText = `Displaying 1 result`;
	} else {
		document.querySelector('#count-p').style.display = 'inline-block';
		document.querySelector('#count-p').innerText = `Displaying ${count} results`;
	}

	//closing popup
	const closeButton = document.querySelector('.leaflet-popup-close-button');
	if (closeButton) closeButton.click();

	//resize iframe
	pymChild.sendHeight();
}



