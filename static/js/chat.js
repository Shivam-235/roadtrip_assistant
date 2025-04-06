// Helper function to append a message to the chat
function appendMessage(sender, message, map_embed) {
    const chatbox = document.getElementById("chatbox");
    const messageElement = document.createElement("div");
    messageElement.classList.add("message", sender);
    messageElement.textContent = message;

    // Add speak button only for bot responses
    if (sender === "roadie") {
        const speakButton = document.createElement("button");
        speakButton.textContent = "🔊 Speak";
        speakButton.classList.add("speak-btn");
        speakButton.onclick = () => speakText(message);
        messageElement.appendChild(document.createElement("br"));
        messageElement.appendChild(speakButton);
    }

    chatbox.appendChild(messageElement);

    if (map_embed) {
        const mapElement = document.createElement("iframe");
        mapElement.src = map_embed;
        chatbox.appendChild(mapElement);
    }

    chatbox.scrollTop = chatbox.scrollHeight;
}

// Speak only when speak button is clicked
function speakText(text) {
    const utterance = new SpeechSynthesisUtterance(text);
    window.speechSynthesis.speak(utterance);
}

function showSuggestions(suggestions) {
    const chatbox = document.getElementById("chatbox");
    const suggestionBox = document.createElement("div");
    suggestionBox.classList.add("message", "roadie");

    suggestionBox.innerHTML = `<strong>Suggestions:</strong><br>` + suggestions.map(s => `<div class="suggestion-item" onclick="handleSuggestion('${s}')">${s}</div>`).join("");

    chatbox.appendChild(suggestionBox);
    chatbox.scrollTop = chatbox.scrollHeight;
}

function handleSuggestion(text) {
    document.getElementById("messageInput").value = text;
    sendMessage();
}

// Function to handle sending a message
async function sendMessage() {
    const input = document.getElementById("messageInput");
    const message = input.value.trim();
    if (!message) return;

    appendMessage("user", message);
    input.value = "";

    const res = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message })
    });

    const data = await res.json();
    console.log("Server Response:", data);

    appendMessage("roadie", data.text, data.map_embed);
    if (data.suggestions) {
        showSuggestions(data.suggestions);
    }
}

// Function to start voice recognition
function startListening() {
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.onresult = (event) => {
        const message = event.results[0][0].transcript;
        document.getElementById("messageInput").value = message;
        sendMessage();
    };
    recognition.start();
}

async function planTrip() {
    const start = document.getElementById("start").value;
    const end = document.getElementById("end").value;
    const fuelBudget = document.getElementById("fuelBudget").value;
    const lodgingBudget = document.getElementById("lodgingBudget").value;
    const foodBudget = document.getElementById("foodBudget").value;
    const mpg = document.getElementById("mpg").value;
    const fuelPrice = document.getElementById("fuelPrice").value;
    const departureTime = document.getElementById("departureTime").value;
    const preferences = document.getElementById("preferences").value;

    const summary = `Plan a road trip from ${start} to ${end}. Departure: ${departureTime}. Fuel budget: ${fuelBudget}, Lodging: ${lodgingBudget}, Food: ${foodBudget}, MPG: ${mpg}, Fuel price: ${fuelPrice}. Preferences: ${preferences}.`;

    appendMessage("user", summary);

    const res = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: summary })
    });

    const data = await res.json();
    appendMessage("roadie", data.text, data.map_embed);
    if (data.suggestions) {
        showSuggestions(data.suggestions);
    }
}
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/static/service-worker.js');
    });
  }
  