/* ---------------- MAP ---------------- */

const map = L.map('owmMap', { preferCanvas: true }).setView([20, 0], 3);

let markersGroup = L.layerGroup().addTo(map);

L.tileLayer(
'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
{ maxZoom: 19 }
).addTo(map);


/* ---------------- SEARCH ---------------- */

async function refreshAndOpen(city, view){

city = (city || "").trim();

if(!city){
alert("Enter a city first");
return;
}

try{

const resp = await fetch("/api/weather", {
method:"POST",
headers:{"Content-Type":"application/json"},
body: JSON.stringify({city})
});

if(!resp.ok){
alert("Server error");
return;
}

const url = view
? `/weather/${encodeURIComponent(city)}/${view}`
: `/weather/${encodeURIComponent(city)}`;

window.location.href = url;

}catch(e){
console.error(e);
alert("Network error");
}

}


/* Search button */

const searchBtn = document.getElementById("searchBtn");

if(searchBtn){
searchBtn.addEventListener("click", () => {

const city =
document.getElementById("cityInput").value;

refreshAndOpen(city,"");

});
}


/* Enter key search */

const mapSearchInput = document.getElementById("mapSearchInput");

if(mapSearchInput){
mapSearchInput.addEventListener("keydown",(e)=>{
if(e.key === "Enter"){
document.getElementById("mapSearchBtn").click();
}
});
}


/* ---------------- HISTORY ---------------- */

async function loadHistory(){

try{

const r = await fetch("/api/history");
const arr = await r.json();

if(!arr || !arr.length){

document.getElementById("historyList").innerHTML =
"No recent searches";

return;

}

document.getElementById("historyList").innerHTML =
arr.map(item => `
<div class="card recent-card" data-city="${item.city}">
<div class="city">${item.city}</div>

<div class="mid-row">
<div class="weather-icon">${item.icon || "☀️"}</div>
<div class="temp">${Math.round(item.temperature)}°C</div>
</div>

</div>
`).join("");

}catch(e){

console.error("History load failed", e);

document.getElementById("historyList").innerHTML =
"Error loading history";

}

}

loadHistory();


/* Click history */

document.addEventListener("click",(e)=>{

const el = e.target.closest(".recent-card");

if(!el) return;

const city = el.dataset.city;

refreshAndOpen(city,"");

});


/* ---------------- HEADER BUTTONS ---------------- */

function headerAction(view){

const city =
document.getElementById("cityInput").value;

refreshAndOpen(city,view);

}

const todayBtn = document.getElementById("btn-today");
const hourlyBtn = document.getElementById("btn-hourly");
const dailyBtn = document.getElementById("btn-daily");

if(todayBtn){
todayBtn.addEventListener("click",(e)=>{
e.preventDefault();
headerAction("today");
});
}

if(hourlyBtn){
hourlyBtn.addEventListener("click",(e)=>{
e.preventDefault();
headerAction("hourly");
});
}

if(dailyBtn){
dailyBtn.addEventListener("click",(e)=>{
e.preventDefault();
headerAction("daily");
});
}


/* ---------------- MAP SEARCH ---------------- */

const mapSearchBtn = document.getElementById("mapSearchBtn");

if(mapSearchBtn){

mapSearchBtn.addEventListener("click", async () => {

const city =
document.getElementById("mapSearchInput").value;

if(!city){
alert("Enter city name");
return;
}

try{

const res = await fetch(
`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(city)}`
);

const data = await res.json();

if(!data.length){
alert("City not found");
return;
}

const lat = data[0].lat;
const lon = data[0].lon;

map.setView([lat,lon],10);

markersGroup.clearLayers();

const marker = L.marker([lat,lon])
.addTo(markersGroup)
.bindPopup(`<b>${city}</b><br>Click to view weather`)
.openPopup();

/* open weather only when marker clicked */
marker.on("click", () => {
refreshAndOpen(city,"");
});

}catch(e){
console.error(e);
alert("Search failed");
}

});

}


/* ---------------- LOCATE ME ---------------- */

const locateBtn = document.getElementById("locateMeBtn");

if(locateBtn){

locateBtn.addEventListener("click", () => {

if(!navigator.geolocation){
alert("Geolocation not supported");
return;
}

navigator.geolocation.getCurrentPosition((pos)=>{

const lat = pos.coords.latitude;
const lon = pos.coords.longitude;

map.setView([lat,lon],10);

markersGroup.clearLayers();

L.marker([lat,lon])
.addTo(markersGroup)
.bindPopup("You are here")
.openPopup();

});

});

}


/* ---------------- SIDEBAR MENU ---------------- */

function toggleMenu(){

const sidebar = document.getElementById("sidebar");
const overlay = document.getElementById("overlay");

sidebar.classList.toggle("active");
overlay.classList.toggle("active");

}


/* ---------------- INSTALL APP ---------------- */

let deferredPrompt;

window.addEventListener("beforeinstallprompt",(e)=>{

e.preventDefault();

deferredPrompt = e;

const installBtn = document.getElementById("installBtn");

if(installBtn){
installBtn.style.display="block";
}

});

const installBtn = document.getElementById("installBtn");

if(installBtn){

installBtn.addEventListener("click", async ()=>{

if(!deferredPrompt) return;

deferredPrompt.prompt();

const choice =
await deferredPrompt.userChoice;

if(choice.outcome === "accepted"){
console.log("App installed");
}

deferredPrompt=null;

});

}