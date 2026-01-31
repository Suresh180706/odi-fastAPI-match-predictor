async function predict() {
    const payload = {
        team1: team1.value,
        team2: team2.value,
        venue: venue.value,
        toss_winner: toss_winner.value,
        toss_decision: toss_decision.value,
        season: season.value
    };

    const res = await fetch("/predict", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(payload)
    });

    const data = await res.json();
    const div = document.getElementById("result");

    if (data.error) {
        div.innerHTML = `<p style="color:red">${data.error}</p>`;
        return;
    }

    div.innerHTML = `
        <h3>🏆 Winner: ${data.winner}</h3>

        <p>${data.team1} – ${data.team1_confidence}%</p>
        <div class="bar"><div class="fill" style="width:${data.team1_confidence}%"></div></div>

        <p>${data.team2} – ${data.team2_confidence}%</p>
        <div class="bar"><div class="fill" style="width:${data.team2_confidence}%"></div></div>

        <p>📊 ${data.reason}</p>
    `;
}
