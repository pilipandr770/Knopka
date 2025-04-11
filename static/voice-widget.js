// 📁 static/voice-widget.js (оновлений повністю з підтримкою режимів, TTS, адаптивного чату)

let mediaRecorder;
let audioChunks = [];
let isRecording = false;
let recordTimeout;
let autoplay = true;
let interactionMode = "voice+chat"; // дефолтне значення

const floatingChat = document.createElement("div");
floatingChat.id = "floating-chat";
floatingChat.style.display = "none";
floatingChat.innerHTML = `
  <div id="chat-box"></div>
  <button onclick="document.getElementById('floating-chat').style.display='none'">❌</button>
`;
document.body.appendChild(floatingChat);

function appendMessage(text, isUser = false) {
    if (interactionMode === "voice-only") return;
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

    if (interactionMode !== "voice-only") {
        document.getElementById("chat-box").appendChild(container);
    }

    if (autoplay) audio.play().catch(() => {});
}

function playAudioFromBlob(blob) {
    const audioUrl = URL.createObjectURL(blob);
    const audio = new Audio(audioUrl);
    if (autoplay) audio.play().catch(() => {});
}

function sendRecording() {
    const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
    const formData = new FormData();
    formData.append("file", audioBlob, "recording.webm");

    const clientId = localStorage.getItem("client_id") || Math.random().toString(36).substring(2);
    localStorage.setItem("client_id", clientId);
    formData.append("client_id", clientId);

    if (interactionMode === "voice+chat") {
        appendMessage("🎤 Повідомлення відправлено", true);
    }

    fetch("/process_audio", {
        method: "POST",
        body: formData
    }).then(async response => {
        const audioBlob = await response.blob();
        const assistantText = decodeURIComponent(response.headers.get("X-Assistant-Answer") || "🤖 Немає відповіді");
        const userText = decodeURIComponent(response.headers.get("X-User-Text") || "");

        if (userText && interactionMode !== "voice-only") {
            appendMessage(userText, true);
        }

        if (interactionMode !== "chat-only") {
            playAudioFromBlob(audioBlob);
        }

        if (interactionMode === "voice+chat") {
            appendAudioPlayer(URL.createObjectURL(audioBlob), assistantText);
        }
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

// Застосування interactionMode
fetch("/static/widget_settings.json")
  .then(r => r.json())
  .then(cfg => {
      interactionMode = cfg.interaction_mode || "voice+chat";
      if (interactionMode === "chat-only") {
          recordButton.style.display = "none";
          floatingChat.style.display = "flex";
      }
  });

// CSS через JS для адаптивного чату
const style = document.createElement("style");
style.innerHTML = `
.voice-button {
  position: fixed;
  bottom: 20px;
  right: 20px;
  font-size: 30px;
  padding: 15px;
  border-radius: 50%;
  border: none;
  background-color: #4CAF50;
  color: white;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
  cursor: pointer;
  z-index: 9999;
}

.voice-button.recording {
  background-color: red;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(255,0,0, 0.4); }
  70% { box-shadow: 0 0 0 10px rgba(255,0,0, 0); }
  100% { box-shadow: 0 0 0 0 rgba(255,0,0, 0); }
}

#floating-chat {
  position: fixed;
  bottom: 90px;
  right: 20px;
  width: 340px;
  max-height: 70vh;
  min-height: 220px;
  overflow-y: auto;
  background: white;
  border-radius: 12px;
  box-shadow: 0 0 12px rgba(0,0,0,0.2);
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  z-index: 9999;
}

#chat-box {
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow-y: auto;
  max-height: 60vh;
  font-size: 14px;
  padding-bottom: 10px;
}

.chat-message {
  padding: 8px 12px;
  border-radius: 6px;
  max-width: 75%;
  line-height: 1.4;
  white-space: pre-wrap;
}

.chat-message.user {
  align-self: flex-end;
  background-color: #d0f0d0;
  text-align: right;
}

.chat-message.assistant {
  align-self: flex-start;
  background-color: #f0f0f0;
  text-align: left;
}

.audio-container {
  margin-top: 5px;
}

.audio-label {
  font-size: 0.85em;
  margin-bottom: 3px;
  color: #333;
}

.autoplay-toggle {
  position: fixed;
  bottom: 160px;
  right: 20px;
  background: #fff;
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 0.9em;
  box-shadow: 0 0 5px rgba(0,0,0,0.2);
  z-index: 9999;
}

@media (max-width: 768px) {
  #floating-chat {
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    width: 100%;
    border-radius: 0;
  }
}
`;
document.head.appendChild(style);
