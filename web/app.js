const state = {
  provider: "mock",
  sampleOrder: null,
  running: false,
};

const els = {
  health: document.querySelector("#healthStatus"),
  runButton: document.querySelector("#runButton"),
  compareButton: document.querySelector("#compareButton"),
  actionsList: document.querySelector("#actionsList"),
  actionTemplate: document.querySelector("#actionTemplate"),
  metricActions: document.querySelector("#metricActions"),
  metricQuality: document.querySelector("#metricQuality"),
  metricSavings: document.querySelector("#metricSavings"),
  metricProvider: document.querySelector("#metricProvider"),
  summaryTitle: document.querySelector("#summaryTitle"),
  resultBadge: document.querySelector("#resultBadge"),
  customerName: document.querySelector("#customerName"),
  orderTotal: document.querySelector("#orderTotal"),
  customerOrders: document.querySelector("#customerOrders"),
  orderItems: document.querySelector("#orderItems"),
  orderNote: document.querySelector("#orderNote"),
  comparisonTable: document.querySelector("#comparisonTable"),
  providerButtons: [...document.querySelectorAll("[data-provider]")],
};

function titleCase(value) {
  return String(value || "")
    .replace(/[_-]/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

async function requestJson(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with ${response.status}`);
  }
  return response.json();
}

function setBusy(isBusy) {
  state.running = isBusy;
  els.runButton.disabled = isBusy;
  els.compareButton.disabled = isBusy;
  els.runButton.classList.toggle("loading", isBusy);
}

function setProvider(provider) {
  state.provider = provider;
  els.providerButtons.forEach((button) => {
    button.classList.toggle("active", button.dataset.provider === provider);
  });
}

function renderOrder(order) {
  const customer = order.customer || {};
  const items = order.line_items || [];
  const itemCount = items.reduce((sum, item) => sum + Number(item.quantity || 0), 0);
  const customerName = [customer.first_name, customer.last_name].filter(Boolean).join(" ") || "Customer";

  els.customerName.textContent = customerName;
  els.orderTotal.textContent = `${order.currency || "USD"} ${Number(order.total_price || 0).toFixed(2)}`;
  els.customerOrders.textContent = String(customer.orders_count || 0);
  els.orderItems.textContent = `${itemCount} across ${items.length} SKUs`;
  els.orderNote.textContent = order.note || "No customer note attached.";
}

function renderResult(result) {
  const actions = result.actions || [];
  const quality = result.quality_score || {};
  els.metricActions.textContent = String(actions.length);
  els.metricQuality.textContent = String(quality.score || 0);
  els.metricSavings.textContent = String(result.estimated_savings_minutes || 0);
  els.metricProvider.textContent = titleCase(result.provider || state.provider);
  els.summaryTitle.textContent = result.summary || "Automation complete";
  els.resultBadge.textContent = `${titleCase(result.topic || "orders/create")}`;

  els.actionsList.replaceChildren();
  if (!actions.length) {
    const empty = document.createElement("p");
    empty.className = "empty-state";
    empty.textContent = "No actions were recommended for this order.";
    els.actionsList.append(empty);
    return;
  }

  actions.forEach((action) => {
    const node = els.actionTemplate.content.cloneNode(true);
    node.querySelector(".action-type").textContent = titleCase(action.action_type);
    const priority = node.querySelector(".priority");
    priority.textContent = titleCase(action.priority);
    priority.classList.add(action.priority);
    node.querySelector("h3").textContent = action.title;
    node.querySelector("p").textContent = action.body;

    const evidence = node.querySelector(".evidence");
    (action.evidence || []).slice(0, 5).forEach((item) => {
      const chip = document.createElement("span");
      chip.textContent = item;
      evidence.append(chip);
    });
    els.actionsList.append(node);
  });
}

function renderComparison(data) {
  els.comparisonTable.replaceChildren();
  Object.entries(data).forEach(([provider, result]) => {
    const row = document.createElement("div");
    row.className = "comparison-row";
    const label = document.createElement("span");
    label.textContent = titleCase(provider);
    const value = document.createElement("strong");
    if (result.status) {
      value.textContent = titleCase(result.status);
      value.title = result.message || "";
    } else {
      value.textContent = `${result.quality_score.score} pts / ${result.actions.length} actions`;
    }
    row.append(label, value);
    els.comparisonTable.append(row);
  });
}

async function runAutomation() {
  setBusy(true);
  try {
    const result = await requestJson("/api/run-demo", {
      method: "POST",
      body: JSON.stringify({ provider: state.provider, order: state.sampleOrder }),
    });
    renderResult(result);
  } catch (error) {
    els.summaryTitle.textContent = "Automation failed";
    els.resultBadge.textContent = "check config";
    els.actionsList.replaceChildren();
    const message = document.createElement("p");
    message.className = "empty-state";
    message.textContent = error.message;
    els.actionsList.append(message);
  } finally {
    setBusy(false);
  }
}

async function compareProviders() {
  setBusy(true);
  try {
    const result = await requestJson("/api/compare", {
      method: "POST",
      body: JSON.stringify({ order: state.sampleOrder }),
    });
    renderComparison(result);
  } finally {
    setBusy(false);
  }
}

async function boot() {
  els.providerButtons.forEach((button) => {
    button.addEventListener("click", () => setProvider(button.dataset.provider));
  });
  els.runButton.addEventListener("click", runAutomation);
  els.compareButton.addEventListener("click", compareProviders);

  try {
    await requestJson("/health");
    els.health.textContent = "Service online";
    els.health.classList.add("ok");
  } catch {
    els.health.textContent = "Service offline";
    els.health.classList.add("bad");
  }

  state.sampleOrder = await requestJson("/api/sample-order");
  renderOrder(state.sampleOrder);
  await runAutomation();
}

boot();
