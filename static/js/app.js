// 玄机小筑 — 前端交互逻辑

document.addEventListener('DOMContentLoaded', () => {
    // 汉堡菜单
    const navToggle = document.getElementById('navToggle');
    const navMenu = document.getElementById('navMenu');
    if (navToggle && navMenu) {
        navToggle.addEventListener('click', () => {
            navMenu.classList.toggle('open');
        });
        document.addEventListener('click', (e) => {
            if (!navToggle.contains(e.target) && !navMenu.contains(e.target)) {
                navMenu.classList.remove('open');
            }
        });
    }

    // 折叠面板
    document.querySelectorAll('.accordion-header').forEach(header => {
        header.addEventListener('click', () => {
            const body = header.nextElementSibling;
            if (body) {
                body.classList.toggle('open');
            }
        });
    });

    // 淡入动画
    document.querySelectorAll('.fade-in').forEach((el, i) => {
        el.style.animationDelay = `${i * 0.1}s`;
    });

    // 投币页面逻辑
    if (document.querySelector('.toss-area')) {
        initIchangToss();
    }

    // 签筒动画
    if (document.querySelector('.lot-draw-area')) {
        initGuanyinDraw();
    }
});

// ============================================================
// 周易金钱卦 — 逐爻投币
// ============================================================
function initIchangToss() {
    const tossBtn = document.getElementById('tossBtn');
    const coinArea = document.getElementById('coinArea');
    const resultDisplay = document.getElementById('resultDisplay');
    const yaoProgress = document.getElementById('yaoProgress');
    const fullResult = document.getElementById('fullResult');
    const submitForm = document.getElementById('tossForm');

    if (!tossBtn) return;

    let currentToss = 0;
    const tosses = [];
    const tossValues = [null, null, null, null, null, null];

    // 初始化进度点
    for (let i = 0; i < 6; i++) {
        const dot = document.createElement('span');
        dot.className = 'yao-dot';
        dot.id = `yao-dot-${i}`;
        yaoProgress.appendChild(dot);
    }

    // 创建硬币
    for (let i = 0; i < 3; i++) {
        const coin = document.createElement('div');
        coin.className = 'coin';
        coin.id = `coin-${i}`;
        coin.textContent = '☯';
        coinArea.appendChild(coin);
    }

    tossBtn.addEventListener('click', () => {
        if (currentToss >= 6) return;

        tossBtn.disabled = true;
        document.getElementById(`yao-dot-${currentToss}`).classList.add('current');

        // 硬币翻转动画
        for (let i = 0; i < 3; i++) {
            const coin = document.getElementById(`coin-${i}`);
            coin.classList.add('flipping');
            setTimeout(() => coin.classList.remove('flipping'), 600);
        }

        // 调用API
        fetch('/api/iching/toss')
            .then(r => r.json())
            .then(data => {
                const val = data.value;
                tossValues[currentToss] = val;

                // 更新硬币显示
                setTimeout(() => {
                    const coins = simulateCoins(val);
                    for (let i = 0; i < 3; i++) {
                        const coin = document.getElementById(`coin-${i}`);
                        coin.textContent = coins[i] === '阳' ? '⚊' : '⚋';
                        coin.className = `coin ${coins[i] === '阳' ? 'yang' : 'yin'}`;
                    }

                    // 显示结果
                    const yaoNames = {6:'老阴 ██  ×', 7:'少阳 ███▌', 8:'少阴 ██ ▏', 9:'老阳 ███○'};
                    const yaoNamesShort = {6:'老阴(变爻)', 7:'少阳', 8:'少阴', 9:'老阳(变爻)'};
                    resultDisplay.innerHTML = `
                        <div class="interp-block fade-in">
                            <div class="interp-source">第${currentToss+1}爻（${currentToss===0?'初':currentToss===1?'二':currentToss===2?'三':currentToss===3?'四':currentToss===4?'五':'上'}爻）</div>
                            <div class="interp-text">${yaoNames[val]}</div>
                            <div class="text-light" style="font-size:0.8rem">${yaoNamesShort[val]}</div>
                        </div>`;

                    document.getElementById(`yao-dot-${currentToss}`).classList.remove('current');
                    document.getElementById(`yao-dot-${currentToss}`).classList.add('done');

                    currentToss++;
                    tossBtn.textContent = currentToss >= 6 ? '查看卦象' : `掷第${currentToss+1}次`;

                    if (currentToss >= 6) {
                        finishTossing();
                    }

                    tossBtn.disabled = false;
                }, 700);

                // 隐藏值存入表单
                if (submitForm) {
                    let hidden = submitForm.querySelector(`#toss-${currentToss}`);
                    if (!hidden) {
                        hidden = document.createElement('input');
                        hidden.type = 'hidden';
                        hidden.name = `toss_${currentToss}`;
                        hidden.id = `toss-${currentToss}`;
                        submitForm.appendChild(hidden);
                    }
                    hidden.value = val;
                }
            });
    });

    function finishTossing() {
        tossBtn.textContent = '卦成！查看结果';
        tossBtn.classList.add('btn-primary');
        tossBtn.onclick = () => {
            // 收集所有投币结果
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = '/iching/result';
            for (let i = 0; i < 6; i++) {
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = `toss_${i}`;
                input.value = tossValues[i];
                form.appendChild(input);
            }
            document.body.appendChild(form);
            form.submit();
        };
    }
}

function simulateCoins(val) {
    // 模拟给定总值的硬币结果
    const map = {
        6: ['阴','阴','阴'],
        7: ['阳','阴','阴'],
        8: ['阴','阳','阳'],
        9: ['阳','阳','阳'],
    };
    return map[val] || ['阳','阴','阴'];
}


// ============================================================
// 观音灵签 — 签筒动画
// ============================================================
function initGuanyinDraw() {
    const drawBtn = document.getElementById('drawBtn');
    const lotTube = document.getElementById('lotTube');
    if (!drawBtn || !lotTube) return;

    drawBtn.addEventListener('click', () => {
        drawBtn.disabled = true;
        lotTube.classList.add('shake');

        setTimeout(() => {
            lotTube.classList.remove('shake');
            // 跳转结果页
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = '/guanyin/result';
            document.body.appendChild(form);
            form.submit();
        }, 2000);
    });
}
