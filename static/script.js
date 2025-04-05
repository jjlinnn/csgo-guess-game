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
            <td>${data.player.team}</td>
            <td class="flag-cell">
              <img src="https://flagcdn.com/24x18/${data.player.flag}.png" alt="${data.player.region}" />
            </td>
            <td class="${arrowClass(data.feedback.age)}">${data.player.age}</td>
            <td>${data.player.role}</td>
            <td class="${arrowClass(data.feedback.majors)}">${data.player.majors}</td>
          </tr>
        `;
  
        // ✅ 每次追加新行，而不是清空旧行
        document.getElementById("playerRow").innerHTML += row;
  
        // 清空输入框
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

  // 页面加载时拉取选手名字
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
  
  // 原来的 submitGuess 和 arrowClass 函数保持不变
   
  function addPlayer() {
    const data = {
      name: document.getElementById("name").value.trim(),
      team: document.getElementById("team").value.trim(),
      region: document.getElementById("region").value.trim(),
      flag: document.getElementById("flag").value.trim().toLowerCase(),
      age: parseInt(document.getElementById("age").value),
      role: document.getElementById("role").value.trim(),
      majors: parseInt(document.getElementById("majors").value)
    };
  
    fetch("/add_player", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    })
    .then(res => res.json())
    .then(result => {
      document.getElementById("add-result").innerText = result.message;
  
      // 清空表单
      ["name", "team", "region", "flag", "age", "role", "majors"].forEach(id =>
        document.getElementById(id).value = ""
      );
    });
  }