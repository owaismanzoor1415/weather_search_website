const weather = document.body.dataset.weather.toLowerCase()

const backgrounds = {

clear:"https://images.unsplash.com/photo-1500530855697-b586d89ba3ee",

clouds:"https://images.unsplash.com/photo-1506744038136-46273834b3fb",

rain:"https://images.unsplash.com/photo-1501696461441-9c8b4e9b20bb",

snow:"https://images.unsplash.com/photo-1483664852095-d6cc6870702d"

}

let bg = backgrounds.clouds

if(weather.includes("clear")) bg = backgrounds.clear
if(weather.includes("cloud")) bg = backgrounds.clouds
if(weather.includes("rain")) bg = backgrounds.rain
if(weather.includes("snow")) bg = backgrounds.snow

document.body.style.backgroundImage = `url(${bg})`