// 📁 static/voice-widget.js

document.addEventListener("DOMContentLoaded", () => {
  const widget = document.createElement("div");
  widget.id = "voice-widget";
  widget.innerHTML = `
    <div id="chat-container" style="display: none;"></div>
    <button id="record-button">🎤</button>
  `;
  document.body.appendChild(widget);

  const recordButton = document.getElementById("record-button");
  const chatContainer = document.getElementById("chat-container");

  let mediaRecorder;
  let chunks = [];

  const supportsAudioRecording = !!(navigator.mediaDevices && window.MediaRecorder);
  const isRestrictedDevice = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;

  function fallbackToTextChat() {
    recordButton.style.display = "none";
    chatContainer.style.display = "block";
    chatContainer.innerHTML = `
      <p>👋 Вибачте, ваш пристрій не підтримує голосовий запис. Ви можете спілкуватися з асистентом у чаті нижче.</p>
      <input type="text" id="chat-input" placeholder="Напишіть запит..." />
      <button id="send-chat">Надіслати</button>
      <div id="chat-log"></div>
    `;
    document.getElementById("send-chat").onclick = async () => {
      const input = document.getElementById("chat-input");
      const log = document.getElementById("chat-log");
      const text = input.value.trim();
      if (!text) return;
      input.value = "";
      log.innerHTML += `<div><b>Ви:</b> ${text}</div>`;
      const response = await fetch("/process_audio", {
        method: "POST",
        body: JSON.stringify({ text }),
        headers: { "Content-Type": "application/json" }
      });
      const data = await response.json();
      log.innerHTML += `<div><b>Асистент:</b> ${data.response}</div>`;
    };
  }

  if (!supportsAudioRecording || isRestrictedDevice) {
    fallbackToTextChat();
    return;
  }

  recordButton.onclick = async () => {
    if (mediaRecorder && mediaRecorder.state === "recording") {
      mediaRecorder.stop();
      recordButton.textContent = "🎤";
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        chunks = [];
        mediaRecorder.ondataavailable = e => chunks.push(e.data);
        mediaRecorder.onstop = async () => {
          const blob = new Blob(chunks, { type: "audio/webm" });
          const formData = new FormData();
          formData.append("audio", blob, "recording.webm");
          const response = await fetch("/process_audio", { method: "POST", body: formData });
          const data = await response.json();
          alert("GPT: " + data.response);
        };
        mediaRecorder.start();
        recordButton.textContent = "⏹️";
      } catch (err) {
        console.error("Error accessing mic:", err);
        fallbackToTextChat();
      }
    }
  };
});
