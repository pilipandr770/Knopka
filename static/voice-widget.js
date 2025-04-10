// 📁 static/voice-widget.js

document.addEventListener("DOMContentLoaded", () => {
    let mediaRecorder;
    let audioChunks = [];
    let isRecording = false;
    let autoplay = true;
    let recordTimeout;
    let interactionMode = "voice+chat";
    const baseUrl = window.location.origin;

    const floatingChat = document.createElement("div");
    floatingChat.id = "floating-chat";
    floatingChat.style.display = "none";
    floatingChat.innerHTML = `
      <style>
        #floating-chat {
            position: fixed;
            bottom: 80px;
            right: 20px;
            width: 320px;
            max-height: 400px;
            background: #fff;
            border-radius: 12px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.2);
            display: flex;
            flex-direction: column;
            font-family: sans-serif;
            z-index: 9999;
        }
        #chat-box {
            flex: 1;
            overflow-y: auto;
            padding: 10px;
        }
        .chat-message {
            padding: 8px 12px;
            margin: 6px 0;
            border-radius: 10px;
            max-width: 80%;
            line-height: 1.4;
        }
        .chat-message.user {
            align-self: flex-end;
            background: #DCF8C6;
        }
        .chat-message.assistant {
            align-self: flex-start;
            background: #eee;
        }
        #chat-input {
            border: none;
            padding: 8px;
            font-size: 14px;
            border-top: 1px solid #ccc;
            width: 100%;
        }
        .audio-container {
            padding: 5px;
        }
        .voice-button {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #0b93f6;
            color: #fff;
            border: none;
            border-radius: 50%;
            width: 60px;
            height: 60px;
            font-size: 24px;
            cursor: pointer;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            z-index: 9999;
        }
        .voice-button.recording {
            background: red;
        }
        .autoplay-toggle {
            position: fixed;
            bottom: 100px;
            right: 90px;
            background: #fff;
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 13px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
            z-index: 9999;
        }
      </style>
      <div id="chat-box"></div>
      <input id="chat-input" type="text" placeholder="Напишіть повідомлення..." />
    `;
    document.body.appendChild(floatingChat);

    function appendMessage(text, isUser = false) {
        if (interactionMode !== "voice+chat") return;
        const msg = document.createElement("div");
        msg.className = "chat-message " + (isUser ? "user" : "assistant");
        msg.textContent = text;
        document.getElementById("chat-box").appendChild(msg);
        document.getElementById("chat-box").scrollTop = 999999;
    }

    function appendAudioPlayer(audioUrl, label) {
        const container = document.createElement("div");
        container.className = "audio-container";

        const labelEl = document.createElement("div");
        labelEl.textContent = label;

        const audio = document.createElement("audio");
        audio.controls = true;
        audio.src = audioUrl;

        container.appendChild(labelEl);
        container.appendChild(audio);

        document.getElementById("chat-box").appendChild(container);
        if (autoplay) audio.play().catch(() => {});
    }

    function sendRecording() {
        const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
        if (audioBlob.size < 1000) {
            alert("⚠️ Помилка: аудіо занадто коротке або порожнє. Спробуйте ще раз.");
            return;
        }

        const formData = new FormData();
        formData.append("audio", audioBlob, "recording.webm");

        const clientId = localStorage.getItem("client_id") || Math.random().toString(36).substring(2);
        localStorage.setItem("client_id", clientId);
        formData.append("client_id", clientId);

        appendMessage("🎤 Повідомлення відправлено", true);

        fetch(`${baseUrl}/process_audio`, {
            method: "POST",
            body: formData
        }).then(res => res.json()).then(data => {
            if (data.response) {
                appendMessage(data.response);
            } else {
                appendMessage("⚠️ Відповідь відсутня.");
            }
        }).catch(err => {
            console.error("❌ Помилка при відправці аудіо:", err);
            appendMessage("⚠️ Помилка з'єднання з сервером", false);
        });
    }

    function fallbackToChat() {
        interactionMode = "voice+chat";
        floatingChat.style.display = "flex";
        appendMessage("😔 Ваш браузер не підтримує запис голосу або мікрофон недоступний. Ви можете спілкуватися з асистентом у текстовому чаті.");
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

            floatingChat.style.display = "flex";
        }).catch(err => {
            console.error("🎤 Мікрофон недоступний:", err);
            fallbackToChat();
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
    recordButton.title = "Утримуйте для запису (до 30 сек)";
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
      🔊 Авто
    `;
    document.body.appendChild(autoplayToggle);
    document.getElementById("autoplay-check").addEventListener("change", e => {
        autoplay = e.target.checked;
    });

    document.getElementById("chat-input").addEventListener("keypress", e => {
        if (e.key === "Enter") {
            const text = e.target.value.trim();
            if (text) {
                appendMessage(text, true);
                fetch("/process_text", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ text, client_id: localStorage.getItem("client_id") })
                }).then(r => r.json()).then(data => {
                    appendMessage(data.answer || "🤖 Відповідь відсутня");
                }).catch(() => {
                    appendMessage("⚠️ Сервер недоступний");
                });
                e.target.value = "";
            }
        }
    });

    fetch("/static/widget_settings.json")
        .then(r => r.json())
        .then(cfg => interactionMode = cfg.interaction_mode || "voice+chat");
});
