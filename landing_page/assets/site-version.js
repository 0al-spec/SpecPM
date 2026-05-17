(function () {
  document.addEventListener("DOMContentLoaded", () => {
    fetch(new URL("./v0/status/index.json", window.location.href), {
      headers: { Accept: "application/json" }
    })
      .then((response) => {
        if (!response.ok) {
          return null;
        }
        return response.json();
      })
      .then((payload) => {
        const implementation = payload?.registry?.implementation;
        if (implementation) {
          updateBuildLabels(implementation);
        }
      })
      .catch(() => {});
  });

  function updateBuildLabels(implementation) {
    const version = implementation.version || "unknown";
    const build = implementation.build || {};
    const number = build.number || "local";
    const revision = build.revision_short || build.revision || "unknown";

    setText("[data-specpm-version]", `SpecPM v${version}`);
    setText("[data-specpm-build]", `Build ${number}`);
    setText("[data-specpm-revision]", `Revision ${revision}`);
    setText("[data-specpm-build-line]", `SpecPM v${version} / build ${number} / ${revision}`);
  }

  function setText(selector, value) {
    document.querySelectorAll(selector).forEach((element) => {
      element.textContent = value;
    });
  }
})();
