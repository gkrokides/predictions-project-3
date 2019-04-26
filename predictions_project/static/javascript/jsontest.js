var btn = document.getElementById("btnjson")
var container = document.getElementById("ourcontainer")
var url = 'http://127.0.0.1:8000/smseasonjson'

btn.addEventListener("click", function(){
	var ourRequest = new XMLHttpRequest();
	ourRequest.open("GET", url);
	ourRequest.onload = function(){
		console.log(ourRequest.responseText); // this is not Json formatted
		var ourData = JSON.parse(ourRequest.responseText);
		console.log(ourData);
	}
	ourRequest.send();
})