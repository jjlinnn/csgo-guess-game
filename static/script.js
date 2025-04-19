function submitGuess() {
  const guess = document.getElementById("guessInput").value;

  fetch("/guess", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ guess: guess })
  })
    .then(res => res.json())
    .then(data => {
      document.getElementById("result").innerText = data.result;
      document.getElementById("playerTable").style.display = "table";

      if (data.player) {
        let row = `
          <tr>
            <td>${data.player.name}</td>
            <td class="${arrowClass(data.feedback.mana)}">${data.player.mana}</td>
            <td class="${arrowClass(data.feedback.attack)}">${data.player.attack}</td>
            <td class="${arrowClass(data.feedback.health)}">${data.player.health}</td>
            <td>${data.player.tribe}</td>
          </tr>
        `;

        document.getElementById("playerRow").innerHTML += row;
        document.getElementById("guessInput").value = "";
      }
    });
}

function restartGame() {
  fetch("/restart", { method: "POST" })
    .then(res => res.json())
    .then(data => {
      console.log("新游戏已开始");
      document.getElementById("playerRow").innerHTML = "";
      document.getElementById("result").innerText = "";
      document.getElementById("guessInput").value = "";
      document.getElementById("playerTable").style.display = "none";
      document.getElementById("guessInput").disabled = false;
    });
}

function arrowClass(status) {
  if (status === "up") return "arrow-up";
  if (status === "down") return "arrow-down";
  return "";
}

let allNames = [];

window.onload = function () {
  fetch("/players")
    .then(res => res.json())
    .then(data => allNames = data);
};

document.getElementById("guessInput").addEventListener("input", function () {
  const input = this.value.toLowerCase();
  const suggestionBox = document.getElementById("suggestions");
  suggestionBox.innerHTML = "";

  if (input.length === 0) return;

  const matches = allNames.filter(name => name.toLowerCase().startsWith(input)).slice(0, 5);
  matches.forEach(name => {
    const li = document.createElement("li");
    li.textContent = name;
    li.onclick = () => {
      document.getElementById("guessInput").value = name;
      suggestionBox.innerHTML = "";
    };
    suggestionBox.appendChild(li);
  });
});

// ✅ 添加炉石卡牌
function addPlayer() {
  const data = {
    name: document.getElementById("name").value.trim(),
    mana: parseInt(document.getElementById("mana").value),
    attack: parseInt(document.getElementById("attack").value),
    health: parseInt(document.getElementById("health").value),
    tribe: document.getElementById("tribe").value.trim()
  };

  fetch("/add_player", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  })
    .then(res => res.json())
    .then(result => {
      document.getElementById("add-result").innerText = result.message;

      ["name", "mana", "attack", "health", "tribe"].forEach(id =>
        document.getElementById(id).value = ""
      );
    });
}
