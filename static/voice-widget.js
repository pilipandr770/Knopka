// Файл: static/voice-widget.js

let mediaRecorder;
let audioChunks = [];
let isRecording = false;
let autoplay = true;
let recordTimeout;

const chatBox = document.createElement("div");
chatBox.id = "chat-box";
document.body.appendChild(chatBox);

function appendMessage(text, isUser = false) {
    const msg = document.createElement("div");
    msg.className = isUser ? "chat-message user" : "chat-message assistant";
    msg.textContent = text;
    chatBox.appendChild(msg);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function appendAudioPlayer(audioUrl, label) {
    const container = document.createElement("div");
    container.className = "audio-container";

    const labelEl = document.createElement("div");
    labelEl.className = "audio-label";
    labelEl.textContent = label;

    const audio = document.createElement("audio");
    audio.controls = true;
    audio.src = audioUrl;

    container.appendChild(labelEl);
    container.appendChild(audio);
    chatBox.appendChild(container);
    chatBox.scrollTop = chatBox.scrollHeight;

    if (autoplay) {
        audio.play().catch(e => console.log("🔇 Автовідтворення заборонено браузером:", e));
    }
}

function sendRecording() {
    const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
    const formData = new FormData();
    formData.append("file", audioBlob, "recording.webm");

    const clientId = localStorage.getItem("client_id") || Math.random().toString(36).substring(2);
    localStorage.setItem("client_id", clientId);
    formData.append("client_id", clientId);

    appendMessage("🎤 Повідомлення відправлено", true);

    fetch("/process_audio", {
        method: "POST",
        body: formData
    }).then(async response => {
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);

        const assistantText = decodeURIComponent(response.headers.get("X-Assistant-Answer") || "🤖 Немає відповіді");
        const userText = decodeURIComponent(response.headers.get("X-User-Text") || "");

        if (userText && userText !== "🎤 Повідомлення відправлено") {
            appendMessage(userText, true);
        }

        appendAudioPlayer(audioUrl, assistantText);
    }).catch(error => {
        console.error("Помилка:", error);
        appendMessage("⚠️ Помилка при надсиланні аудіо", false);
    });
}

function startRecording() {
    if (isRecording) return;
    isRecording = true;
    recordButton.classList.add("recording");

    navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
        mediaRecorder = new MediaRecorder(stream);
        mediaRecorder.start();
        audioChunks = [];

        mediaRecorder.addEventListener("dataavailable", event => {
            audioChunks.push(event.data);
        });

        mediaRecorder.addEventListener("stop", () => {
            isRecording = false;
            recordButton.classList.remove("recording");
            sendRecording();
        });

        // ⏱ Обмеження по часу — максимум 30 секунд
        recordTimeout = setTimeout(() => {
            if (isRecording) {
                console.log("⏰ Автоматичне завершення через 30 сек");
                stopRecording();
            }
        }, 30000);
    }).catch(err => {
        console.error("🎙️ Доступ до мікрофона заборонено:", err);
        appendMessage("❌ Не вдалося отримати доступ до мікрофона", true);
        isRecording = false;
        recordButton.classList.remove("recording");
    });
}

function stopRecording() {
    if (!isRecording) return;
    isRecording = false;
    recordButton.classList.remove("recording");
    clearTimeout(recordTimeout);
    if (mediaRecorder && mediaRecorder.state === "recording") {
        mediaRecorder.stop();
    }
}

// 🎤 Кнопка мікрофона
const recordButton = document.createElement("button");
recordButton.className = "voice-button";
recordButton.innerHTML = "🎤";
recordButton.title = "Утримуй, щоб записати (до 30 сек)";
document.body.appendChild(recordButton);

// 👉 Події натискання й утримання
recordButton.addEventListener("mousedown", startRecording);
recordButton.addEventListener("touchstart", startRecording);
recordButton.addEventListener("mouseup", stopRecording);
recordButton.addEventListener("mouseleave", stopRecording);
recordButton.addEventListener("touchend", stopRecording);

// 🎚️ Перемикач автовідтворення
const autoplayToggle = document.createElement("label");
autoplayToggle.className = "autoplay-toggle";
autoplayToggle.innerHTML = `
  <input type="checkbox" checked id="autoplay-check" />
  🔊 Автовідтворення
`;
document.body.appendChild(autoplayToggle);
document.getElementById("autoplay-check").addEventListener("change", e => {
    autoplay = e.target.checked;
});
