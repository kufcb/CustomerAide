// 后端流式聊天接口（与前端同源，由 FastAPI 提供）
const API_URL = "http://localhost:8888/stream_chat";

const messagesEl = document.getElementById("messages");
const inputEl = document.getElementById("input");
const sendBtn = document.getElementById("sendBtn");
const clearBtn = document.getElementById("clearBtn");

const WELCOME = "你好，我是智能客服助手，有什么可以帮你的吗？";

let isSending = false;

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

/* ---------- 发送与流式接收 ---------- */

async function sendMessage() {
    const text = inputEl.value.trim();
    if (!text || isSending) return;

    isSending = true;
    sendBtn.disabled = true;

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
        inputEl.focus();
    }
}

/* ---------- 交互事件 ---------- */

sendBtn.addEventListener("click", sendMessage);

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
