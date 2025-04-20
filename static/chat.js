document.addEventListener("DOMContentLoaded", () => {
    const chatForm = document.getElementById("chat-form");
    const chatInput = document.getElementById("chat-input");
    const chatBox = document.getElementById("chat-box");

    chatForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const userMessage = chatInput.value.trim();
        if (!userMessage) return;

        // Display user message in the chatbox
        appendMessage("You", userMessage);
        chatInput.value = "";

        try {
            const response = await fetch("/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: userMessage })
            });

            if (response.ok) {
                const data = await response.json();
                appendMessage("Roadie", data.text);

                // Optionally handle map embeds or suggestions
                if (data.map_embed) {
                    appendMapEmbed(data.map_embed);
                }
            } else {
                appendMessage("Roadie", "Sorry, something went wrong. Please try again.");
            }
        } catch (error) {
            console.error("Error:", error);
            appendMessage("Roadie", "Sorry, I couldn't connect to the server.");
        }
    });

    function appendMessage(sender, message) {
        const messageElement = document.createElement("div");
        messageElement.className = sender === "You" ? "user-message" : "bot-message";
        messageElement.textContent = `${sender}: ${message}`;
        chatBox.appendChild(messageElement);
        chatBox.scrollTop = chatBox.scrollHeight; // Scroll to the latest message
    }

    function appendMapEmbed(embedUrl) {
        const iframe = document.createElement("iframe");
        iframe.src = embedUrl;
        iframe.width = "100%";
        iframe.height = "300px";
        iframe.style.border = "none";
        chatBox.appendChild(iframe);
        chatBox.scrollTop = chatBox.scrollHeight; // Scroll to the latest message
    }
});
