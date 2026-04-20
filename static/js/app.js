document.addEventListener("DOMContentLoaded", () => {
    setupChatbot();
    setupCharts();
});

function setupChatbot() {
    const input = document.getElementById("chatbotInput");
    const sendButton = document.getElementById("chatbotSend");
    const messages = document.getElementById("chatbotMessages");

    if (!input || !sendButton || !messages) {
        return;
    }

    const submitChat = async () => {
        const message = input.value.trim();
        if (!message) {
            return;
        }

        appendMessage(messages, message, "user-message");
        input.value = "";

        try {
            const response = await fetch("/chatbot", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message }),
            });
            const data = await response.json();
            appendMessage(messages, data.reply || "Service unavailable right now.", "bot-message");
        } catch (error) {
            appendMessage(messages, "Unable to connect to the chatbot right now.", "bot-message");
        }
    };

    sendButton.addEventListener("click", submitChat);
    input.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
            event.preventDefault();
            submitChat();
        }
    });
}

function appendMessage(container, text, className) {
    const wrapper = document.createElement("div");
    wrapper.className = className;
    wrapper.textContent = text;
    container.appendChild(wrapper);
    container.scrollTop = container.scrollHeight;
}

function setupCharts() {
    if (typeof Chart === "undefined" || !window.adminAnalytics) {
        return;
    }

    createChart("farmersChart", "bar", ["Total", "Pending", "Approved"], [
        window.adminAnalytics.total_farmers,
        window.adminAnalytics.pending_farmers,
        window.adminAnalytics.approved_farmers,
    ], ["#0d5ea6", "#e0a11d", "#228b52"], "Farmer Count");

    createChart("subsidyChart", "doughnut", ["Pending", "Approved"], [
        window.adminAnalytics.subsidy_pending,
        window.adminAnalytics.subsidy_approved,
    ], ["#f4be4f", "#0f6b46"], "Subsidy Distribution");

    createChart("insuranceChart", "pie", ["Pending", "Approved"], [
        window.adminAnalytics.insurance_pending,
        window.adminAnalytics.insurance_approved,
    ], ["#78a7d4", "#2ca36c"], "Insurance Approvals");

    createChart("complaintsChart", "bar", ["Open/In Progress", "Resolved"], [
        window.adminAnalytics.complaint_open,
        window.adminAnalytics.complaint_resolved,
    ], ["#b63d36", "#228b52"], "Complaints Overview");
}

function createChart(canvasId, type, labels, data, colors, title) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) {
        return;
    }

    new Chart(canvas, {
        type,
        data: {
            labels,
            datasets: [{
                label: title,
                data,
                backgroundColor: colors,
                borderRadius: 10,
                borderWidth: 0,
            }],
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: true,
                    position: "bottom",
                },
                title: {
                    display: true,
                    text: title,
                    color: "#1b2a36",
                    font: { size: 18, weight: "700" },
                },
            },
        },
    });
}
