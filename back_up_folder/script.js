const API_URL = "https://steal-the-egg-web.onrender.com";

const tg = window.Telegram?.WebApp;

const state = {
    user: null,
    data: null,
    eggTab: "shop"
};

const $ = id => document.getElementById(id);

const esc = s => String(s ?? "").replace(
    /[&<>"']/g,
    c => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;"
    }[c])
);


/* =========================
   API
========================= */

function headers() {
    return {
        "Content-Type": "application/json",
        "X-Telegram-Init-Data": tg?.initData || ""
    };
}


async function api(url, options = {}) {

    const r = await fetch(`${API_URL}${url}`, {
        ...options,

        headers: {
            ...headers(),
            ...(options.headers || {})
        }
    });


    const d = await r.json().catch(() => ({
        ok: false,
        error: "Ошибка сервера"
    }));


    if (!r.ok || d.ok === false) {
        throw Error(d.error || "Ошибка");
    }


    return d;
}


/* =========================
   TOAST
========================= */

function toast(t) {

    const e = $("toast");

    if (!e) return;


    e.textContent = t;

    e.classList.add("show");


    clearTimeout(window.tt);


    window.tt = setTimeout(() => {
        e.classList.remove("show");
    }, 2200);
}


/* =========================
   НАВИГАЦИЯ
========================= */

function showPage(page) {

    document
        .querySelectorAll(".page")
        .forEach(x => {
            x.classList.toggle(
                "active",
                x.id === page
            );
        });


    document
        .querySelectorAll("[data-page]")
        .forEach(x => {
            x.classList.toggle(
                "active",
                x.dataset.page === page
            );
        });


    window.scrollTo(0, 0);


    if (page === "eggs") {
        loadEggs();
    }
}


/* =========================
   DATA
========================= */

function setData(d) {

    state.data = d;


    /* =========================
       БАЛАНСЫ
    ========================== */

    if ($("tapCoins")) {
        $("tapCoins").textContent =
            Number(d.tap_coins || 0).toLocaleString();
    }


    if ($("eggCoins")) {
        $("eggCoins").textContent =
            Number(d.egg_coins || 0).toLocaleString();
    }


    /* =========================
       СЕРИЯ
    ========================== */

    if ($("streak")) {
        $("streak").textContent =
            Number(d.streak || 0);
    }


    /* =========================
       LEVEL / XP
    ========================== */

    if ($("level")) {
        $("level").textContent =
            Number(d.level || 1);
    }


    const xp = Number(d.xp || 0);

    const xpRequired =
        Number(
            d.xp_required ||
            ((Number(d.level || 1)) * 100)
        );


    if ($("xpText")) {
        $("xpText").textContent =
            `${xp}/${xpRequired} XP`;
    }


    if ($("xpBar")) {

        let progress = 0;

        if (xpRequired > 0) {
            progress =
                Math.min(
                    100,
                    (xp / xpRequired) * 100
                );
        }


        $("xpBar").style.width =
            progress + "%";
    }


    /* =========================
       PROFILE
    ========================== */

    const firstName =
        state.user?.first_name || "Игрок";


    if ($("profileName")) {
        $("profileName").textContent =
            firstName;
    }


    if ($("profileId")) {
        $("profileId").textContent =
            `ID: ${state.user?.id || "—"}`;
    }


    if ($("profileTap")) {
        $("profileTap").textContent =
            Number(d.tap_coins || 0).toLocaleString();
    }


    if ($("profileEgg")) {
        $("profileEgg").textContent =
            Number(d.egg_coins || 0).toLocaleString();
    }


    /* =========================
       ЯЙЦА
    ========================== */

    let eggsTotal =
        Number(d.eggs_total || 0);


    if (
        !eggsTotal &&
        d.eggs &&
        typeof d.eggs === "object"
    ) {

        eggsTotal =
            Object.values(d.eggs)
                .reduce(
                    (sum, value) =>
                        sum + Number(value || 0),
                    0
                );
    }


    if ($("profileEggs")) {
        $("profileEggs").textContent =
            eggsTotal;
    }


    /* =========================
       ДОСТИЖЕНИЯ
    ========================== */

    if ($("profileAch")) {

        $("profileAch").textContent =
            Array.isArray(d.achievements)
                ? d.achievements.length
                : Number(d.achievements_count || 0);
    }


    /* =========================
       AVATAR
    ========================== */

    if ($("avatarButton")) {

        $("avatarButton").textContent =
            d.avatar || "🥚";
    }


    if ($("profileAvatar")) {

        $("profileAvatar").textContent =
            d.avatar || "🥚";
    }
}


/* =========================
   INIT
========================= */

async function init() {

    if (tg) {

        tg.ready();

        tg.expand();
    }


    try {

        const r = await api(
            "/api/init",
            {
                method: "POST",
                body: "{}"
            }
        );


        state.user = r.user;


        setData(r.data);


        if ($("username")) {

            $("username").textContent =
                state.user.username
                    ? "@" + state.user.username
                    : state.user.first_name || "Игрок";
        }


        if ($("app")) {
            $("app").classList.remove("hidden");
        }


        if (r.login?.claimed) {

            toast(
                `🔥 Серия ${r.login.streak} дней · +${r.login.reward} Egg Coins`
            );
        }


        (r.new_achievements || [])
            .forEach(a => {

                setTimeout(() => {

                    toast(
                        `🏆 ${a.name} · +${a.reward} Egg Coins`
                    );

                }, 700);
            });


    } catch (e) {

        if ($("app")) {
            $("app").classList.remove("hidden");
        }


        if ($("username")) {

            $("username").textContent =
                "Открой приложение через Telegram";
        }


        toast(e.message);
    }
}


/* =========================
   НАВИГАЦИЯ
========================= */

document.addEventListener("click", e => {

    const p =
        e.target.closest("[data-page]");


    if (p) {

        showPage(
            p.dataset.page
        );
    }
});


/* =========================
   ТАПАЛКА
========================= */

if ($("eggTap")) {

    $("eggTap").onclick = async e => {

        const b = e.currentTarget;

        const r =
            b.getBoundingClientRect();


        const f =
            document.createElement("div");


        f.className = "floater";

        f.textContent = "+1";


        f.style.left =
            (
                r.left +
                r.width / 2 -
                10
            ) + "px";


        f.style.top =
            (r.top + 40) + "px";


        if ($("tapFloaters")) {
            $("tapFloaters").appendChild(f);
        }


        setTimeout(() => {
            f.remove();
        }, 800);


        if (tg?.HapticFeedback) {

            tg.HapticFeedback
                .impactOccurred("light");
        }


        try {

            const r = await api(
                "/api/tap",
                {
                    method: "POST",

                    body: JSON.stringify({
                        amount: 1
                    })
                }
            );


            setData(r.data);


            (r.new_achievements || [])
                .forEach(a => {

                    toast(
                        `🏆 ${a.name} · +${a.reward}`
                    );
                });


        } catch (e) {

            toast(e.message);
        }
    };
}


/* =========================
   ОБМЕН TAP COINS
========================= */

if ($("exchangeBtn")) {

    $("exchangeBtn").onclick = async () => {

        if (
            !state.data ||
            Number(state.data.tap_coins || 0) < 1000
        ) {

            toast(
                "Нужно минимум 1000 Tap Coins"
            );

            return;
        }


        try {

            const r = await api(
                "/api/exchange",
                {
                    method: "POST",
                    body: "{}"
                }
            );


            setData(r.data);


            toast(
                `🥚 +${r.received} Egg Coins`
            );


        } catch (e) {

            toast(e.message);
        }
    };
}


/* =========================
   УГАДАЙ ЧИСЛО
========================= */

if ($("guessBtn")) {

    $("guessBtn").onclick = async () => {

        try {

            await api(
                "/api/game/guess/start",
                {
                    method: "POST",
                    body: "{}"
                }
            );


            $("gameArea").innerHTML = `

                <h3>
                    🔢 Угадай число
                </h3>

                <p>
                    Число от 1 до 20 · 10 попыток
                </p>

                <input
                    id="guessInput"
                    class="input"
                    type="number"
                    min="1"
                    max="20"
                    placeholder="Твоё число"
                >

                <button
                    id="guessSend"
                    class="primary"
                    type="button"
                >
                    Ответить
                </button>

                <p id="guessInfo"></p>
            `;


            $("guessSend").onclick =
                async () => {

                    const input =
                        $("guessInput");


                    const guess =
                        Number(input.value);


                    if (
                        !Number.isInteger(guess) ||
                        guess < 1 ||
                        guess > 20
                    ) {

                        toast(
                            "Введи число от 1 до 20"
                        );

                        return;
                    }


                    try {

                        const r =
                            await api(
                                "/api/game/guess/answer",
                                {
                                    method: "POST",

                                    body:
                                        JSON.stringify({
                                            guess
                                        })
                                }
                            );


                        if (
                            r.result ===
                            "continue"
                        ) {

                            $("guessInfo")
                                .textContent =
                                `❌ ${r.hint} · ${r.attempts}/10`;

                            input.value = "";

                            input.focus();

                            return;
                        }


                        setData(r.data);


                        $("gameArea").innerHTML = `

                            <h3>
                                ${
                                    r.result === "win"
                                        ? "🎉 Победа!"
                                        : "❌ Игра окончена"
                                }
                            </h3>

                            <p>
                                Загаданное число:
                                <b>${r.number}</b>
                            </p>

                            <p>
                                Награда:
                                +${r.reward} Egg Coins
                            </p>

                            <button
                                id="guessAgain"
                                class="primary"
                                type="button"
                            >
                                🔄 Играть ещё
                            </button>
                        `;


                        $("guessAgain").onclick =
                            () => $("guessBtn").click();


                    } catch (e) {

                        toast(e.message);
                    }
                };


        } catch (e) {

            toast(e.message);
        }
    };
}


/* =========================
   МАТЕМАТИКА
========================= */

async function startMathGame() {

    try {

        const r =
            await api(
                "/api/game/math/start",
                {
                    method: "POST",
                    body: "{}"
                }
            );


        renderMathQuestion(
            r.question
        );


    } catch (e) {

        toast(e.message);
    }
}


function renderMathQuestion(question) {

    $("gameArea").innerHTML = `

        <h3>
            🧠 Математика
        </h3>

        <div class="boss-hp">
            ${esc(question)}
        </div>

        <input
            id="mathInput"
            class="input"
            type="number"
            placeholder="Ответ"
        >

        <button
            id="mathSend"
            class="primary"
            type="button"
        >
            Проверить
        </button>

        <p id="mathInfo"></p>
    `;


    $("mathSend").onclick =
        async () => {

            const value =
                $("mathInput").value;


            if (value === "") {

                toast(
                    "Введи ответ"
                );

                return;
            }


            const answer =
                Number(value);


            try {

                const x =
                    await api(
                        "/api/game/math/answer",
                        {
                            method: "POST",

                            body:
                                JSON.stringify({
                                    answer
                                })
                        }
                    );


                setData(x.data);


                /*
                 * ПРАВИЛЬНЫЙ ОТВЕТ
                 */

                if (x.result === "win") {

                    $("gameArea").innerHTML = `

                        <h3>
                            🎉 Правильно!
                        </h3>

                        <p>
                            Ответ:
                            <b>${x.correct}</b>
                        </p>

                        <p>
                            Награда:
                            +${x.reward} Egg Coins
                        </p>

                        <button
                            id="mathNext"
                            class="primary"
                            type="button"
                        >
                            ➡️ Следующий пример
                        </button>
                    `;


                    $("mathNext").onclick =
                        startMathGame;


                    return;
                }


                /*
                 * НЕПРАВИЛЬНЫЙ ОТВЕТ
                 */

                $("gameArea").innerHTML = `

                    <h3>
                        ❌ Неправильно
                    </h3>

                    <p>
                        Правильный ответ:
                        <b>${x.correct}</b>
                    </p>

                    <p>
                        Новый пример:
                    </p>

                    <div class="boss-hp">
                        ${esc(
                            x.question ||
                            "Новый пример"
                        )}
                    </div>

                    <input
                        id="mathInput"
                        class="input"
                        type="number"
                        placeholder="Ответ"
                    >

                    <button
                        id="mathSend"
                        class="primary"
                        type="button"
                    >
                        Проверить
                    </button>
                `;


                $("mathSend").onclick =
                    async () => {

                        const newValue =
                            $("mathInput").value;


                        if (newValue === "") {

                            toast(
                                "Введи ответ"
                            );

                            return;
                        }


                        try {

                            const result =
                                await api(
                                    "/api/game/math/answer",
                                    {
                                        method: "POST",

                                        body:
                                            JSON.stringify({
                                                answer:
                                                    Number(
                                                        newValue
                                                    )
                                            })
                                    }
                                );


                            setData(result.data);


                            if (
                                result.result ===
                                "win"
                            ) {

                                $("gameArea").innerHTML = `

                                    <h3>
                                        🎉 Правильно!
                                    </h3>

                                    <p>
                                        Награда:
                                        +${result.reward}
                                        Egg Coins
                                    </p>

                                    <button
                                        id="mathNext"
                                        class="primary"
                                        type="button"
                                    >
                                        ➡️ Следующий пример
                                    </button>
                                `;


                                $("mathNext").onclick =
                                    startMathGame;


                            } else {

                                renderMathQuestion(
                                    result.question
                                );

                                toast(
                                    `❌ Неправильно. Правильный ответ: ${result.correct}`
                                );
                            }

                        } catch (e) {

                            toast(e.message);
                        }
                    };


            } catch (e) {

                toast(e.message);
            }
        };
}


if ($("mathBtn")) {

    $("mathBtn").onclick =
        startMathGame;
}


/* =========================
   КРЕСТИКИ-НОЛИКИ
========================= */

function renderTic(board) {

    /*
     * Всегда создаём ровно 9 клеток.
     * Если сервер прислал меньше 9,
     * недостающие клетки будут пустыми.
     */

    const safeBoard =
        Array(9).fill("");


    if (Array.isArray(board)) {

        for (
            let i = 0;
            i < Math.min(board.length, 9);
            i++
        ) {

            safeBoard[i] =
                board[i] ?? "";
        }
    }


    $("gameArea").innerHTML = `

        <h3>
            ❌⭕ Крестики-нолики
        </h3>

        <div class="tic">

            ${safeBoard.map((v, i) => `

                <button
                    data-cell="${i}"
                    type="button"
                    ${v !== "" ? "disabled" : ""}
                >
                    ${
                        v === ""
                            ? "⬜"
                            : esc(v)
                    }
                </button>

            `).join("")}

        </div>

        <p>
            Ты играешь за ❌
        </p>
    `;


    document
        .querySelectorAll("[data-cell]")
        .forEach(button => {

            button.onclick =
                async () => {

                    const index =
                        Number(
                            button.dataset.cell
                        );


                    if (
                        !Number.isInteger(index) ||
                        index < 0 ||
                        index > 8
                    ) {

                        return;
                    }


                    try {

                        const r =
                            await api(
                                "/api/game/tic/move",
                                {
                                    method: "POST",

                                    body:
                                        JSON.stringify({
                                            index
                                        })
                                }
                            );


                        if (
                            r.result ===
                            "continue"
                        ) {

                            renderTic(
                                r.board
                            );

                            return;
                        }


                        setData(
                            r.data
                        );


                        let title =
                            "❌ Поражение";


                        if (
                            r.result ===
                            "win"
                        ) {

                            title =
                                "🎉 Победа!";

                        } else if (
                            r.result ===
                            "draw"
                        ) {

                            title =
                                "🤝 Ничья!";
                        }


                        $("gameArea").innerHTML = `

                            <h3>
                                ${title}
                            </h3>

                            <p>
                                Награда:
                                +${r.reward || 0}
                                Egg Coins
                            </p>

                            <button
                                id="ticAgain"
                                class="primary"
                                type="button"
                            >
                                🔄 Играть ещё
                            </button>
                        `;


                        $("ticAgain").onclick =
                            () => $("ticBtn").click();


                    } catch (e) {

                        toast(e.message);
                    }
                };
        });
}


if ($("ticBtn")) {

    $("ticBtn").onclick =
        async () => {

            try {

                const r =
                    await api(
                        "/api/game/tic/start",
                        {
                            method: "POST",
                            body: "{}"
                        }
                    );


                renderTic(
                    r.board
                );


            } catch (e) {

                toast(e.message);
            }
        };
}


/* =========================
   ЯЙЦА
========================= */

document
    .querySelectorAll(".tab")
    .forEach(t => {

        t.onclick = () => {

            document
                .querySelectorAll(".tab")
                .forEach(x => {
                    x.classList.remove(
                        "active"
                    );
                });


            t.classList.add("active");


            state.eggTab =
                t.dataset.tab;


            loadEggs();
        };
    });


if ($("refreshEggs")) {

    $("refreshEggs").onclick =
        loadEggs;
}


async function loadEggs() {

    try {

        const r =
            await api(
                "/api/eggs"
            );


        /*
         * МАГАЗИН
         */

        if (
            state.eggTab ===
            "shop"
        ) {

            const shop =
                r.shop || {};


            const entries =
                Array.isArray(shop)
                    ? shop.map(
                        e => [
                            String(e.id),
                            e
                        ]
                    )
                    : Object.entries(
                        shop
                    );


            $("eggContent").innerHTML =
                entries
                    .map(([id, e]) => `

                        <div class="egg-item">

                            <div class="egg-top">

                                <div>

                                    <div class="egg-name">

                                        ${
                                            esc(
                                                e.emoji ||
                                                "🥚"
                                            )
                                        }

                                        ${esc(
                                            e.name
                                        )}

                                    </div>

                                    <div class="rarity">

                                        ${esc(
                                            e.rarity ||
                                            ""
                                        )}

                                    </div>

                                </div>

                                <div class="price">

                                    ${Number(
                                        e.price || 0
                                    ).toLocaleString()}
                                    🥚

                                </div>

                            </div>


                            <button
                                class="action buy-egg"
                                data-id="${id}"
                                type="button"
                            >
                                Купить
                            </button>

                        </div>

                    `)
                    .join("");


            document
                .querySelectorAll(".buy-egg")
                .forEach(button => {

                    button.onclick =
                        async () => {

                            try {

                                const x =
                                    await api(
                                        "/api/eggs/buy",
                                        {
                                            method:
                                                "POST",

                                            body:
                                                JSON.stringify({
                                                    egg_id:
                                                        Number(
                                                            button
                                                                .dataset
                                                                .id
                                                        )
                                                })
                                        }
                                    );


                                setData(
                                    x.data
                                );


                                toast(
                                    `🎉 ${x.egg?.emoji || "🥚"} ${x.egg?.name || "Яйцо куплено"}`
                                );


                                loadEggs();


                            } catch (e) {

                                toast(
                                    e.message
                                );
                            }
                        };
                });


            return;
        }


        /*
         * МОИ ЯЙЦА
         */

        const shop =
            r.shop || {};


        const owned =
            r.owned || {};


        const entries =
            Array.isArray(shop)
                ? shop.map(
                    e => [
                        String(e.id),
                        e
                    ]
                )
                : Object.entries(
                    shop
                );


        const ownedEntries =
            entries.filter(
                ([id]) =>
                    Number(
                        owned[id] || 0
                    ) > 0
            );


        if (!ownedEntries.length) {

            $("eggContent").innerHTML = `

                <div class="egg-item">

                    🎒 У тебя пока нет яиц.

                </div>
            `;

            return;
        }


        $("eggContent").innerHTML =
            ownedEntries
                .map(([id, e]) => `

                    <div class="egg-item">

                        <div class="egg-top">

                            <div>

                                <div class="egg-name">

                                    ${
                                        esc(
                                            e.emoji ||
                                            "🥚"
                                        )
                                    }

                                    ${esc(
                                        e.name
                                    )}

                                </div>

                                <div class="rarity">

                                    ${esc(
                                        e.rarity ||
                                        ""
                                    )}

                                </div>

                            </div>


                            <div class="price">

                                × ${Number(
                                    owned[id] || 0
                                )}

                            </div>

                        </div>


                        <button
                            class="action open-egg"
                            data-id="${id}"
                            type="button"
                        >
                            🥚 Открыть
                        </button>

                    </div>

                `)
                .join("");


        document
            .querySelectorAll(".open-egg")
            .forEach(button => {

                button.onclick =
                    async () => {

                        try {

                            const x =
                                await api(
                                    "/api/eggs/open",
                                    {
                                        method:
                                            "POST",

                                        body:
                                            JSON.stringify({
                                                egg_id:
                                                    Number(
                                                        button
                                                            .dataset
                                                            .id
                                                    )
                                            })
                                    }
                                );


                            setData(
                                x.data
                            );


                            toast(
                                `🎉 ${x.egg?.emoji || "🥚"} Открыто · +${x.reward} Egg Coins`
                            );


                            loadEggs();


                        } catch (e) {

                            toast(
                                e.message
                            );
                        }
                    };
            });


    } catch (e) {

        toast(e.message);
    }
}


/* =========================
   MODAL
========================= */

function openModal(html) {

    $("modalContent").innerHTML =
        html;


    $("modal")
        .classList
        .remove("hidden");
}


function closeModal() {

    $("modal")
        .classList
        .add("hidden");
}


if ($("modalClose")) {

    $("modalClose").onclick =
        closeModal;
}


if ($("modal")) {

    $("modal").onclick =
        e => {

            if (
                e.target.id ===
                "modal"
            ) {

                closeModal();
            }
        };
}


/* =========================
   ДОСТИЖЕНИЯ
========================= */

if ($("achievementsBtn")) {

    $("achievementsBtn").onclick =
        async () => {

            try {

                const r =
                    await api(
                        "/api/achievements"
                    );


                openModal(`

                    <h2>
                        🏆 Достижения
                    </h2>

                    ${
                        (r.items || [])
                            .map(a => `

                                <div class="achievement">

                                    <b>

                                        ${
                                            a.unlocked
                                                ? "✅"
                                                : "🔒"
                                        }

                                        ${esc(
                                            a.name
                                        )}

                                    </b>

                                    <div class="rarity">

                                        ${esc(
                                            a.description
                                        )}

                                    </div>

                                    <div class="price">

                                        🎁 +${a.reward}
                                        Egg Coins

                                    </div>

                                </div>

                            `)
                            .join("")
                    }

                `);


            } catch (e) {

                toast(e.message);
            }
        };
}


/* =========================
   ЛИДЕРБОРД
========================= */

if ($("leaderboardBtn")) {

    $("leaderboardBtn").onclick =
        async () => {

            try {

                const r =
                    await api(
                        "/api/leaderboard"
                    );


                openModal(`

                    <h2>
                        📊 Таблица лидеров
                    </h2>

                    ${
                        (r.players || [])
                            .map((p, i) => `

                                <div class="leader">

                                    <div>

                                        <b>

                                            ${
                                                p.avatar ||
                                                "🥚"
                                            }

                                            ${i + 1}.

                                            ${
                                                esc(
                                                    p.username
                                                        ? "@" +
                                                          p.username
                                                        : "ID " +
                                                          p.user_id
                                                )
                                            }

                                        </b>

                                        <small>

                                            ⭐ Уровень
                                            ${p.level}

                                        </small>

                                    </div>

                                    <b>

                                        🥚
                                        ${Number(
                                            p.egg_coins || 0
                                        ).toLocaleString()}

                                    </b>

                                </div>

                            `)
                            .join("")
                    }


                    <p>

                        Твоё место:
                        <b>
                            ${r.my_rank || "—"}
                        </b>

                    </p>

                `);


            } catch (e) {

                toast(e.message);
            }
        };
}


/* =========================
   ЕЖЕДНЕВНЫЕ ЗАДАНИЯ
========================= */

async function loadTasks() {

    try {

        const r =
            await api(
                "/api/daily/tasks"
            );


        openModal(`

            <h2>
                🎯 Ежедневные задания
            </h2>

            ${
                (r.tasks || [])
                    .map(t => `

                        <div class="task">

                            <b>
                                ${esc(
                                    t.title
                                )}
                            </b>

                            <div class="progress">

                                <div
                                    style="
                                        width:${Math.min(
                                            100,
                                            Number(t.progress || 0) /
                                            Math.max(
                                                1,
                                                Number(t.target || 1)
                                            ) *
                                            100
                                        )}%
                                    "
                                ></div>

                            </div>

                            <p>

                                ${t.progress}/${t.target}

                                · 🎁 +${t.reward}

                            </p>


                            <button
                                class="action claim-task"
                                data-id="${t.id}"
                                type="button"
                                ${
                                    t.claimed ||
                                    t.progress < t.target
                                        ? "disabled"
                                        : ""
                                }
                            >

                                ${
                                    t.claimed
                                        ? "Получено"
                                        : "Забрать"
                                }

                            </button>

                        </div>

                    `)
                    .join("")
            }

        `);


        document
            .querySelectorAll(".claim-task")
            .forEach(button => {

                button.onclick =
                    async () => {

                        try {

                            const x =
                                await api(
                                    "/api/daily/tasks/claim",
                                    {
                                        method:
                                            "POST",

                                        body:
                                            JSON.stringify({
                                                task_id:
                                                    button
                                                        .dataset
                                                        .id
                                            })
                                    }
                                );


                            setData(
                                x.data
                            );


                            toast(
                                `🎁 +${x.reward} Egg Coins`
                            );


                            loadTasks();


                        } catch (e) {

                            toast(
                                e.message
                            );
                        }
                    };
            });


    } catch (e) {

        toast(e.message);
    }
}


if ($("tasksBtn")) {

    $("tasksBtn").onclick =
        loadTasks;
}


/* =========================
   ЕЖЕДНЕВНОЙ БОНУС
========================= */

if ($("bonusBtn")) {

    $("bonusBtn").onclick =
        async () => {

            try {

                const r =
                    await api(
                        "/api/daily/bonus",
                        {
                            method:
                                "POST",

                            body: "{}"
                        }
                    );


                setData(
                    r.data
                );


                toast(
                    `🎁 +${r.reward} Egg Coins`
                );


            } catch (e) {

                toast(e.message);
            }
        };
}


/* =========================
   BOSS
========================= */

async function loadBoss() {

    try {

        const r =
            await api(
                "/api/boss"
            );


        const maxHp =
            Math.max(
                1,
                Number(r.max_hp || 1)
            );


        const hp =
            Math.max(
                0,
                Number(r.hp || 0)
            );


        openModal(`

            <h2>
                👾 EGG BOSS
            </h2>

            <div class="boss-name">
                🌑 Тёмный Хранитель
            </div>

            <div class="boss-hp">

                ${hp}/${maxHp}

            </div>

            <div class="boss-bar">

                <div
                    style="
                        width:${Math.min(
                            100,
                            hp / maxHp * 100
                        )}%
                    "
                ></div>

            </div>

            <p>

                ⚔️ Твой урон:
                <b>
                    ${r.my_damage || 0}
                </b>

            </p>

            <button
                id="attackBoss"
                class="primary"
                type="button"
            >

                ⚔️ Атаковать

            </button>

        `);


        $("attackBoss").onclick =
            async () => {

                try {

                    const x =
                        await api(
                            "/api/boss/attack",
                            {
                                method:
                                    "POST",

                                body: "{}"
                            }
                        );


                    setData(
                        x.data
                    );


                    toast(
                        x.defeated
                            ? "🎉 Босс побеждён! +100 Egg Coins"
                            : `⚔️ -${x.damage} HP`
                    );


                    loadBoss();


                } catch (e) {

                    toast(
                        e.message
                    );
                }
            };


    } catch (e) {

        toast(e.message);
    }
}


if ($("bossBtn")) {

    $("bossBtn").onclick =
        loadBoss;
}


/* =========================
   ПРЕДМЕТЫ
========================= */

async function loadItems() {

    try {

        const r =
            await api(
                "/api/items"
            );


        const items =
            r.items || {};


        const entries =
            Array.isArray(items)
                ? items.map(
                    x => [
                        String(x.id),
                        x
                    ]
                )
                : Object.entries(
                    items
                );


        openModal(`

            <h2>
                🛒 Магазин предметов
            </h2>

            ${
                entries
                    .map(([id, x]) => `

                        <div class="item-card">

                            <div class="item-top">

                                <b>
                                    ${esc(
                                        x.name
                                    )}
                                </b>

                                <span class="price">

                                    ${Number(
                                        x.price || 0
                                    ).toLocaleString()}
                                    🥚

                                </span>

                            </div>

                            <div class="rarity">

                                ${esc(
                                    x.description
                                )}

                            </div>

                            <p>

                                📦 ${x.count || 0}

                                ${
                                    x.active_seconds
                                        ? ` · ⚡ активно ${x.active_seconds} сек.`
                                        : ""
                                }

                            </p>


                            <button
                                class="action buy-item"
                                data-id="${id}"
                                type="button"
                            >
                                Купить
                            </button>


                            ${
                                Number(x.count || 0)
                                    ? `
                                        <button
                                            class="action activate-item"
                                            data-id="${id}"
                                            type="button"
                                        >
                                            Активировать
                                        </button>
                                    `
                                    : ""
                            }

                        </div>

                    `)
                    .join("")
            }

        `);


        document
            .querySelectorAll(".buy-item")
            .forEach(button => {

                button.onclick =
                    async () => {

                        try {

                            const x =
                                await api(
                                    "/api/items/buy",
                                    {
                                        method:
                                            "POST",

                                        body:
                                            JSON.stringify({
                                                item_id:
                                                    Number(
                                                        button
                                                            .dataset
                                                            .id
                                                    )
                                            })
                                    }
                                );


                            setData(
                                x.data
                            );


                            toast(
                                "🛒 Куплено"
                            );


                            loadItems();


                        } catch (e) {

                            toast(
                                e.message
                            );
                        }
                    };
            });


        document
            .querySelectorAll(".activate-item")
            .forEach(button => {

                button.onclick =
                    async () => {

                        try {

                            const x =
                                await api(
                                    "/api/items/activate",
                                    {
                                        method:
                                            "POST",

                                        body:
                                            JSON.stringify({
                                                item_id:
                                                    Number(
                                                        button
                                                            .dataset
                                                            .id
                                                    )
                                            })
                                    }
                                );


                            setData(
                                x.data
                            );


                            toast(
                                "⚡ Активировано на 10 минут"
                            );


                            loadItems();


                        } catch (e) {

                            toast(
                                e.message
                            );
                        }
                    };
            });


    } catch (e) {

        toast(e.message);
    }
}


if ($("itemsBtn")) {

    $("itemsBtn").onclick =
        loadItems;
}


if ($("profileItems")) {

    $("profileItems").onclick =
        loadItems;
}


/* =========================
   ВЫБОР АВАТАРА
========================= */

const DEFAULT_AVATARS = [
    "🥚",
    "🐣",
    "🐤",
    "🐥",
    "🐔",
    "🦆",
    "🐲",
    "🦄",
    "👑",
    "💎",
    "🔥",
    "⚡",
    "🌑",
    "🚀",
    "👾"
];


function getAvatars() {

    if (
        state.data &&
        Array.isArray(
            state.data.avatars
        ) &&
        state.data.avatars.length
    ) {

        return state.data.avatars;
    }


    return DEFAULT_AVATARS;
}


function openAvatarSelector() {

    const avatars =
        getAvatars();


    const current =
        state.data?.avatar ||
        "🥚";


    openModal(`

        <h2>
            🖼️ Выбор аватара
        </h2>

        <p>
            Выбери свой аватар:
        </p>

        <div
            class="avatar-grid"
            style="
                display:grid;
                grid-template-columns:
                    repeat(5,1fr);
                gap:10px;
                margin-top:15px;
            "
        >

            ${
                avatars
                    .map(avatar => `

                        <button
                            class="avatar-choice"
                            data-avatar="${esc(
                                avatar
                            )}"
                            type="button"
                            style="
                                font-size:32px;
                                padding:12px;
                                border-radius:14px;
                                background:
                                    ${
                                        avatar === current
                                            ? "#6730a3"
                                            : "#20102e"
                                    };
                                border:
                                    1px solid
                                    rgba(
                                        255,
                                        255,
                                        255,
                                        .08
                                    );
                            "
                        >
                            ${esc(avatar)}
                        </button>

                    `)
                    .join("")
            }

        </div>

    `);


    document
        .querySelectorAll(".avatar-choice")
        .forEach(button => {

            button.onclick =
                async () => {

                    const avatar =
                        button.dataset.avatar;


                    try {

                        const r =
                            await api(
                                "/api/avatar",
                                {
                                    method:
                                        "POST",

                                    body:
                                        JSON.stringify({
                                            avatar
                                        })
                                }
                            );


                        setData(
                            r.data
                        );


                        closeModal();


                        toast(
                            `🖼️ Аватар изменён на ${avatar}`
                        );


                    } catch (e) {

                        toast(e.message);
                    }
                };
        });
}


/* =========================
   ВЫВОД ЯИЦ
========================= */

async function openWithdrawal() {

    try {

        const r =
            await api(
                "/api/withdrawal"
            );


        const eggs =
            r.eggs || {};


        const shop =
            r.shop || {};


        const entries =
            Array.isArray(shop)
                ? shop.map(
                    e => [
                        String(e.id),
                        e
                    ]
                )
                : Object.entries(
                    shop
                );


        const owned =
            entries.filter(
                ([id]) =>
                    Number(
                        eggs[id] || 0
                    ) > 0
            );


        const total =
            Number(
                r.total_eggs ??
                r.total ??
                Object.values(eggs)
                    .reduce(
                        (sum, value) =>
                            sum +
                            Number(
                                value || 0
                            ),
                        0
                    )
            );


        openModal(`

            <h2>
                🥚 Вывод яиц
            </h2>

            <p>

                Всего яиц:
                <b>${total}</b>

            </p>


            ${
                owned.length
                    ? owned
                        .map(([id, egg]) => `

                            <div class="egg-item">

                                ${
                                    esc(
                                        egg.emoji ||
                                        "🥚"
                                    )
                                }

                                ${esc(
                                    egg.name ||
                                    `Яйцо #${id}`
                                )}

                                ×
                                ${Number(
                                    eggs[id] || 0
                                )}

                            </div>

                        `)
                        .join("")
                    : `
                        <p>
                            🎒 У тебя нет яиц.
                        </p>
                    `
            }


            <button
                id="withdrawGo"
                class="primary"
                type="button"
            >

                🥚 Перейти к боту вывода

            </button>

        `);


        $("withdrawGo").onclick =
            () => {

                if (
                    tg?.openTelegramLink &&
                    r.bot
                ) {

                    tg.openTelegramLink(
                        r.bot
                    );

                } else if (r.bot) {

                    window.open(
                        r.bot,
                        "_blank"
                    );
                }
            };


    } catch (e) {

        toast(e.message);
    }
}


if ($("withdrawBtn")) {

    $("withdrawBtn").onclick =
        openWithdrawal;
}


if ($("profileWithdraw")) {

    $("profileWithdraw").onclick =
        openWithdrawal;
}


/* =========================
   ЗАПУСК
========================= */

loadEggs();

init();
