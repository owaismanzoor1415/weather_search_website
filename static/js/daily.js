/* ===== ELEMENTS ===== */

const slider = document.getElementById("slider");
const backBtn = document.getElementById("backBtn");

/* ===== RAIN LAYER ===== */

const rainLayer = document.createElement("div");
rainLayer.className = "rain";
document.body.appendChild(rainLayer);

/* ===== WEATHER BACKGROUNDS ===== */

const backgrounds = {

clear: "https://images.unsplash.com/photo-1502082553048-f009c37129b9",

clouds: "https://images.unsplash.com/photo-1506744038136-46273834b3fb",

rain: "https://images.unsplash.com/photo-1501696461441-9c8b4e9b20bb",

snow: "https://images.unsplash.com/photo-1483664852095-d6cc6870702d"

};

/* ===== SET BACKGROUND ===== */

function setWeatherBackground(desc){

if(!desc) return;

desc = desc.toLowerCase();

let img = backgrounds.clouds;

if(desc.includes("clear")) img = backgrounds.clear;
if(desc.includes("rain")) img = backgrounds.rain;
if(desc.includes("snow")) img = backgrounds.snow;

document.body.style.backgroundImage = `url(${img})`;
document.body.style.backgroundSize = "cover";
document.body.style.backgroundPosition = "center";
document.body.style.backgroundAttachment = "fixed";

}

/* ===== WEATHER EFFECTS ===== */

function weatherEffects(desc){

if(!desc) return;

desc = desc.toLowerCase();

if(desc.includes("rain")){

rainLayer.style.display = "block";

}else{

rainLayer.style.display = "none";

}

}

/* ===== INITIAL WEATHER ===== */

const firstDescElement = document.querySelector(".desc");

if(firstDescElement){

const firstDesc = firstDescElement.textContent;

setWeatherBackground(firstDesc);
weatherEffects(firstDesc);

}

/* ===== PARALLAX + BACK BUTTON ===== */

if(slider){

slider.addEventListener("scroll", () => {

const scrollTop = slider.scrollTop;

/* PARALLAX BACKGROUND */

document.body.style.backgroundPositionY = scrollTop * 0.2 + "px";

/* SHOW BACK BUTTON AT END */

const maxScroll = slider.scrollHeight - slider.clientHeight;

if(backBtn){

if(scrollTop >= maxScroll - 50){

backBtn.classList.add("show");

}else{

backBtn.classList.remove("show");

}

}

});

}