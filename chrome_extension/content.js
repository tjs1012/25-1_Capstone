chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "modifyDOM") {
    const data = message.data;

    const normalizePathname = (urlStr) => {
      try {
        const url = new URL(urlStr);
        return url.pathname;
      } catch (e) {
        return urlStr;
      }
    };

    data.forEach((article) => {
      const url = article.url;
      const newTitle = article.new_title;

      console.log("기사 URL:", url, "newTitle:", newTitle);

      const articleElement = Array.from(document.querySelectorAll('li.NewsItem_news_item__fhEmd')).find((item) => {
        const link = item.querySelector('a.NewsItem_link_news__tD7x3');
        if (!link || !link.href) return false;

        const itemPath = normalizePathname(link.href);
        return itemPath === normalizePathname(url);
      });

      if (articleElement) {
        articleElement.style.position = 'relative';
        articleElement.style.border = '3px solid red';
        articleElement.style.padding = '10px';

        if (!articleElement.querySelector('.clickbait-label')) {
          const clickbaitLabel = document.createElement('div');
          clickbaitLabel.className = 'clickbait-label';

          // 🛠️ 이모지용 span
          const emojiSpan = document.createElement('span');
          emojiSpan.innerText = '🔍';
          emojiSpan.style.marginRight = '4px';
          emojiSpan.style.verticalAlign = 'middle';

          // 🛠️ 텍스트용 span
          const textSpan = document.createElement('span');
          textSpan.innerText = `Clickbait - ${newTitle || "제목 없음"}`;

          // ✅ DOM 구성
          clickbaitLabel.appendChild(emojiSpan);
          clickbaitLabel.appendChild(textSpan);

          // ✅ 스타일 설정
          clickbaitLabel.style.position = 'absolute';
          clickbaitLabel.style.left = '0';
          clickbaitLabel.style.top = '0';
          clickbaitLabel.style.backgroundColor = '#ff6347';
          clickbaitLabel.style.color = 'white';
          clickbaitLabel.style.padding = '1px 4px';
          clickbaitLabel.style.fontSize = '17px';
          clickbaitLabel.style.fontWeight = 'bold';
          clickbaitLabel.style.zIndex = '1000';
          clickbaitLabel.style.display = 'flex';
          clickbaitLabel.style.alignItems = 'center';

          articleElement.appendChild(clickbaitLabel);
        }
      }
    });
  }
});