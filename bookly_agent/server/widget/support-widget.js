(function () {
  const script = document.currentScript;
  const chatUrl = script?.dataset.chatUrl || "/api/support/chat";
  const resetUrl = chatUrl.replace(/\/chat$/, "/reset");
  const storageKey = "bookly_support_session_id";
  const WELCOME_MESSAGE =
    "Hi! I'm the Bookly support agent. I can check order status, start refunds, or answer policy questions.";

  function createSessionId() {
    return window.crypto?.randomUUID?.() || `sess-${Date.now()}`;
  }

  function getSessionId() {
    let sessionId = window.localStorage.getItem(storageKey);
    if (!sessionId) {
      sessionId = createSessionId();
      window.localStorage.setItem(storageKey, sessionId);
    }
    return sessionId;
  }

  function createMessage(text, role) {
    const node = document.createElement("div");
    node.className = `bookly-support-message is-${role}`;
    node.textContent = text;
    return node;
  }

  function mountWidget() {
    const root = document.createElement("div");
    root.className = "bookly-support-root";
    root.innerHTML = `
      <div class="bookly-support-panel" id="booklySupportPanel" aria-hidden="true">
        <div class="bookly-support-header">
          <h2>Bookly Support</h2>
          <button type="button" class="bookly-support-close" aria-label="Close chat">×</button>
        </div>
        <div class="bookly-support-messages" id="booklySupportMessages"></div>
        <div class="bookly-support-status" id="booklySupportStatus"></div>
        <div class="bookly-support-toolbar">
          <button type="button" class="bookly-support-reset" aria-label="Start over">Start over</button>
        </div>
        <form class="bookly-support-form" id="booklySupportForm">
          <input
            class="bookly-support-input"
            id="booklySupportInput"
            type="text"
            placeholder="Ask about orders, returns, shipping..."
            autocomplete="off"
            required
          />
          <button class="bookly-support-send" type="submit">Send</button>
        </form>
      </div>
      <button type="button" class="bookly-support-launcher" aria-expanded="false" aria-controls="booklySupportPanel">
        Help
      </button>
    `;

    document.body.appendChild(root);

    const panel = root.querySelector("#booklySupportPanel");
    const launcher = root.querySelector(".bookly-support-launcher");
    const resetButton = root.querySelector(".bookly-support-reset");
    const closeButton = root.querySelector(".bookly-support-close");
    const messages = root.querySelector("#booklySupportMessages");
    const status = root.querySelector("#booklySupportStatus");
    const form = root.querySelector("#booklySupportForm");
    const input = root.querySelector("#booklySupportInput");
    const sendButton = root.querySelector(".bookly-support-send");

    let opened = false;

    function setOpen(isOpen) {
      opened = isOpen;
      panel.classList.toggle("is-open", isOpen);
      panel.setAttribute("aria-hidden", isOpen ? "false" : "true");
      launcher.setAttribute("aria-expanded", isOpen ? "true" : "false");
      if (isOpen) {
        input.focus();
        if (!messages.childElementCount) {
          appendAgentMessage(WELCOME_MESSAGE);
        }
      }
    }

    function appendAgentMessage(text) {
      messages.appendChild(createMessage(text, "agent"));
      messages.scrollTop = messages.scrollHeight;
    }

    function appendUserMessage(text) {
      messages.appendChild(createMessage(text, "user"));
      messages.scrollTop = messages.scrollHeight;
    }

    async function sendMessage(text) {
      sendButton.disabled = true;
      status.textContent = "Thinking...";

      try {
        const response = await fetch(chatUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "same-origin",
          body: JSON.stringify({
            session_id: getSessionId(),
            message: text,
          }),
        });

        const payload = await response.json();
        if (!response.ok) {
          throw new Error(payload.error || "Request failed");
        }

        appendAgentMessage(payload.reply || "Sorry, I couldn't process that.");
        status.textContent = "";
      } catch (error) {
        status.textContent = "";
        appendAgentMessage("Something went wrong. Please try again in a moment.");
        console.error("Bookly support widget error:", error);
      } finally {
        sendButton.disabled = false;
        input.focus();
      }
    }

    async function startOver() {
      const oldSessionId = getSessionId();
      resetButton.disabled = true;
      sendButton.disabled = true;
      status.textContent = "Starting over...";

      try {
        await fetch(resetUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "same-origin",
          body: JSON.stringify({ session_id: oldSessionId }),
        });
      } catch (error) {
        console.error("Bookly support reset error:", error);
      }

      window.localStorage.setItem(storageKey, createSessionId());
      messages.innerHTML = "";
      status.textContent = "";
      appendAgentMessage(WELCOME_MESSAGE);
      resetButton.disabled = false;
      sendButton.disabled = false;
      input.focus();
    }

    launcher.addEventListener("click", () => setOpen(!opened));
    resetButton.addEventListener("click", startOver);
    closeButton.addEventListener("click", () => setOpen(false));

    form.addEventListener("submit", (event) => {
      event.preventDefault();
      const text = input.value.trim();
      if (!text) {
        return;
      }
      input.value = "";
      appendUserMessage(text);
      sendMessage(text);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mountWidget);
  } else {
    mountWidget();
  }
})();
