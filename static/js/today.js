const weather = (document.body.dataset.weather || "").toLowerCase()

const backgrounds = {

clear: "https://images.pexels.com/photos/912110/pexels-photo-912110.jpeg",

clouds: "https://images.pexels.com/photos/531767/pexels-photo-531767.jpeg",

rain: "https://images.unsplash.com/photo-1519692933481-e162a57d6721?auto=format&fit=crop&w=2000&q=80.jpeg",

snow: "https://images.pexels.com/photos/688660/pexels-photo-688660.jpeg",

mist: "https://images.pexels.com/photos/167699/pexels-photo-167699.jpeg"

}

let bg = backgrounds.clouds

if(weather.includes("clear")) bg = backgrounds.clear
else if(weather.includes("cloud")) bg = backgrounds.clouds
else if(weather.includes("rain") || weather.includes("drizzle") || weather.includes("thunderstorm")) bg = backgrounds.rain
else if(weather.includes("snow")) bg = backgrounds.snow
else if(weather.includes("mist") || weather.includes("fog") || weather.includes("haze")) bg = backgrounds.mist

document.body.style.backgroundImage = `url(${bg})`
document.body.style.backgroundSize = "cover"
document.body.style.backgroundPosition = "center"