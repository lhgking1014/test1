const timeElement = document.getElementById("clock-time");
const dateElement = document.getElementById("clock-date");
const timezoneElement = document.getElementById("clock-timezone");

function renderNow(now) {
    const locale = "ko-KR";

    timeElement.textContent = now.toLocaleTimeString(locale, {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit"
    });

    dateElement.textContent = now.toLocaleDateString(locale, {
        year: "numeric",
        month: "long",
        day: "numeric",
        weekday: "long"
    });

    timezoneElement.textContent = Intl.DateTimeFormat().resolvedOptions().timeZone || "";
}

function startClock() {
    // Render immediately so the user sees the current time without delay.
    renderNow(new Date());

    // Align the update interval to the next second boundary for smoother ticking.
    const delay = 1000 - (Date.now() % 1000);
    setTimeout(() => {
        renderNow(new Date());
        setInterval(() => renderNow(new Date()), 1000);
    }, delay);
}

startClock();
