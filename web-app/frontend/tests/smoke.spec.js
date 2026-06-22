// End-to-end smoke tests for the LIF Neuron Simulator frontend.
//
// These exercise our own code (the client-side engine, the form wiring, the
// tab/About swapping) in a real browser. Plotly itself is loaded from a CDN and
// is not what we're testing, so we stub it to a no-op — this keeps the tests
// deterministic and able to run with no external network access.
const { test, expect } = require("@playwright/test");

test.beforeEach(async ({ page }) => {
  // Block the Plotly CDN and provide a recording stub so render* calls succeed.
  await page.route(/cdn\.plot\.ly/, (route) => route.abort());
  await page.addInitScript(() => {
    window.__plotCalls = [];
    window.Plotly = {
      react: (id, data, layout) => window.__plotCalls.push({ id, n: (data || []).length }),
      newPlot: (id, data, layout) => window.__plotCalls.push({ id, n: (data || []).length }),
    };
  });
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  page.__errors = errors;
  await page.goto("/index.html");
});

test("page loads with the Simulation About panel visible by default", async ({ page }) => {
  await expect(page).toHaveTitle(/LIF Neuron Simulator/);
  await expect(page.locator("#about-sim")).toBeVisible();
  await expect(page.locator("#about-fi")).toBeHidden();
  await expect(page.locator("#about-isi")).toBeHidden();
  await expect(page.locator("#about-phase")).toBeHidden();
});

test("default parameters populate from the engine defaults", async ({ page }) => {
  await expect(page.locator("#I")).toHaveValue("1.5");
  await expect(page.locator("#V_thr")).toHaveValue("-55");
  await expect(page.locator("#R")).toHaveValue("10");
});

const tabCases = [
  { tab: "#tab-fi", about: "#about-fi", heading: /F.?I Curve/ },
  { tab: "#tab-isi", about: "#about-isi", heading: /ISI Distribution/ },
  { tab: "#tab-phase", about: "#about-phase", heading: /Phase Portrait/ },
  { tab: "#tab-sim", about: "#about-sim", heading: /Leaky Integrate-and-Fire/ },
];

for (const { tab, about, heading } of tabCases) {
  test(`clicking ${tab} shows only its About panel`, async ({ page }) => {
    await page.click(tab);
    await expect(page.locator(about)).toBeVisible();
    await expect(page.locator(`${about} h2`)).toHaveText(heading);
    // Every other About panel is hidden.
    for (const other of ["#about-sim", "#about-fi", "#about-isi", "#about-phase"]) {
      if (other !== about) await expect(page.locator(other)).toBeHidden();
    }
  });
}

test("running the default simulation reports zero spikes and no error", async ({ page }) => {
  await page.click("#run-btn");
  await expect(page.locator("#spike-summary")).toHaveText(/Total spikes: 0/);
  await expect(page.locator("#error-banner")).toBeHidden();
  expect(page.__errors).toEqual([]);
});

test("suprathreshold current produces spikes", async ({ page }) => {
  await page.fill("#I", "2.0");
  await page.click("#run-btn");
  await expect(page.locator("#spike-summary")).toHaveText(/Total spikes: [1-9]/);
  await expect(page.locator("#spike-stats")).toContainText("Mean rate");
});

test("the 'onset' preset uses np.where and runs without error", async ({ page }) => {
  await page.selectOption("#preset", "onset");
  // Regression guard: the old Python-ternary expression broke the JS engine.
  await expect(page.locator("#I")).toHaveValue("np.where(t > 50, 2.5, 0.0)");
  await page.click("#run-btn");
  await expect(page.locator("#error-banner")).toBeHidden();
  await expect(page.locator("#spike-summary")).toHaveText(/Total spikes: [1-9]/);
});

test("an invalid expression surfaces an error banner", async ({ page }) => {
  await page.fill("#I", "1.5 +");
  await page.click("#run-btn");
  await expect(page.locator("#error-banner")).toBeVisible();
});
