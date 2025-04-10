// 📁 static/voice-widget.js (з адаптивним fetch)

let mediaRecorder;
let audioChunks = [];
let isRecording = false;
let autoplay = true;
let recordTimeout;
let interactionMode = "voice+chat"; // за замовчуванням
const baseUrl = window.location.origin;

const floatingChat = document.createElement("div");
floatingChat.id = "floating-chat";
floatingChat.style.display = "none";
floatingChat.innerHTML = `
  <div id="chat-box"></div>
  <button onclick="document.getElementById('floating-chat').style.display='none'">❌</button>
`;
document.body.appendChild(floatingChat);

function appendMessage(text, isUser = false) {
    if (interactionMode !== "voice+chat") return;
    const msg = document.createElement("div");
    msg.className = isUser ? "chat-message user" : "chat-message assistant";
    msg.textContent = text;
    document.getElementById("chat-box").appendChild(msg);
    document.getElementById("chat-box").scrollTop = 999999;
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

    if (interactionMode === "voice+chat") {
        document.getElementById("chat-box").appendChild(container);
    }

    if (autoplay) audio.play().catch(() => {});
}

function sendRecording() {
    const audioBlob = new Blob(audioChunks, { type: "audio/webm; codecs=opus" }); // ✅ ключова зміна
    const formData = new FormData();
    formData.append("file", audioBlob, "recording.webm");

    const clientId = localStorage.getItem("client_id") || Math.random().toString(36).substring(2);
    localStorage.setItem("client_id", clientId);
    formData.append("client_id", clientId);

    if (interactionMode === "voice+chat") {
        appendMessage("🎤 Повідомлення відправлено", true);
    }

    fetch(`${baseUrl}/process_audio`, {
        method: "POST",
        body: formData
    }).then(async response => {
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        const assistantText = decodeURIComponent(response.headers.get("X-Assistant-Answer") || "🤖 Немає відповіді");
        const userText = decodeURIComponent(response.headers.get("X-User-Text") || "");

        if (userText && interactionMode === "voice+chat") {
            appendMessage(userText, true);
        }

        appendAudioPlayer(audioUrl, assistantText);
    }).catch(err => {
        console.error("❌ Помилка при відправці аудіо:", err);
        appendMessage("⚠️ Помилка з'єднання з сервером", false);
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

        mediaRecorder.addEventListener("dataavailable", event => audioChunks.push(event.data));
        mediaRecorder.addEventListener("stop", () => {
            isRecording = false;
            recordButton.classList.remove("recording");
            sendRecording();
        });

        recordTimeout = setTimeout(() => {
            if (isRecording) stopRecording();
        }, 30000);

        if (interactionMode === "voice+chat") {
            floatingChat.style.display = "flex";
        }
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

const recordButton = document.createElement("button");
recordButton.className = "voice-button";
recordButton.innerHTML = "🎤";
recordButton.title = "Утримуй, щоб записати (до 30 сек)";
document.body.appendChild(recordButton);
recordButton.addEventListener("mousedown", startRecording);
recordButton.addEventListener("touchstart", startRecording);
recordButton.addEventListener("mouseup", stopRecording);
recordButton.addEventListener("mouseleave", stopRecording);
recordButton.addEventListener("touchend", stopRecording);

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

    if (audioBlob.size < 1000) {
    alert("⚠️ Помилка: аудіо занадто коротке або порожнє. Спробуйте ще раз.");
    return;
}

console.log("📦 Audio blob:", audioBlob);
console.log("📏 Розмір blob:", audioBlob.size);

fetch("/static/widget_settings.json")
  .then(r => r.json())
  .then(cfg => interactionMode = cfg.interaction_mode || "voice+chat");
