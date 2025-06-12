chrome.action.onClicked.addListener(async (tab) => {
  // 현재 탭의 HTML과 URL을 가져오는 스크립트 실행
  chrome.scripting.executeScript(
    {
      target: { tabId: tab.id },
      func: () => {
        return {
          html: document.documentElement.outerHTML,
          url: window.location.href
        };
      }
    },
    async (injectionResults) => {
      if (chrome.runtime.lastError) {
        return;
      }

      const result = injectionResults[0].result;

      try {
        const response = await fetch('http://localhost:5000/process', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(result)
        });

        const data = await response.json();

         // content.js를 해당 탭에 명시적으로 주입
         await chrome.scripting.executeScript({
          target: { tabId: tab.id },
          files: ['content.js']
        });

        // content script로 메시지를 보내어 DOM 수정 요청
        chrome.tabs.sendMessage(tab.id, {
          action: "modifyDOM",
          data: data
        });

      } catch (error) {
      }
    }
  );
});