"use strict";

const LETTERS = ["a", "b", "c", "d", "e", "f", "g", "h"];

const el = {
  exam: document.getElementById("exam"),
  qid: document.getElementById("qid"),
  progress: document.getElementById("progress"),
  question: document.getElementById("question"),
  choices: document.getElementById("choices"),
  status: document.getElementById("status"),
  next: document.getElementById("next"),
};

let questions = [];
let order = [];   // shuffled list of array positions, no repeats within a pass
let pos = 0;      // pointer into `order`
let answered = false;

/* Fisher–Yates shuffle of [0..n-1] */
function shuffledIndices(n) {
  const a = Array.from({ length: n }, (_, i) => i);
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

function newPass() {
  order = shuffledIndices(questions.length);
  pos = 0;
}

function render() {
  answered = false;
  const q = questions[order[pos]];

  el.exam.textContent = q.exam || "Examen";
  el.qid.textContent = "#" + q.id;            // original, stable index of the question
  el.progress.textContent = (pos + 1) + " / " + questions.length;
  el.question.textContent = q.question;
  el.status.textContent = " ";
  el.status.className = "status";
  el.next.hidden = true;

  el.choices.innerHTML = "";
  q.choices.forEach((text, i) => {
    const li = document.createElement("li");
    const btn = document.createElement("button");
    btn.className = "choice";
    btn.type = "button";
    btn.innerHTML =
      '<span class="choice__letter">' + (LETTERS[i] || (i + 1)) + "</span>" +
      '<span class="choice__text"></span>';
    btn.querySelector(".choice__text").textContent = text;
    btn.addEventListener("click", () => choose(i, q));
    li.appendChild(btn);
    el.choices.appendChild(li);
  });
}

function choose(picked, q) {
  if (answered) return;
  answered = true;

  const buttons = el.choices.querySelectorAll(".choice");
  buttons.forEach((btn, i) => {
    btn.disabled = true;
    if (i === q.correctIndex) btn.classList.add("is-correct");
    else if (i === picked) btn.classList.add("is-wrong");
  });

  const correct = picked === q.correctIndex;
  el.status.textContent = correct ? "Corect!" : "Greșit";
  el.status.className = "status " + (correct ? "ok" : "no");
  el.next.hidden = false;
  el.next.focus();
}

function nextQuestion() {
  pos++;
  if (pos >= order.length) newPass();   // ran through all → reshuffle and loop
  render();
}

el.next.addEventListener("click", nextQuestion);

async function init() {
  try {
    const res = await fetch("questions.json", { cache: "no-store" });
    if (!res.ok) throw new Error("HTTP " + res.status);
    questions = await res.json();
  } catch (err) {
    el.question.textContent =
      "Nu am putut încărca întrebările. Pornește aplicația prin server (node server.js), nu direct din fișier.";
    return;
  }

  if (!Array.isArray(questions) || questions.length === 0) {
    el.question.textContent = "Nu există întrebări disponibile.";
    return;
  }

  newPass();
  render();
}

init();
