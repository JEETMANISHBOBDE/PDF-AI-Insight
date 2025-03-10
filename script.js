document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("question-form");
    const input = document.getElementById("question-input");
    const responseDiv = document.getElementById("response");

    form.addEventListener("submit", async function (event) {
        event.preventDefault(); // Prevent form from refreshing the page

        const userMessage = input.value.trim();
        if (!userMessage) {
            responseDiv.innerText = "Please enter a question!";
            return;
        }

        responseDiv.innerText = "Thinking..."; // Show loading text

        try {
            const response = await fetch("/ask_question", {
                method: "POST",
                body: JSON.stringify({ question: userMessage }),
                headers: { "Content-Type": "application/json" }
            });

            const data = await response.json();
            console.log(data); // Debugging: See response in the console

            if (data.answer) {
                responseDiv.innerText = "AI: " + data.answer;
            } else if (data.error) {
                responseDiv.innerText = "Error: " + data.error;
            } else {
                responseDiv.innerText = "No response from AI.";
            }
        } catch (error) {
            console.error("Fetch error:", error);
            responseDiv.innerText = "Failed to connect to the AI.";
        }

        input.value = ""; // Clear input field
    });
});
