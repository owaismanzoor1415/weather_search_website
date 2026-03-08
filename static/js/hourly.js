document.addEventListener("DOMContentLoaded", () => {

/* ===== AUTO SCROLL TO CURRENT HOUR ===== */

const current = document.querySelector(".hour-box.now");

if(current){

current.scrollIntoView({
behavior:"smooth",
inline:"center",
block:"nearest"
});

}

/* ===== DYNAMIC WEATHER BACKGROUND ===== */

const weather = document.body.dataset.weather?.toLowerCase() || "";

let bg = "https://images.pexels.com/photos/1563356/pexels-photo-1563356.jpeg";

if(weather.includes("rain")){
bg = "https://images.unsplash.com/photo-1519692933481-e162a57d6721";
}
else if(weather.includes("cloud")){
bg = "https://images.unsplash.com/photo-1499346030926-9a72daac6c63";
}
else if(weather.includes("clear")){
bg = "https://images.unsplash.com/photo-1472214103451-9374bd1c798e";
}

document.body.style.backgroundImage = `url(${bg})`;

});