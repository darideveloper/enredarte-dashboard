document.addEventListener("DOMContentLoaded", function () {
  const slugInput = document.querySelector("#id_slug");
  if (!slugInput) return;

  function findEsTitleInput() {
    // 1. Direct check on translations-0-title if it's Spanish
    const lang0 = document.querySelector("#id_translations-0-language");
    if (lang0 && lang0.value === "es") {
      return document.querySelector("#id_translations-0-title");
    }

    // 2. Iterate translation formsets to find whichever is 'es'
    const langInputs = document.querySelectorAll(
      "input[name$='-language'], select[name$='-language']"
    );
    for (const langInput of langInputs) {
      if (langInput.value === "es") {
        const titleName = langInput.name.replace("-language", "-title");
        const titleInput = document.querySelector(`[name="${titleName}"]`);
        if (titleInput) return titleInput;
      }
    }

    // 3. Fallback to first title input inside translation inlines
    return (
      document.querySelector("#id_translations-0-title") ||
      document.querySelector("input[name*='translations'][name$='title']")
    );
  }

  const esTitleInput = findEsTitleInput();
  if (!esTitleInput) return;

  let isManualSlug = slugInput.value.trim().length > 0;

  slugInput.addEventListener("input", function () {
    isManualSlug = slugInput.value.trim().length > 0;
  });

  esTitleInput.addEventListener("input", function () {
    if (isManualSlug) return;

    const slug = esTitleInput.value
      .toLowerCase()
      .trim()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-z0-9\s-]/g, "")
      .replace(/[\s-]+/g, "-")
      .replace(/^-+|-+$/g, "");

    slugInput.value = slug;
  });
});
