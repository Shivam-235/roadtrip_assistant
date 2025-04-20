// Helper function to append a message to the chat
function appendMessage(sender, message, prioritizeMap = false) {
    const chatbox = document.getElementById("chatbox");
    if (!chatbox) {
        console.error("Chatbox element not found!");
        return;
    }
    
    const messageElement = document.createElement("div");
    messageElement.classList.add("message", sender);
    
    // Create message content with enhanced styling
    const messageText = document.createElement("div");
    messageText.classList.add("message-text");
    
    // Use formatted rendering for roadie messages with rich formatting
    if (sender === "roadie" && 
        (message.includes("•") || message.includes("🚗") || message.includes("🛣️"))) {
        messageText.innerHTML = renderFormattedMessage(message);
    } else {
        // Safety: use textContent for plain text, innerHTML for formatted HTML
        if (typeof message === 'string' && (message.includes("<") && message.includes(">"))) {
            messageText.innerHTML = message;
        } else {
            messageText.textContent = message;
        }
    }
    
    messageElement.appendChild(messageText);

    // Add speak button only for bot responses with enhanced styling
    if (sender === "roadie") {
        const speakButton = document.createElement("button");
        speakButton.innerHTML = "🔊";
        speakButton.title = "Speak this message";
        speakButton.classList.add("speak-btn");
        speakButton.onclick = () => speakText(message);
        messageElement.appendChild(speakButton);
    }

    // Apply staggered animation delay for smoother appearance
    const existingMessages = chatbox.querySelectorAll(".message").length;
    messageElement.style.animationDelay = `${existingMessages * 0.05}s`;
    
    // Ensure the message is properly appended and stays visible
    chatbox.appendChild(messageElement);
    
    // Force a DOM reflow
    void messageElement.offsetWidth;
    
    // Make sure the message is visible by setting styles explicitly
    messageElement.style.display = 'block';
    messageElement.style.opacity = '1';

    // Smooth scroll to bottom with animation
    smoothScrollToBottom(chatbox);
    
    // Debug: log message addition
    console.log(`Message added (${sender}):`, message.substring(0, 50) + (message.length > 50 ? '...' : ''));
    console.log("Current chat messages:", chatbox.querySelectorAll(".message").length);
}

// Enhanced rendering for messages with improved formatting
function renderFormattedMessage(text) {
    // Convert bullet points for better display
    text = text.replace(/•\s+(.*?)(\n|$)/g, '<div class="bullet-point">• $1</div>');
    
    // Add style to sections (identified by text followed by a colon)
    text = text.replace(/^([A-Za-z\s]+):\s*$/gm, '<div class="section-header">$1:</div>');
    
    // Highlight distance/duration
    text = text.replace(/(Distance|Duration|Travel time|Driving time):\s+([^<\n]+)/g, 
        '<div class="info-item"><span class="info-label">$1:</span> <span class="info-value">$2</span></div>');
    
    // Create paragraphs from line breaks
    const paragraphs = text.split('\n\n').filter(p => p.trim() !== '');
    
    return paragraphs.map(p => `<div class="message-paragraph">${p}</div>`).join('');
}

// Smooth scroll function
function smoothScrollToBottom(element) {
    const targetPosition = element.scrollHeight;
    const startPosition = element.scrollTop;
    const distance = targetPosition - startPosition;
    const duration = 300;
    let startTime = null;

    function animation(currentTime) {
        if (startTime === null) startTime = currentTime;
        const timeElapsed = currentTime - startTime;
        const scrollY = easeOutCubic(timeElapsed, startPosition, distance, duration);
        element.scrollTop = scrollY;
        if (timeElapsed < duration) {
            requestAnimationFrame(animation);
        }
    }

    // Easing function for smooth scroll
    function easeOutCubic(t, b, c, d) {
        t /= d;
        t--;
        return c * (t * t * t + 1) + b;
    }

    requestAnimationFrame(animation);
}

// Speak the given text using selected voice
function speakText(text) {
    const utterance = new SpeechSynthesisUtterance(text);
    const voices = speechSynthesis.getVoices();
    const voiceSelect = document.getElementById('voiceSelect');

    // Show audio indicator
    showAudioIndicator();

    let selectedIndex = "";
    if (voiceSelect) {
        selectedIndex = voiceSelect.value;
    }

    if (voices.length && selectedIndex !== "") {
        utterance.voice = voices[selectedIndex];
    } else {
        const fallback = voices.find(voice =>
            voice.name.toLowerCase().includes("female") ||
            voice.name.toLowerCase().includes("woman") ||
            voice.gender === "female" ||
            voice.name.toLowerCase().includes("google us english")
        );
        if (fallback) utterance.voice = fallback;
    }

    utterance.pitch = 1.05;
    utterance.rate = 1.05;
    
    // Event handlers for audio indicator
    utterance.onend = removeAudioIndicator;
    utterance.onerror = removeAudioIndicator;
    
    speechSynthesis.speak(utterance);
}

// Show audio indicator
function showAudioIndicator() {
    const indicator = document.createElement("div");
    indicator.id = "audio-indicator";
    indicator.innerHTML = `
        <div style="position: fixed; bottom: 20px; right: 20px; background: var(--primary-gradient); 
        color: white; padding: 12px 20px; border-radius: 30px; display: flex; align-items: center; 
        gap: 10px; box-shadow: var(--shadow); z-index: 1000; animation: fadeIn 0.3s ease;">
            <div class="audio-wave">
                <span></span><span></span><span></span><span></span>
            </div>
            <span>Speaking...</span>
        </div>
    `;
    
    // Add wave animation styles
    const style = document.createElement("style");
    style.textContent = `
        .audio-wave {
            display: flex;
            align-items: center;
            gap: 3px;
            height: 20px;
        }
        .audio-wave span {
            display: block;
            width: 3px;
            height: 100%;
            background-color: white;
            border-radius: 3px;
            animation: audio-wave 1.5s infinite ease-in-out;
        }
        .audio-wave span:nth-child(2) { animation-delay: 0.2s; }
        .audio-wave span:nth-child(3) { animation-delay: 0.4s; }
        .audio-wave span:nth-child(4) { animation-delay: 0.6s; }
        
        @keyframes audio-wave {
            0%, 40%, 100% { transform: scaleY(0.4); }
            20% { transform: scaleY(1); }
        }
    `;
    
    document.body.appendChild(style);
    document.body.appendChild(indicator);
}

// Remove audio indicator
function removeAudioIndicator() {
    const indicator = document.getElementById("audio-indicator");
    if (indicator) {
        indicator.style.opacity = "0";
        indicator.style.transform = "translateY(20px)";
        indicator.style.transition = "all 0.3s ease";
        setTimeout(() => indicator.remove(), 300);
    }
}

// Remove map-related logic from suggestions
function showSuggestions(suggestions) {
    const chatbox = document.getElementById("chatbox");
    const suggestionBox = document.createElement("div");
    suggestionBox.classList.add("suggestion-container");

    const header = document.createElement("div");
    header.textContent = "You might want to ask:";
    header.style.fontSize = "14px";
    header.style.marginBottom = "10px";
    header.style.opacity = "0.8";
    header.style.fontWeight = "500";

    suggestionBox.appendChild(header);

    const buttonsContainer = document.createElement("div");
    buttonsContainer.style.display = "flex";
    buttonsContainer.style.flexWrap = "wrap";
    buttonsContainer.style.gap = "8px";

    // Add Indian city suggestions
    const indianCitySuggestions = [
        "Weather in Mumbai",
        "Best stops between Delhi and Jaipur",
        "Plan a trip from Bangalore to Mysore",
        "Travel time from Chennai to Pondicherry"
    ];
    suggestions = suggestions.concat(indianCitySuggestions);

    suggestions.forEach((s, index) => {
        const button = document.createElement("button");
        button.classList.add("suggestion-item");
        button.textContent = s;
        button.onclick = () => handleSuggestion(s);
        button.style.padding = "8px 14px";
        button.style.fontSize = "13px";
        button.style.opacity = "0";
        button.style.transform = "translateY(10px)";
        button.style.transition = "all 0.4s ease";
        button.style.transitionDelay = `${0.1 + index * 0.05}s`;

        buttonsContainer.appendChild(button);

        setTimeout(() => {
            button.style.opacity = "1";
            button.style.transform = "translateY(0)";
        }, 10);
    });

    suggestionBox.appendChild(buttonsContainer);
    suggestionBox.style.marginTop = "16px";
    suggestionBox.style.marginBottom = "16px";

    chatbox.appendChild(suggestionBox);
    smoothScrollToBottom(chatbox);
}

// Fill suggestion text into input and send
function handleSuggestion(text) {
    const input = document.getElementById("messageInput");
    input.value = text;
    
    // Add focus and typing effect
    input.focus();
    animateTyping(text, () => {
        sendMessage();
    });
}

// Animate typing effect
function animateTyping(fullText, callback, speed = 25) {
    const input = document.getElementById("messageInput");
    input.value = "";
    let i = 0;
    
    function typeChar() {
        if (i < fullText.length) {
            input.value += fullText.charAt(i);
            i++;
            setTimeout(typeChar, speed);
        } else if (callback) {
            setTimeout(callback, 200);
        }
    }
    
    typeChar();
}

// Play send sound with better error handling
const sendSound = new Audio("/static/sounds/send.mp3");
function playSendSound() {
    sendSound.volume = 0.5;
    sendSound.play().catch(e => {
        console.log("Sound playback error (non-critical):", e);
    });
}

// Enhanced typing indicator animation
function showTypingIndicator() {
    const chatbox = document.getElementById("chatbox");
    const typingDiv = document.createElement("div");
    typingDiv.className = "typing-indicator";
    typingDiv.id = "typing-indicator";
    
    for (let i = 0; i < 3; i++) {
        const dot = document.createElement("span");
        dot.className = "typing-dot";
        typingDiv.appendChild(dot);
    }
    
    chatbox.appendChild(typingDiv);
    smoothScrollToBottom(chatbox);
}

function hideTypingIndicator() {
    const typing = document.getElementById("typing-indicator");
    if (typing) {
        typing.style.opacity = "0";
        typing.style.transform = "translateY(10px)";
        typing.style.transition = "all 0.3s ease";
        
        setTimeout(() => typing.remove(), 300);
    }
}

// Toggle response format
function toggleResponseFormat() {
    useJsonFormat = !useJsonFormat;
    const toggleButton = document.getElementById("formatToggle");
    toggleButton.textContent = useJsonFormat ? "Switch to Default Format" : "Switch to JSON Format";
}

// Enhanced rendering for JSON responses
function renderJsonResponse(json) {
    const { summary, details, steps, recommendations } = json;

    return `
        <div class="json-response">
            <h3>${summary}</h3>
            <p>${details}</p>
            <h4>Steps:</h4>
            <ul>${steps.map(step => `<li>${step}</li>`).join("")}</ul>
            <h4>Recommendations:</h4>
            <ul>${recommendations.map(rec => `<li>${rec}</li>`).join("")}</ul>
        </div>
    `;
}

// Function to handle sending a message with enhanced enforcement for trip topics
async function sendMessage() {
    const input = document.getElementById("messageInput");
    const message = input.value.trim();
    if (!message) return;

    // Enhanced client-side filtering for non-travel topics
    const forbiddenPatterns = [
        /math/i, /problem/i, /calculation/i, /equation/i, /algebra/i, /geometry/i,
        /fibonacci/i, /algorithm/i, /code/i, /programming/i, 
        /exam/i, /homework/i, /assignment/i, /test/i, /quiz/i,
        /president/i, /politics/i, /religion/i, /recipe/i, /cook/i,
        /history\sof(?!\s+travel)/i, /science/i, /medicine/i, /disease/i,
        /stock market/i, /investing/i, /bitcoin/i, /crypto/i
    ];
    
    // Client-side check for obviously non-travel topics
    let isForbiddenTopic = false;
    for (const pattern of forbiddenPatterns) {
        if (pattern.test(message)) {
            isForbiddenTopic = true;
            break;
        }
    }
    
    if (isForbiddenTopic) {
        appendMessage("user", message);
        playSendSound();
        
        // Add a small delay to simulate processing
        setTimeout(() => {
            const rejectionMessage = "I'm focused exclusively on travel topics. I can help with routes, weather, and trip planning. Please ask me travel-related questions only.";
            appendMessage("roadie", rejectionMessage);
            
            // Style as warning and add animation
            const lastMessage = document.querySelector(".message.roadie:last-child");
            if (lastMessage) {
                lastMessage.style.background = "linear-gradient(135deg, #f44336, #ff9800)";
                lastMessage.classList.add("warning");
                
                // Show some helpful travel suggestions
                setTimeout(() => {
                    showSuggestions([
                        "Weather in San Francisco",
                        "Best stops between Miami and Orlando",
                        "Plan a trip from Chicago to Detroit",
                        "Travel time from LA to San Diego"
                    ]);
                }, 500);
            }
        }, 500);
        
        input.value = "";
        return;
    }

    appendMessage("user", message);
    playSendSound(); // Sound effect
    input.value = "";
    
    // Show button animation
    const sendButton = document.querySelector('.input-group button');
    if (sendButton) {
        sendButton.classList.add('sending');
        setTimeout(() => sendButton.classList.remove('sending'), 300);
    }

    showTypingIndicator();

    try {
        const res = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message, json_format: useJsonFormat })
        });

        if (!res.ok) throw new Error(`HTTP error: ${res.status}`);
        
        const data = await res.json();
        hideTypingIndicator();

        // Small delay for more natural conversation
        setTimeout(() => {
            // Enhanced weather detection
            const isWeatherRequest = (
                message.match(/weather|temperature|raining|forecast/i) &&
                data.text.includes("Weather in")
            );
            
            if (isWeatherRequest) {
                appendMessage("roadie", data.text);
            } else {
                if (useJsonFormat && data.summary) {
                    appendMessage("roadie", renderJsonResponse(data));
                } else {
                    appendMessage("roadie", data.text);
                }
            }
            
            // Detect if this is an off-topic redirection
            const isOffTopic = data.text.includes("I'm solely focused on travel assistance") &&
                              !message.includes("who are you");
            
            // Add a visual indicator if the message is a redirect from an off-topic query
            if (isOffTopic) {
                const lastMessage = document.querySelector(".message.roadie:last-child");
                if (lastMessage) {
                    lastMessage.style.background = "linear-gradient(135deg, #f44336, #ff9800)";
                    
                    const noteElement = document.createElement("div");
                    noteElement.classList.add("topic-note");
                    noteElement.innerHTML = "⚠️ <i>I can only answer questions about travel, routes, and weather</i>";
                    noteElement.style.fontSize = "14px";
                    noteElement.style.opacity = "0.9";
                    noteElement.style.marginTop = "8px";
                    noteElement.style.fontWeight = "500";
                    lastMessage.appendChild(noteElement);
                }
            }
            
            // Only show suggestions after a small delay
            if (data.suggestions && data.suggestions.length) {
                setTimeout(() => {
                    showSuggestions(data.suggestions);
                }, 500);
            }
        }, 300);
    } catch (error) {
        hideTypingIndicator();
        console.error("API error:", error);
        
        // Show error message with retry option
        appendMessage("roadie", "Sorry, I couldn't process that request. Please try again with a travel-related question.");
    }
}

// Start voice recognition with visual feedback
function startListening() {
    // Show listening indicator
    const micButton = document.querySelector('button[onclick="startListening()"]');
    const originalText = micButton.innerHTML;
    micButton.innerHTML = "🎤 Listening...";
    micButton.style.background = "linear-gradient(135deg, #f44336, #ff9800)";
    
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = 'en-US';
    recognition.interimResults = true;
    
    const messageInput = document.getElementById("messageInput");
    messageInput.placeholder = "Listening...";
    
    let finalTranscript = '';
    
    recognition.onresult = (event) => {
        let interimTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
                finalTranscript += event.results[i][0].transcript;
            } else {
                interimTranscript += event.results[i][0].transcript;
            }
        }
        
        // Show interim results
        messageInput.value = interimTranscript || finalTranscript;
    };
    
    recognition.onend = () => {
        // Restore button
        micButton.innerHTML = originalText;
        micButton.style.background = "";
        messageInput.placeholder = "Ask Roadie anything...";
        
        if (finalTranscript) {
            messageInput.value = finalTranscript;
            setTimeout(() => sendMessage(), 300);
        }
    };
    
    recognition.onerror = (event) => {
        console.error("Speech recognition error", event.error);
        micButton.innerHTML = originalText;
        micButton.style.background = "";
        messageInput.placeholder = "Ask Roadie anything...";
    };
    
    recognition.start();
}

// Enhanced plan trip function - simplified to focus only on text responses
async function planTrip() {
    const start = document.getElementById("start").value;
    const end = document.getElementById("end").value;
    
    // Validate required fields
    if (!start || !end) {
        alert("Please enter starting point and destination");
        return;
    }
    
    // Show trip summary
    const summary = document.getElementById('tripSummary');
    summary.style.display = 'block';
    document.getElementById('summaryDistance').textContent = 'Distance: Calculating...';
    document.getElementById('summaryDuration').textContent = 'Duration: Calculating...';
    document.getElementById('summaryFuelCost').textContent = 'Fuel Cost: Calculating...';
    
    // Create a well-formatted message
    const message = `Plan a trip from ${start} to ${end}`;
    
    try {
        // Use the regular chat API
        const res = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message })
        });
        
        if (!res.ok) throw new Error(`HTTP error: ${res.status}`);
        const data = await res.json();
        
        // Display result in the chat interface
        appendMessage("user", message);
        appendMessage("roadie", data.text);
        
        // Try to extract distance and duration from the response for summary
        const distanceMatch = data.text.match(/distance:\s*([\d,.]+ (?:km|miles|mi))/i);
        const durationMatch = data.text.match(/duration:\s*([\d.]+ (?:hours|hrs|days)(?:\s+and\s+\d+\s+minutes)?)/i);
        const costMatch = data.text.match(/(?:fuel cost|cost|budget):\s*\$?([\d,.]+)/i);
        
        if (distanceMatch) {
            document.getElementById('summaryDistance').textContent = `Distance: ${distanceMatch[1]}`;
        }
        if (durationMatch) {
            document.getElementById('summaryDuration').textContent = `Duration: ${durationMatch[1]}`;
        }
        if (costMatch) {
            document.getElementById('summaryFuelCost').textContent = `Est. Fuel Cost: $${costMatch[1]}`;
        }
        
        if (data.suggestions && data.suggestions.length) {
            showSuggestions(data.suggestions);
        }
        
    } catch (error) {
        console.error("API error:", error);
        alert("Sorry, there was an error planning your trip. Please try again.");
        
        // Reset summary
        document.getElementById('summaryDistance').textContent = 'Distance: Not available';
        document.getElementById('summaryDuration').textContent = 'Duration: Not available';
        document.getElementById('summaryFuelCost').textContent = 'Fuel Cost: Not available';
    }
}

// Load available voices into the dropdown with improved handling
function populateVoices() {
    const voices = speechSynthesis.getVoices();
    const voiceSelect = document.getElementById('voiceSelect');
    if (!voiceSelect) return;
    voiceSelect.innerHTML = '';

    if (voices.length === 0) {
        // Retry loading voices if not available yet
        setTimeout(populateVoices, 100);
        return;
    }

    // Group voices by language
    const voicesByLang = {};
    voices.forEach((voice, index) => {
        if (!voicesByLang[voice.lang]) {
            voicesByLang[voice.lang] = [];
        }
        voicesByLang[voice.lang].push({ voice, index });
    });

    // Create optgroups by language
    Object.keys(voicesByLang).sort().forEach(lang => {
        const langVoices = voicesByLang[lang];
        const optgroup = document.createElement('optgroup');
        optgroup.label = new Intl.DisplayNames(['en'], { type: 'language' }).of(lang.split('-')[0]) || lang;

        langVoices.forEach(({ voice, index }) => {
            const option = document.createElement('option');
            option.value = index;
            option.textContent = `${voice.name}${voice.default ? ' — Default' : ''}`;
            optgroup.appendChild(option);
        });

        voiceSelect.appendChild(optgroup);
    });

    // Select a good default
    const defaultVoice = voices.findIndex(voice =>
        voice.name.includes("Samantha") ||
        voice.name.includes("Google US English Female") ||
        (voice.lang === "en-US" && voice.name.includes("Female"))
    );

    if (defaultVoice >= 0) {
        voiceSelect.value = defaultVoice;
    }
}

// Ensure voices are populated when they are loaded
if (typeof speechSynthesis !== "undefined") {
    populateVoices();
    speechSynthesis.onvoiceschanged = populateVoices;
}

let useJsonFormat = false; // Toggle for JSON response format

// Update the DOMContentLoaded event handler to properly bind the Enter key
window.addEventListener('DOMContentLoaded', () => {
    // Check for system dark mode preference
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        document.body.classList.add('dark-mode');
        document.querySelectorAll('.toggle-btn')[1].innerHTML = '☀️';
    }
    
    if (typeof speechSynthesis !== "undefined") {
        populateVoices();
        speechSynthesis.onvoiceschanged = populateVoices;
    }

    // Fix the Enter key event listener
    const input = document.getElementById("messageInput");
    if (input) {
        input.addEventListener("keypress", function(event) {
            if (event.key === "Enter") {
                event.preventDefault();
                sendMessage();
            }
        });
        
        // Add focus animation to input
        input.addEventListener("focus", function() {
            this.parentElement.classList.add("input-focused");
        });
        
        input.addEventListener("blur", function() {
            this.parentElement.classList.remove("input-focused");
        });
    }
});
