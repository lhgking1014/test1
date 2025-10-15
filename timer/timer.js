const dom = {
    ampm: document.getElementById("clock-ampm"),
    digits: document.getElementById("clock-digits"),
    date: document.getElementById("clock-date"),
    ms: document.getElementById("clock-ms"),
    timezone: document.getElementById("clock-timezone"),
    selected: document.getElementById("clock-selected"),
    languageToggle: document.getElementById("language-toggle"),
    languageLabel: document.getElementById("language-label"),
    mapHint: document.getElementById("map-hint"),
    mapCities: document.getElementById("map-cities"),
    mapTerminator: document.getElementById("map-terminator")
};

const languages = [
    { code: "ko-KR" },
    { code: "en-US" },
    { code: "ja-JP" }
];

const translations = {
    "ko-KR": {
        languageLabel: "한국어",
        languageToggle: "언어 변경",
        mapHint: "도시를 클릭해 시간을 변경하세요.",
        selected: (city) => `${city} 현재 시간`,
        timezone: (city, zone, offset) => `${city} · ${zone} (${offset})`,
        title: "세계 타임존 타이머",
        citiesListLabel: "주요 도시 목록"
    },
    "en-US": {
        languageLabel: "English",
        languageToggle: "Change language",
        mapHint: "Click a city to jump to that timezone.",
        selected: (city) => `${city} local time`,
        timezone: (city, zone, offset) => `${city} · ${zone} (${offset})`,
        title: "World Time Impact Clock",
        citiesListLabel: "Major cities"
    },
    "ja-JP": {
        languageLabel: "日本語",
        languageToggle: "言語を変更",
        mapHint: "都市をクリックしてタイムゾーンを切り替えます。",
        selected: (city) => `${city}の現在時刻`,
        timezone: (city, zone, offset) => `${city}・${zone}（${offset}）`,
        title: "世界タイムゾーンクロック",
        citiesListLabel: "主要都市"
    }
};

const cities = [
    {
        id: "seoul",
        abbr: "SEL",
        timeZone: "Asia/Seoul",
        coordinates: { x: 50, y: 44 },
        names: {
            "ko-KR": "서울",
            "en-US": "Seoul",
            "ja-JP": "ソウル"
        }
    },
    {
        id: "tokyo",
        abbr: "TYO",
        timeZone: "Asia/Tokyo",
        coordinates: { x: 56, y: 45 },
        names: {
            "ko-KR": "도쿄",
            "en-US": "Tokyo",
            "ja-JP": "東京"
        }
    },
    {
        id: "sydney",
        abbr: "SYD",
        timeZone: "Australia/Sydney",
        coordinates: { x: 64, y: 78 },
        names: {
            "ko-KR": "시드니",
            "en-US": "Sydney",
            "ja-JP": "シドニー"
        }
    },
    {
        id: "dubai",
        abbr: "DXB",
        timeZone: "Asia/Dubai",
        coordinates: { x: 38, y: 56 },
        names: {
            "ko-KR": "두바이",
            "en-US": "Dubai",
            "ja-JP": "ドバイ"
        }
    },
    {
        id: "mumbai",
        abbr: "BOM",
        timeZone: "Asia/Kolkata",
        coordinates: { x: 41, y: 53 },
        names: {
            "ko-KR": "뭄바이",
            "en-US": "Mumbai",
            "ja-JP": "ムンバイ"
        }
    },
    {
        id: "london",
        abbr: "LON",
        timeZone: "Europe/London",
        coordinates: { x: 22, y: 38 },
        names: {
            "ko-KR": "런던",
            "en-US": "London",
            "ja-JP": "ロンドン"
        }
    },
    {
        id: "paris",
        abbr: "PAR",
        timeZone: "Europe/Paris",
        coordinates: { x: 24, y: 41 },
        names: {
            "ko-KR": "파리",
            "en-US": "Paris",
            "ja-JP": "パリ"
        }
    },
    {
        id: "newyork",
        abbr: "NYC",
        timeZone: "America/New_York",
        coordinates: { x: 6, y: 45 },
        names: {
            "ko-KR": "뉴욕",
            "en-US": "New York",
            "ja-JP": "ニューヨーク"
        }
    },
    {
        id: "losangeles",
        abbr: "LAX",
        timeZone: "America/Los_Angeles",
        coordinates: { x: 2, y: 50 },
        names: {
            "ko-KR": "로스앤젤레스",
            "en-US": "Los Angeles",
            "ja-JP": "ロサンゼルス"
        }
    },
    {
        id: "santiago",
        abbr: "SCL",
        timeZone: "America/Santiago",
        coordinates: { x: 8, y: 78 },
        names: {
            "ko-KR": "산티아고",
            "en-US": "Santiago",
            "ja-JP": "サンティアゴ"
        }
    }
];

let currentLocaleIndex = 0;
let currentCityId = "seoul";
let previousSecond = null;
let previousMinute = null;

const cityButtons = new Map();

function getCity(cityId) {
    return cities.find((city) => city.id === cityId);
}

function getCityName(city, locale) {
    return city.names[locale] || city.names["en-US"];
}

function buildCityButtons() {
    const locale = languages[currentLocaleIndex].code;
    cities.forEach((city) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "city-marker";
        button.id = `city-${city.id}`;
        button.dataset.cityId = city.id;
        button.dataset.timeZone = city.timeZone;
        button.style.setProperty("--x", String(city.coordinates.x));
        button.style.setProperty("--y", String(city.coordinates.y));
        button.textContent = city.abbr;
        button.setAttribute("role", "option");
        button.setAttribute("aria-selected", "false");
        const cityName = getCityName(city, locale);
        button.setAttribute("title", cityName);
        button.setAttribute("aria-label", cityName);
        button.addEventListener("click", () => selectCity(city.id));
        dom.mapCities.appendChild(button);
        cityButtons.set(city.id, button);
    });
}

function selectCity(cityId) {
    const city = getCity(cityId);
    if (!city) {
        return;
    }

    currentCityId = cityId;
    cityButtons.forEach((button, id) => {
        const isActive = id === cityId;
        button.classList.toggle("city-marker--active", isActive);
        button.setAttribute("aria-selected", String(isActive));
        if (isActive) {
            dom.mapCities.setAttribute("aria-activedescendant", button.id);
        }
    });

    renderClock();
}

function getOffsetMinutes(date, timeZone) {
    const formatter = new Intl.DateTimeFormat("en-US", {
        timeZone,
        calendar: "iso8601",
        numberingSystem: "latn",
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: false
    });

    const parts = formatter.formatToParts(date);
    const values = {};
    for (const part of parts) {
        if (part.type !== "literal") {
            values[part.type] = part.value;
        }
    }

    const utcEquivalent = Date.UTC(
        Number(values.year),
        Number(values.month) - 1,
        Number(values.day),
        Number(values.hour),
        Number(values.minute),
        Number(values.second)
    );

    return (utcEquivalent - date.getTime()) / 60000;
}

function formatOffsetLabel(offsetMinutes) {
    const totalMinutes = Math.round(offsetMinutes);
    const sign = totalMinutes >= 0 ? "+" : "-";
    const absolute = Math.abs(totalMinutes);
    const hours = String(Math.floor(absolute / 60)).padStart(2, "0");
    const minutes = String(absolute % 60).padStart(2, "0");
    return `GMT${sign}${hours}:${minutes}`;
}

function renderClock() {
    const now = new Date();
    const locale = languages[currentLocaleIndex].code;
    const copy = translations[locale] || translations["en-US"];
    const city = getCity(currentCityId) || cities[0];
    const timeZone = city.timeZone;

    const timeFormatter = new Intl.DateTimeFormat(locale, {
        timeZone,
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: true,
        numberingSystem: "latn"
    });

    const dateFormatter = new Intl.DateTimeFormat(locale, {
        timeZone,
        year: "numeric",
        month: "long",
        day: "numeric",
        weekday: "long"
    });

    const parts = timeFormatter.formatToParts(now);
    const partLookup = Object.fromEntries(
        parts
            .filter((part) => part.type !== "literal")
            .map((part) => [part.type, part.value])
    );

    const ampm = partLookup.dayPeriod || "";
    const hour = partLookup.hour || "--";
    const minute = partLookup.minute || "--";
    const second = partLookup.second || "--";

    const numericMinute = Number(minute);
    const numericSecond = Number(second);

    dom.ampm.textContent = locale === "en-US" ? ampm.toUpperCase() : ampm;
    dom.digits.textContent = `${hour}:${minute}:${second}`;
    dom.date.textContent = dateFormatter.format(now);

    if (previousMinute !== null && Number.isFinite(numericMinute) && numericMinute !== previousMinute) {
        dom.digits.classList.remove("tick-impact");
        dom.digits.classList.add("minute-impact");
    } else if (previousSecond !== null && Number.isFinite(numericSecond) && numericSecond !== previousSecond) {
        dom.digits.classList.remove("minute-impact");
        dom.digits.classList.add("tick-impact");
    }

    previousMinute = Number.isFinite(numericMinute) ? numericMinute : previousMinute;
    previousSecond = Number.isFinite(numericSecond) ? numericSecond : previousSecond;

    const offsetLabel = formatOffsetLabel(getOffsetMinutes(now, timeZone));
    const cityName = getCityName(city, locale);
    dom.timezone.textContent = copy.timezone(cityName, timeZone, offsetLabel);
    dom.selected.textContent = copy.selected(cityName);

    updateMapLighting(now);
    updateCityDayStates(now);
}

function updateMapLighting(now) {
    if (!dom.mapTerminator) {
        return;
    }
    const minutesUtc = now.getUTCHours() * 60 + now.getUTCMinutes();
    const rotation = (minutesUtc / 1440) * 360 - 90;
    dom.mapTerminator.style.transform = `rotate(${rotation}deg)`;
}

function updateCityDayStates(now) {
    const locale = languages[currentLocaleIndex].code;
    cities.forEach((city) => {
        const button = cityButtons.get(city.id);
        if (!button) {
            return;
        }
        const formatter = new Intl.DateTimeFormat("en-US", {
            timeZone: city.timeZone,
            hour12: false,
            hour: "2-digit",
            numberingSystem: "latn"
        });
        const hour = Number(formatter.format(now));
        const isNight = Number.isFinite(hour) ? hour < 6 || hour >= 18 : false;
        button.classList.toggle("city-marker--night", isNight);

        const name = getCityName(city, locale);
        button.setAttribute("title", name);
        button.setAttribute("aria-label", name);
    });
}

dom.digits.addEventListener("animationend", () => {
    dom.digits.classList.remove("tick-impact");
    dom.digits.classList.remove("minute-impact");
});

function applyLanguage() {
    const locale = languages[currentLocaleIndex].code;
    const copy = translations[locale] || translations["en-US"];

    document.documentElement.lang = locale;
    document.title = copy.title;
    dom.languageLabel.textContent = copy.languageLabel;
    dom.languageToggle.setAttribute("aria-label", copy.languageToggle);
    dom.mapHint.textContent = copy.mapHint;
    dom.mapCities.setAttribute("aria-label", copy.citiesListLabel);

    renderClock();
}

dom.languageToggle.addEventListener("click", () => {
    currentLocaleIndex = (currentLocaleIndex + 1) % languages.length;
    applyLanguage();
    dom.languageToggle.setAttribute("aria-expanded", "false");
});

function startTicker() {
    renderClock();
    const delay = 1000 - (Date.now() % 1000);
    setTimeout(() => {
        renderClock();
        setInterval(renderClock, 1000);
    }, delay);
}

function updateMilliseconds() {
    const now = new Date();
    dom.ms.textContent = now.getMilliseconds().toString().padStart(3, "0");
    requestAnimationFrame(updateMilliseconds);
}

buildCityButtons();
applyLanguage();
selectCity(currentCityId);
startTicker();
updateMilliseconds();
