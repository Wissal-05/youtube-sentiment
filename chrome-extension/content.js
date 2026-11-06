function extractComments(limit = 200) {
  const nodes = document.querySelectorAll(
    "ytd-comment-thread-renderer #content-text, ytd-comment-view-model #content-text"
  );

  const comments = Array.from(nodes)
    // On écarte les réponses (threads) : seuls les commentaires principaux sont analysés
    .filter(node => !node.closest("ytd-comment-replies-renderer"))
    .map(node => node.innerText.trim())
    .filter(text => text.length > 0);

  // Éliminer les doublons
  return [...new Set(comments)].slice(0, limit);
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.action === "extract") {
    try {
      const comments = extractComments(msg.max || 200);
      sendResponse({ comments });
    } catch (error) {
      sendResponse({
        comments: [],
        error: error.message
      });
    }
  }
});