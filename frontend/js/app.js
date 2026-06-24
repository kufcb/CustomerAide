// 后端接口（与前端同源，由 FastAPI 提供）
const API_BASE = "http://localhost:8888";
const API_URL = `${API_BASE}/stream_chat`;
const UPLOAD_URL = `${API_BASE}/upload`;

const messagesEl = document.getElementById("messages");
const inputEl = document.getElementById("input");
const sendBtn = document.getElementById("sendBtn");
const clearBtn = document.getElementById("clearBtn");
const uploadBtn = document.getElementById("uploadBtn");
const fileInput = document.getElementById("fileInput");

const WELCOME = "你好，我是智能客服助手，有什么可以帮你的吗？";

let isSending = false;
let isUploading = false;

// 页面进入即显示欢迎语
appendMessage("ai", WELCOME);

/* ---------- 消息渲染 ---------- */

// 追加一条消息，返回气泡 DOM（便于流式更新）
function appendMessage(role, text) {
    const row = document.createElement("div");
    row.className = `msg msg--${role}`;

    const avatar = document.createElement("div");
    avatar.className = "msg__avatar";
    avatar.textContent = role === "ai" ? "AI" : "我";

    const bubble = document.createElement("div");
    bubble.className = "msg__bubble";
    bubble.textContent = text;

    row.appendChild(avatar);
    row.appendChild(bubble);
    messagesEl.appendChild(row);
    scrollToBottom();
    return bubble;
}

// 显示"正在输入"的加载气泡
function appendLoading() {
    const row = document.createElement("div");
    row.className = "msg msg--ai";
    row.innerHTML = `
        <div class="msg__avatar">AI</div>
        <div class="msg__bubble">
            <span class="dots"><span></span><span></span><span></span></span>
        </div>`;
    messagesEl.appendChild(row);
    scrollToBottom();
    return row;
}

function scrollToBottom() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
}

// 居中系统提示（上传结果等）
function appendSystemMessage(text, isError = false) {
    const row = document.createElement("div");
    row.className = "msg msg--system";
    if (isError) row.classList.add("msg--system-error");

    const bubble = document.createElement("div");
    bubble.className = "msg__bubble";
    bubble.textContent = text;

    row.appendChild(bubble);
    messagesEl.appendChild(row);
    scrollToBottom();
}

/* ---------- 文件上传 ---------- */

async function uploadFile(file) {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("knowledge_base", "默认");

    const resp = await fetch(UPLOAD_URL, {
        method: "POST",
        body: formData,
    });

    const raw = await resp.text();
    let result = {};
    try {
        result = raw ? JSON.parse(raw) : {};
    } catch {
        if (!resp.ok) {
            throw new Error(raw || `上传失败：${resp.status}`);
        }
        throw new Error(`上传失败：${resp.status}`);
    }

    if (!resp.ok) {
        const detail = result.detail || result.message || `HTTP ${resp.status}`;
        throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
    if (result.code !== 200) {
        throw new Error(result.message || "上传失败");
    }
    return result;
}

async function handleFileSelected(e) {
    const file = e.target.files?.[0];
    fileInput.value = "";
    if (!file || isUploading) return;

    isUploading = true;
    uploadBtn.disabled = true;
    sendBtn.disabled = true;

    appendSystemMessage(`正在上传「${file.name}」…`);

    try {
        const result = await uploadFile(file);
        const sizeKb = ((result.data?.size || file.size) / 1024).toFixed(1);
        appendSystemMessage(`「${file.name}」上传成功（${sizeKb} KB），已加入知识库。`);
    } catch (err) {
        appendSystemMessage(`上传失败：${err.message}`, true);
    } finally {
        isUploading = false;
        uploadBtn.disabled = false;
        if (!isSending) sendBtn.disabled = false;
        inputEl.focus();
    }
}

/* ---------- 发送与流式接收 ---------- */

async function sendMessage() {
    const text = inputEl.value.trim();
    if (!text || isSending || isUploading) return;

    isSending = true;
    sendBtn.disabled = true;
    uploadBtn.disabled = true;

    // 渲染用户消息
    appendMessage("user", text);
    inputEl.value = "";
    autoResize();

    // 加载占位
    const loadingRow = appendLoading();

    try {
        const resp = await fetch(API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text }),
        });

        if (!resp.ok || !resp.body) {
            throw new Error(`请求失败：${resp.status}`);
        }

        // 移除加载占位，换成真正的 AI 气泡
        loadingRow.remove();
        const bubble = appendMessage("ai", "");
        bubble.classList.add("typing-cursor");

        const reader = resp.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let answer = "";

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            answer += decoder.decode(value, { stream: true });
            bubble.textContent = answer;
            scrollToBottom();
        }

        bubble.classList.remove("typing-cursor");
        if (!answer.trim()) {
            bubble.textContent = "（未收到回复内容）";
        }
    } catch (err) {
        loadingRow.remove();
        const bubble = appendMessage("ai", `出错了：${err.message}`);
        bubble.style.color = "#e74c3c";
    } finally {
        isSending = false;
        sendBtn.disabled = false;
        if (!isUploading) uploadBtn.disabled = false;
        inputEl.focus();
    }
}

/* ---------- 交互事件 ---------- */

sendBtn.addEventListener("click", sendMessage);

uploadBtn.addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", handleFileSelected);

inputEl.addEventListener("keydown", (e) => {
    // 回车发送，Shift + 回车换行
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// 输入框高度自适应
function autoResize() {
    inputEl.style.height = "auto";
    inputEl.style.height = Math.min(inputEl.scrollHeight, 140) + "px";
}
inputEl.addEventListener("input", autoResize);

// 清空对话
clearBtn.addEventListener("click", () => {
    messagesEl.innerHTML = "";
    appendMessage("ai", WELCOME);
});

inputEl.focus();
