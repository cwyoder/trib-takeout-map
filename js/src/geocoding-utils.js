function triggerWarning(trigger, message){
	if (trigger == 'trigger'){
		document.querySelector('.profile-lookup__error-message').innerHTML = message;
		document.querySelector('.profile-lookup').classList.add('profile-lookup--error');
	} else if (trigger == 'clear') {
		document.querySelector('.profile-lookup').classList.remove('profile-lookup--error');
	}
}

function spinner(iconToShow){
	// Just switches between the submit arrow and the loading spinner on the form, so people know it's working.

	const icons = document.querySelectorAll(".submit-icon");
	
	for (let i=0; i < icons.length; i++){
		const icon = icons[i];
		if (icon.classList.contains(`submit-icon--${iconToShow}`)){
			icon.classList.add('submit-icon--visible')
		} else {
			icon.classList.remove('submit-icon--visible')
		}
	}
}


module.exports = {
	triggerWarning: triggerWarning,
	spinner: spinner
};