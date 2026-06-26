const askBtn = document.getElementById("askBtn");
const questionInput = document.getElementById("question");
const ownerInput = document.getElementById("owner");
const confInput = document.getElementById("confidentiality");
const useWebInput = document.getElementById("useWeb");
const answerBox = document.getElementById("answer");
const metaBox = document.getElementById("meta");
const citationsBox = document.getElementById("citations");
const thinkingPanel = document.getElementById("thinkingPanel");
const progressFill = document.getElementById("progressFill");
const progressPct = document.getElementById("progressPct");
const progressLabel = document.getElementById("progressLabel");
const thinkingSteps = document.querySelectorAll("#thinkingSteps li");

let progressTimer = null;

function setProgress(percent, label) {
  const value = Math.max(0, Math.min(100, percent));
  if (progressFill) progressFill.style.width = `${value}%`;
  if (progressPct) progressPct.textContent = `${Math.round(value)}%`;
  if (progressLabel && label) progressLabel.textContent = label;

  thinkingSteps.forEach((node, idx) => {
    node.classList.remove("active", "done");
    if (value >= (idx + 1) * 25) {
      node.classList.add("done");
    } else if (value >= idx * 25) {
      node.classList.add("active");
    }
  });
}

function startThinking() {
  if (thinkingPanel) thinkingPanel.classList.remove("hidden");
  if (progressTimer) clearInterval(progressTimer);

  let current = 5;
  setProgress(current, "正在解析问题...");
  progressTimer = setInterval(() => {
    if (current < 35) {
      current += 3;
      setProgress(current, "正在检索证据...");
      return;
    }
    if (current < 70) {
      current += 2;
      setProgress(current, "正在生成回答...");
      return;
    }
    if (current < 92) {
      current += 1;
      setProgress(current, "正在整理结果...");
      return;
    }
    setProgress(92, "即将完成...");
  }, 260);
}

function finishThinking(ok, latencyMs) {
  if (progressTimer) {
    clearInterval(progressTimer);
    progressTimer = null;
  }
  if (ok) {
    const suffix = typeof latencyMs === "number" ? `（${latencyMs}ms）` : "";
    setProgress(100, `完成${suffix}`);
  } else {
    setProgress(100, "请求失败");
  }
}

function renderCitations(citations) {
  citationsBox.innerHTML = "";
  if (!citations || citations.length === 0) {
    citationsBox.innerHTML = "<li>无可用引用</li>";
    return;
  }

  citations.forEach((c) => {
    const li = document.createElement("li");
    li.textContent = `[${c.chunk_id}] ${c.source} p.${c.page} ${c.section} | score=${c.score.toFixed(3)} | ${c.snippet}`;
    citationsBox.appendChild(li);
  });
}

askBtn.addEventListener("click", async () => {
  const question = questionInput.value.trim();
  if (!question) {
    alert("请先输入问题");
    return;
  }

  askBtn.disabled = true;
  answerBox.textContent = "思考中...";
  metaBox.textContent = "";
  startThinking();

  try {
    const body = {
      question,
      owner: ownerInput.value.trim() || null,
      confidentiality: confInput.value.trim() || null,
      use_web: !!useWebInput?.checked,
      web_top_k: 3,
    };

    const resp = await fetch("/v1/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!resp.ok) {
      const err = await resp.text();
      throw new Error(err || `HTTP ${resp.status}`);
    }

    const data = await resp.json();
    answerBox.textContent = data.answer;
    metaBox.textContent = `request_id=${data.request_id} | confidence=${data.confidence} | latency=${data.latency_ms}ms | rewritten=${data.rewritten_question}`;
    renderCitations(data.citations);
    finishThinking(true, data.latency_ms);
  } catch (e) {
    answerBox.textContent = `请求失败: ${e.message}`;
    citationsBox.innerHTML = "";
    finishThinking(false);
  } finally {
    askBtn.disabled = false;
  }
});
