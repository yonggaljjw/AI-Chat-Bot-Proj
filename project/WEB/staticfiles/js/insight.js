// 인사이트 아이콘 SVG 정의
const INSIGHT_ICON = `
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"></circle>
        <path d="M12 16v-4"></path>
        <path d="M12 8h.01"></path>
    </svg>
`;

// 인사이트 관련 함수들
const insightManager = {
	initialize: function () {
		const dashboardContents = [
			document.getElementById("dashboard-content-one"),
			document.getElementById("dashboard-content-two"),
			document.getElementById("dashboard-content-three"),
		];

		dashboardContents.forEach((content) => {
			if (!content) return;

			const chartContainers = content.querySelectorAll(".shadow-md");
			chartContainers.forEach((container) => {
				const jsonElement = container.querySelector('[id$="_json"]');
				const titleElement = container.querySelector("h3");
				const chartId =
					(jsonElement && jsonElement.id) ||
					(titleElement && titleElement.textContent.trim()) ||
					"unknown";

				if (container.querySelector(".insight-tooltip")) return;

				container.style.position = "relative";

				const tooltipDiv = document.createElement("div");
				tooltipDiv.className = "insight-tooltip";
				tooltipDiv.innerHTML = `
                    <div class="insight-icon">${INSIGHT_ICON}</div>
                    <div class="insight-content" id="insight-content-${chartId}">
                        <div class="animate-pulse">인사이트 로딩중...</div>
                    </div>
                `;

				container.appendChild(tooltipDiv);
				this.loadInsight(chartId, tooltipDiv.querySelector(".insight-content"));
			});
		});
	},

	loadInsight: function (chartId, contentElement) {
		if (!chartId || !contentElement) {
			console.error("Invalid chartId or contentElement");
			return;
		}

		const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]");
		if (!csrfToken) {
			console.error("CSRF token not found");
			contentElement.innerHTML = "인사이트를 불러올 수 없습니다.";
			return;
		}

		fetch(`/chatbot/send/?chartId=${encodeURIComponent(chartId)}`, {
			method: "GET",
			headers: {
				"X-CSRFToken": csrfToken.value,
				"Content-Type": "application/json",
			},
		})
			.then((response) => {
				if (!response.ok) {
					throw new Error(`HTTP error! status: ${response.status}`);
				}
				return response.json();
			})
			.then((data) => {
				if (data.status === "success" && data.insight) {
					contentElement.innerHTML = data.insight;
				} else {
					throw new Error(data.message || "인사이트 데이터가 없습니다.");
				}
			})
			.catch((error) => {
				console.error("Error loading insight:", error);
				contentElement.innerHTML = "현재 서비스 준비중입니다.";
			});
	},
};

// DOM이 로드되면 insightManager 초기화
document.addEventListener("DOMContentLoaded", function () {
	try {
		insightManager.initialize();
	} catch (error) {
		console.error("Error initializing insightManager:", error);
	}
});
