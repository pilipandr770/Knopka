// static/voice-widget.js

let isRecording = false;
let mediaRecorder;
let audioChunks = [];

const widgetButton = document.createElement("div");
widgetButton.id = "voice-widget-button";
widgetButton.innerHTML = `<div class="mic-icon">🎤</div>`;
document.body.appendChild(widgetButton);

const chatContainer = document.createElement("div");
chatContainer.id = "voice-widget-chat";
chatContainer.style.display = "none";
chatContainer.innerHTML = `
  <div class="chat-header">AI-помічник <span id="close-chat">×</span></div>
  <div id="chat-messages"></div>
  <form id="chat-form">
    <input type="text" id="chat-input" placeholder="Напишіть повідомлення..." autocomplete="off" />
    <button type="submit">Відправити</button>
  </form>
`;
document.body.appendChild(chatContainer);

const style = document.createElement("style");
style.innerHTML = `
#voice-widget-button {
  position: fixed;
  bottom: 20px;
  right: 20px;
  background: #4CAF50;
  color: white;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30px;
  cursor: pointer;
  box-shadow: 0 4px 10px rgba(0,0,0,0.3);
  z-index: 9999;
}
#voice-widget-chat {
  position: fixed;
  bottom: 100px;
  right: 20px;
  width: 320px;
  max-height: 400px;
  background: white;
  border: 1px solid #ccc;
  border-radius: 10px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  z-index: 9999;
  box-shadow: 0 4px 15px rgba(0,0,0,0.2);
}
.chat-header {
  background: #4CAF50;
  color: white;
  padding: 10px;
  font-weight: bold;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
#chat-messages {
  flex: 1;
  padding: 10px;
  overflow-y: auto;
  font-size: 14px;
}
#chat-form {
  display: flex;
  border-top: 1px solid #ddd;
}
#chat-input {
  flex: 1;
  padding: 8px;
  border: none;
  font-size: 14px;
}
#chat-form button {
  background: #4CAF50;
  color: white;
  border: none;
  padding: 8px 12px;
  cursor: pointer;
}
.user-msg { text-align: right; margin: 5px 0; }
.bot-msg { text-align: left; margin: 5px 0; color: #333; }
`;
document.head.appendChild(style);

widgetButton.addEventListener("mousedown", () => {
  if (window.MediaRecorder) {
    startRecording();
  } else {
    fallbackToChat();
  }
});

widgetButton.addEventListener("mouseup", () => {
  if (isRecording) {
    stopRecording();
  }
});

document.getElementById("close-chat").addEventListener("click", () => {
  chatContainer.style.display = "none";
});

const form = document.getElementById("chat-form");
const input = document.getElementById("chat-input");
const messages = document.getElementById("chat-messages");

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const userMessage = input.value.trim();
  if (!userMessage) return;

  appendMessage(userMessage, "user-msg");
  input.value = "";

  const response = await fetch("/process_audio", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: userMessage })
  });

  const data = await response.json();
  appendMessage(data.reply, "bot-msg");
});

function appendMessage(text, className) {
  const msg = document.createElement("div");
  msg.className = className;
  msg.textContent = text;
  messages.appendChild(msg);
  messages.scrollTop = messages.scrollHeight;
}

async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.start();
    isRecording = true;
    audioChunks = [];

    mediaRecorder.addEventListener("dataavailable", event => {
      audioChunks.push(event.data);
    });

    mediaRecorder.addEventListener("stop", async () => {
      const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
      const formData = new FormData();
      formData.append("audio", audioBlob, "recording.webm");

      const response = await fetch("/process_audio", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      chatContainer.style.display = "block";
      appendMessage(data.transcription || data.reply, "bot-msg");
    });
  } catch (err) {
    fallbackToChat();
  }
}

function stopRecording() {
  if (mediaRecorder && isRecording) {
    mediaRecorder.stop();
    isRecording = false;
  }
}

function fallbackToChat() {
  chatContainer.style.display = "block";
  appendMessage("Вибачте, ваш пристрій не підтримує запис голосу. Ви можете спілкуватися в чаті.", "bot-msg");
}

// Перевірка Safari
const isSafari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent);
if (isSafari || !navigator.mediaDevices || !window.MediaRecorder) {
  fallbackToChat();
}
