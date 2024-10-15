const AfterAppendix = () => {

  return (
    <div className="text-left mt-8">
      <a href="/">
        <img
          src="https://news.ntv.co.jp/images/logo.svg"
          alt="日テレNEWS NNN｜日本テレビ系NNN30局のニュースサイト"
          style={{ width: '100%', maxWidth: '240px' }}
        />
      </a>
      <a href={`https://news.ntv.co.jp/category/society/1594a26c1d794967a9245ed34e70d681`}>
        衆議院選挙2024ブロードリスニングレポートまとめ
      </a><br />
      <a href={`https://news.ntv.co.jp/pages/kiyaku`}>
        ご利用にあたって
      </a><br />
      <a href={`https://news.ntv.co.jp/pages/cookiepolicy`}>
        Cookieポリシー
      </a><br />
      <a href={`https://news.ntv.co.jp/pages/privacy`}>
        プライバシーポリシー
      </a><br />
      <a href="https://www.ntv.co.jp/election2024/" target="_blank" rel="noopener noreferrer">
        zero選挙2024（衆議院選挙）特設サイト
      </a>
    </div>
  );
};

export default AfterAppendix;
