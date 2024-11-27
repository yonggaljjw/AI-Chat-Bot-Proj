document.addEventListener("DOMContentLoaded", function () {
	// 채팅 관련 요소들
	const chatIcon = document.getElementById("chat-icon");
	const chatWindow = document.getElementById("chat-window");
	const closeChat = document.getElementById("close-chat");
	const chatForm = document.getElementById("chat-form");
	const messageInput = document.getElementById("message-input");
	const chatMessages = document.getElementById("chat-messages");
	const powerModeToggle = document.getElementById("power-mode-toggle");

	// 채팅 아이콘 클릭 이벤트
	chatIcon.addEventListener("click", function () {
		chatWindow.classList.toggle("hidden");
	});

	// 닫기 버튼 클릭 이벤트
	closeChat.addEventListener("click", function () {
		chatWindow.classList.add("hidden");
	});

	// 메시지 전송 이벤트
	chatForm.addEventListener("submit", async function (e) {
		e.preventDefault();
		const message = messageInput.value.trim();
		if (!message) return;

		// 사용자 메시지 표시
		appendMessage(message, true);
		messageInput.value = "";

		try {
			const response = await fetch("/chatbot/send/", {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
					"X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]")
						.value,
				},
				body: JSON.stringify({
					message: message,
					isPowerMode: powerModeToggle.checked,
				}),
			});

			if (!response.ok) throw new Error("Network response was not ok");

			const data = await response.json();
			appendMessage(data.response, false);
		} catch (error) {
			console.error("Error:", error);
			appendMessage("죄송합니다. 오류가 발생했습니다.", false);
		}
	});

	// 메시지 추가 함수
	function appendMessage(message, isUser) {
		const div = document.createElement("div");
		div.className = `flex ${isUser ? "justify-end" : "justify-start"} mb-4`;
		div.innerHTML = `
            <div class="max-w-[70%] ${
							isUser ? "bg-blue-500 text-white" : "bg-gray-200"
						} rounded-lg px-4 py-2">
                <p class="text-sm">${message}</p>
            </div>
        `;
		chatMessages.appendChild(div);
		chatMessages.scrollTop = chatMessages.scrollHeight;
	}
});
