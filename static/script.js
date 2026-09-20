function sendMessage() {

    const input = document.getElementById("message");
    const message = input.value.trim();

    if (message === "") {
        return;
    }

    const chatBox = document.getElementById("chat-box");

    // User message
    chatBox.innerHTML += `
        <div class="message user-message">
            <div class="message-content">
                ${message}
            </div>
        </div>
    `;

    input.value = "";

    chatBox.scrollTop = chatBox.scrollHeight;

    fetch("/chat", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            message: message
        })
    })
    .then(async response => {

        // Get the actual response from Flask
        const text = await response.text();

        console.log("HTTP Status:", response.status);
        console.log("Server Response:", text);

        // Try to convert response to JSON
        let data;

        try {
            data = JSON.parse(text);
        } catch (error) {
            throw new Error(
                "Server returned non-JSON response: " + text
            );
        }

        // If Flask returned an error status
        if (!response.ok) {
            throw new Error(
                data.reply || `Server error: ${response.status}`
            );
        }

        return data;
    })
    .then(data => {

        chatBox.innerHTML += `
            <div class="message bot-message">
                <div class="message-content">
                    ${data.reply}
                </div>
            </div>
        `;

        chatBox.scrollTop = chatBox.scrollHeight;
    })
    .catch(error => {

        console.error("CHAT ERROR:", error);

        chatBox.innerHTML += `
            <div class="message bot-message">
                <div class="message-content">
                    ${error.message}
                </div>
            </div>
        `;

        chatBox.scrollTop = chatBox.scrollHeight;
    });
}
// ==========================================
// PDF UPLOAD
// ==========================================

document.getElementById("pdf-file").addEventListener("change", function () {

    const file = this.files[0];

    if (!file) {
        return;
    }

    if (!file.name.toLowerCase().endsWith(".pdf")) {

        alert("Please select a PDF file.");

        this.value = "";

        return;
    }


    const formData = new FormData();

    formData.append("file", file);


    const status = document.getElementById("upload-status");

    status.innerText = "Uploading PDF...";


    fetch("/upload", {
        method: "POST",
        body: formData
    })

    .then(response => response.json())

    .then(data => {

        if (data.message) {

            status.innerText = data.message;

            console.log("PDF upload result:", data);

        }

    })

    .catch(error => {

        console.error("PDF upload error:", error);

        status.innerText =
            "Could not upload PDF.";

    });

});