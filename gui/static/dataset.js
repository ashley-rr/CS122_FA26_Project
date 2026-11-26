const previewForm = document.querySelector(".preview-controls");

if (previewForm) {
  const status = document.getElementById("preview-status");
  const results = document.getElementById("preview-results");
  const buttons = previewForm.querySelectorAll("button");

  previewForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const selected = event.submitter;
    if (!selected) {
      status.textContent = "Choose a preview button.";
      return;
    }

    buttons.forEach((button) => { button.disabled = true; });
    try {
      const url = new URL(previewForm.dataset.previewUrl, window.location.href);
      url.searchParams.set("preview", selected.value);
      const response = await fetch(url, { cache: "no-store" });
      if (!response.ok) {
        throw new Error(`Preview request failed (HTTP ${response.status}).`);
      }

      results.innerHTML = await response.text();
      buttons.forEach((button) => {
        button.classList.toggle("selected", button === selected);
      });
    } catch (error) {
      status.textContent = "Unable to load the preview. Please try again.";
      console.error(error);
    } finally {
      buttons.forEach((button) => { button.disabled = false; });
    }
  });
}
