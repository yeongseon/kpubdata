document$.subscribe(function () {
  if (typeof mermaid !== "undefined") {
    document.querySelectorAll("pre code.language-mermaid").forEach(function (codeBlock) {
      var pre = codeBlock.parentElement;
      var container = document.createElement("div");
      container.className = "mermaid";
      container.textContent = codeBlock.textContent;
      if (pre && pre.parentElement) {
        pre.parentElement.replaceChild(container, pre);
      }
    });
    mermaid.initialize({ startOnLoad: true });
    mermaid.run();
  }
});
