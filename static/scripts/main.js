function makeReadOnly() {
	/*var myText = document.getElementById("myEditor");
	console.log(myText);
	if (myText.hasAttribute("readonly")) {
		console.log('already there');
	}
	else {
		myText.setAttribute("readonly", "true");
	}*/
	document.getElementById("myEditor").readOnly = true;
}

function showDiv() {
    document.getElementById('welcome').style.display = "block";
}


/*function refresh() {
	var e=document.getElementById("refreshed");
	if(e.value=="no");e.value="yes";
	else{e.value="no";location.reload();}
	console.log(e.value);
}*/

/*onload=function(){
var e=document.getElementById("refreshed");
if(e.value=="no")e.value="yes";
else{e.value="no";location.reload();}
*/
//personalized welcome page

/*
var myButton = document.querySelector('button');
var myHeading = document.querySelector('body');

function setUserName() {
	var myName = prompt("Enter your name asshole: ");
	localStorage.setItem('name', myName);
	myHeading.textContent = 'Hannah Reid loves you ' + myName;
}

if (!localStorage.getItem('name')) {
	setUserName();
}
else {
	var storedName = localStorage.getItem('name');
	myHeading.textContent = 'Hannah Reid loves you ' + storedName;
}

myButton.onclick = function() {
	setUserName();
}
*/	
