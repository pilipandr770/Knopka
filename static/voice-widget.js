// 📁 static/voice-widget.js — повна версія з мікрофоном, TTS, текстовим полем і компактним чатом

document.addEventListener("DOMContentLoaded", () => {
    let mediaRecorder;
    let audioChunks = [];
    let isRecording = false;
    let recordTimeout;
    let autoplay = true;
    let interactionMode = "voice+chat";
    let isExpanded = false;

    const assistantUI = document.createElement("div");
    assistantUI.id = "main-assistant-chat";
    assistantUI.style.display = "none";
    assistantUI.style.opacity = "0";
    assistantUI.innerHTML = `
      <div id="assistant-header">
        <span>🤖 Асистент</span>
        <div class="header-controls">
          <button id="toggle-size">📐</button>
          <button id="close-assistant">❌</button>
        </div>
      </div>
      <div id="chat-box"></div>
      <div id="assistant-controls">
        <label><input type="checkbox" id="autoplay-check" checked /> 🔊 Автовідтворення</label>
        <div id="text-input-wrapper">
          <input type="text" id="text-input" placeholder="Напишіть повідомлення...">
          <button id="send-text">📨</button>
        </div>
      </div>
    `;
    document.body.appendChild(assistantUI);

    function appendMessage(text, isUser = false) {
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
      document.getElementById("chat-box").appendChild(container);
      if (autoplay) audio.play().catch(() => {});
    }

    function playAudioFromBlob(blob) {
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      if (autoplay) {
        audio.play().catch(() => {});
      }
    }

    function sendTextMessage() {
      const input = document.getElementById("text-input");
      const text = input.value.trim();
      if (!text) return;
      const clientId = localStorage.getItem("client_id") || Math.random().toString(36).substring(2);
      localStorage.setItem("client_id", clientId);
      appendMessage(text, true);
      input.value = "";

      fetch("/process_text", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, client_id: clientId })
      })
        .then(res => res.json())
        .then(data => {
          appendMessage(data.answer);
          if (autoplay) {
            const audio = new Audio(`/tts?text=${encodeURIComponent(data.answer)}`);
            audio.play().catch(() => {});
          }
        });
    }

    document.addEventListener("click", e => {
      if (e.target.id === "send-text") sendTextMessage();
    });
    document.addEventListener("keydown", e => {
      if (e.key === "Enter" && document.activeElement.id === "text-input") sendTextMessage();
    });

    function showAssistantUI() {
      assistantUI.style.display = "flex";
      requestAnimationFrame(() => {
        assistantUI.style.opacity = "1";
      });
    }

    function hideAssistantUI() {
      assistantUI.style.opacity = "0";
      setTimeout(() => {
        assistantUI.style.display = "none";
      }, 300); // Час анімації в мс
    }

    function startRecording() {
      if (isRecording) return;

      navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
          try {
            isRecording = true;
            recordButton.classList.add("recording");

            mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.start();
            audioChunks = [];

            mediaRecorder.addEventListener("dataavailable", event => audioChunks.push(event.data));
            mediaRecorder.addEventListener("stop", () => {
              isRecording = false;
              recordButton.classList.remove("recording");
              stream.getTracks().forEach(track => track.stop());
              if (audioChunks.length > 0) {
                sendRecording();
              }
            });

            recordTimeout = setTimeout(() => {
              if (isRecording) stopRecording();
            }, 30000);

            showAssistantUI();
          } catch (err) {
            console.error("MediaRecorder initialization error:", err);
            stopRecording();
            appendMessage("⚠️ Помилка ініціалізації запису. Спробуйте ще раз.");
          }
        })
        .catch(err => {
          console.error("getUserMedia error:", err);
          isRecording = false;
          recordButton.classList.remove("recording");
          appendMessage("⚠️ Помилка доступу до мікрофона. Перевірте налаштування браузера.");
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

    function sendRecording() {
      const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
      const formData = new FormData();
      formData.append("audio", audioBlob, "recording.webm");
      const clientId = localStorage.getItem("client_id") || Math.random().toString(36).substring(2);
      localStorage.setItem("client_id", clientId);
      formData.append("client_id", clientId);
      appendMessage("🎤 Повідомлення відправлено", true);
      fetch("/process_audio", {
        method: "POST",
        body: formData
      }).then(async response => {
        const audioBlob = await response.blob();
        const assistantText = decodeURIComponent(response.headers.get("X-Assistant-Answer") || "🤖 Немає відповіді");
        const userText = decodeURIComponent(response.headers.get("X-User-Text") || "");
        if (userText) appendMessage(userText, true);
        playAudioFromBlob(audioBlob);
        appendAudioPlayer(URL.createObjectURL(audioBlob), assistantText);
      });
    }

    const recordButton = document.createElement("button");
    recordButton.className = "voice-button";
    recordButton.innerHTML = "🎤";
    recordButton.title = "Утримуйте, щоб записати";
    document.body.appendChild(recordButton);

    recordButton.style.display = "none";
    assistantUI.style.display = "none";

    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
          recordButton.style.display = "block";

          recordButton.addEventListener("mousedown", startRecording);
          recordButton.addEventListener("touchstart", startRecording);
          recordButton.addEventListener("mouseup", stopRecording);
          recordButton.addEventListener("mouseleave", stopRecording);
          recordButton.addEventListener("touchend", stopRecording);

          stream.getTracks().forEach(track => track.stop());
        })
        .catch(err => {
          console.error("Microphone access error:", err);
          recordButton.style.display = "none";
          showAssistantUI();
          appendMessage("⚠️ Немає доступу до мікрофона. Ви можете використовувати текстовий чат.");
        });
    } else {
      console.error("getUserMedia not supported");
      recordButton.style.display = "none";
      showAssistantUI();
      appendMessage("⚠️ Ваш браузер не підтримує запис голосу. Ви можете використовувати текстовий чат.");
    }

    document.getElementById("autoplay-check").addEventListener("change", e => {
      autoplay = e.target.checked;
    });
    document.getElementById("close-assistant").addEventListener("click", hideAssistantUI);

    document.getElementById("toggle-size").addEventListener("click", () => {
      isExpanded = !isExpanded;
      if (isExpanded) {
        assistantUI.classList.add("expanded");
      } else {
        assistantUI.classList.remove("expanded");
      }
    });

    fetch("/static/widget_settings.json")
      .then(r => r.json())
      .then(cfg => {
        interactionMode = cfg.interaction_mode || "voice+chat";
        if (cfg.button) {
          const btn = cfg.button;
          if (btn.text) recordButton.innerHTML = btn.text;
          if (btn.color) recordButton.style.color = btn.color;
          if (btn.background) recordButton.style.backgroundColor = btn.background;
          if (btn.size) {
            recordButton.style.width = btn.size;
            recordButton.style.height = btn.size;
            recordButton.style.fontSize = `calc(${btn.size} * 0.5)`;
          }
          if (btn.position) {
            if (btn.position.includes("bottom")) recordButton.style.bottom = "20px";
            if (btn.position.includes("top")) recordButton.style.top = "20px";
            if (btn.position.includes("left")) recordButton.style.left = "20px";
            if (btn.position.includes("right")) recordButton.style.right = "20px";
          }
        }
      });

    const style = document.createElement("style");
    style.innerHTML = `
    #main-assistant-chat {
      position: fixed;
      bottom: 100px;
      right: 20px;
      width: 320px;
      height: 400px;
      background: white;
      z-index: 9999;
      display: flex;
      flex-direction: column;
      border-radius: 12px;
      box-shadow: 0 0 10px rgba(0,0,0,0.2);
      transition: all 0.3s ease;
      max-height: 80vh;
      opacity: 1;
      transform-origin: bottom right;
    }

    #main-assistant-chat.expanded {
      width: 90%;
      height: 90vh;
      bottom: 5vh;
      right: 5%;
    }

    #assistant-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: #4CAF50;
      color: white;
      padding: 10px 20px;
      font-size: 18px;
      border-radius: 12px 12px 0 0;
    }

    .header-controls {
      display: flex;
      gap: 10px;
    }

    .header-controls button {
      background: none;
      border: none;
      color: white;
      cursor: pointer;
      font-size: 16px;
      padding: 4px;
    }

    #chat-box {
      flex: 1;
      overflow-y: auto;
      padding: 15px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    .chat-message {
      padding: 10px 14px;
      border-radius: 12px;
      max-width: 85%;
      white-space: pre-wrap;
      font-size: 14px;
      line-height: 1.4;
      animation: slideIn 0.3s ease;
    }

    .chat-message.user {
      align-self: flex-end;
      background: #e3f2fd;
      text-align: right;
    }

    .chat-message.assistant {
      align-self: flex-start;
      background: #f5f5f5;
      text-align: left;
    }

    .audio-container {
      margin-top: 5px;
      width: 100%;
    }

    .audio-label {
      font-size: 0.85em;
      margin-bottom: 3px;
      color: #333;
    }

    #assistant-controls {
      padding: 10px;
      border-top: 1px solid #ddd;
      background: #f9f9f9;
      border-radius: 0 0 12px 12px;
    }

    #text-input-wrapper {
      display: flex;
      gap: 8px;
      margin-top: 8px;
    }

    #text-input {
      flex: 1;
      padding: 8px 12px;
      border: 1px solid #ddd;
      border-radius: 20px;
      font-size: 14px;
    }

    #send-text {
      background: #4CAF50;
      color: white;
      border: none;
      border-radius: 50%;
      width: 36px;
      height: 36px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .voice-button {
      position: fixed;
      bottom: 20px;
      right: 20px;
      width: 60px;
      height: 60px;
      font-size: 24px;
      border-radius: 50%;
      border: none;
      background-color: #4CAF50;
      color: white;
      box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
      cursor: pointer;
      z-index: 9999;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .voice-button:hover {
      transform: scale(1.05);
      box-shadow: 0 6px 15px rgba(0, 0, 0, 0.3);
    }

    .voice-button:active {
      transform: scale(0.95);
    }

    .voice-button.recording {
      background-color: #f44336;
      animation: pulse 1s infinite;
    }

    @keyframes pulse {
      0% { box-shadow: 0 0 0 0 rgba(244,67,54,0.4); }
      70% { box-shadow: 0 0 0 10px rgba(244,67,54,0); }
      100% { box-shadow: 0 0 0 0 rgba(244,67,54,0); }
    }

    @keyframes slideIn {
      from {
        opacity: 0;
        transform: translateY(20px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    audio {
      width: 100%;
      margin-top: 5px;
    }

    @media (max-width: 768px) {
      #main-assistant-chat {
        width: 90%;
        right: 5%;
        bottom: 80px;
      }
    }`;

    document.head.appendChild(style);
  });
