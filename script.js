const lineupKey = 'lineup';
const indexKey = 'currentIndex';
const defaultLineup = ['Sarah', 'Jacob', 'Shannon', 'Kaleb', 'Martin', 'Keith', 'Quinn'];

function loadState() {
    const savedLineup = JSON.parse(localStorage.getItem(lineupKey) || '[]');
    const savedIndex = parseInt(localStorage.getItem(indexKey) || '0', 10);
    const lineup = savedLineup.length ? savedLineup : defaultLineup.slice();
    return {
        lineup,
        index: savedIndex % lineup.length
    };
}

function saveState(lineup, index) {
    localStorage.setItem(lineupKey, JSON.stringify(lineup));
    localStorage.setItem(indexKey, index.toString());
}

function render(lineup, index) {
    const atBatEl = document.getElementById('atBat');
    const onDeckEl = document.getElementById('onDeck');
    const inHoleEl = document.getElementById('inHole');
    const listEl = document.getElementById('lineupList');
    listEl.innerHTML = '';

    lineup.forEach((name, i) => {
        const li = document.createElement('li');
        li.textContent = name;
        if (i === index) {
            li.classList.add('current');
            atBatEl.textContent = `At Bat: ${name}`;
        } else if (i === (index + 1) % lineup.length) {
            li.classList.add('next');
            onDeckEl.textContent = `On Deck: ${name}`;
        } else if (i === (index + 2) % lineup.length) {
            inHoleEl.textContent = `In the Hole: ${name}`;
        }
        listEl.appendChild(li);
    });
}

function moveNext(state) {
    state.index = (state.index + 1) % state.lineup.length;
    saveState(state.lineup, state.index);
    render(state.lineup, state.index);
}

function addName(state, name) {
    if (name.trim()) {
        state.lineup.push(name.trim());
        saveState(state.lineup, state.index);
        render(state.lineup, state.index);
    }
}

function pitchBall(callback) {
    const ball = document.createElement('div');
    ball.className = 'ball';
    ball.textContent = '⚾';
    ball.style.position = 'absolute';
    ball.style.top = '120px';
    ball.style.left = '120px';
    ball.style.transform = 'rotate(-45deg)';
    document.querySelector('.diamond').appendChild(ball);

    requestAnimationFrame(() => {
        ball.style.transition = 'all 0.5s linear';
        ball.style.top = '260px';
        ball.style.left = '120px';
    });

    setTimeout(() => {
        ball.remove();
        callback();
    }, 600);
}

async function runBases(callback) {
    const runner = document.getElementById('runner');
    runner.classList.remove('hidden');
    runner.style.top = '260px';
    runner.style.left = '120px';

    const sleep = ms => new Promise(r => setTimeout(r, ms));

    // small delay to ensure the element is visible before moving
    await sleep(50);

    runner.style.left = '280px'; // to first
    await sleep(800); // move duration
    await sleep(500); // pause at first

    runner.style.top = '100px'; // to second
    await sleep(800);
    await sleep(500); // pause at second

    runner.style.left = '120px'; // to third
    await sleep(800);
    await sleep(500); // pause at third

    runner.style.top = '260px'; // back to home
    await sleep(800);

    runner.classList.add('hidden');
    callback();
}

function fireworks() {
    const duration = 2 * 1000;
    const end = Date.now() + duration;
    const confettiCanvas = document.getElementById('confetti');

    (function frame() {
        confetti({
            particleCount: 5,
            angle: 60,
            spread: 55,
            origin: { x: 0 },
            colors: ['#bb0000', '#ffffff']
        });
        confetti({
            particleCount: 5,
            angle: 120,
            spread: 55,
            origin: { x: 1 },
            colors: ['#bb0000', '#ffffff']
        });
        if (Date.now() < end) {
            requestAnimationFrame(frame);
        }
    })();
}

function showOverlay(text, color) {
    const overlay = document.getElementById('overlay');
    overlay.textContent = text;
    overlay.style.backgroundColor = color || 'rgba(0,0,0,0.5)';
    overlay.classList.remove('hidden');
    setTimeout(() => {
        overlay.classList.add('hidden');
    }, 1500);
}

function strikeOutAnim(callback) {
    const batter = document.querySelector('.batter');
    batter.style.transition = 'transform 1s ease-out, opacity 1s';
    batter.style.transform = 'translateX(-80px) rotate(-45deg)';
    batter.style.opacity = '0';
    setTimeout(() => {
        batter.style.transition = '';
        batter.style.transform = 'rotate(-45deg)';
        batter.style.opacity = '1';
        callback();
    }, 1100);
}

window.addEventListener('DOMContentLoaded', () => {
    const state = loadState();
    render(state.lineup, state.index);

    document.getElementById('strikeBtn').addEventListener('click', () => {
        pitchBall(() => strikeOutAnim(() => {
            showOverlay('STRIKEOUT!', 'rgba(255,0,0,0.7)');
            moveNext(state);
        }));
    });

    document.getElementById('homerunBtn').addEventListener('click', () => {
        pitchBall(() => runBases(() => {
            fireworks();
            showOverlay('HOME RUN!', 'rgba(0,0,0,0.5)');
            moveNext(state);
        }));
    });

    document.getElementById('addBtn').addEventListener('click', () => {
        const nameInput = document.getElementById('nameInput');
        addName(state, nameInput.value);
        nameInput.value = '';
    });
});
