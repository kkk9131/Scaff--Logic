import './styles.css';

function App() {
  return (
    <div className="app">
      <header className="hero">
        <h1>Scaff-logic Frontend</h1>
        <p>Phase 3: 図面インポート & 形状自動判定のためのプレースホルダーUI</p>
      </header>
      <section className="grid">
        <div className="card">
          <h2>アップロード</h2>
          <p>画像(DXF/PDFは今後)をドラッグ＆ドロップして線抽出を開始。</p>
        </div>
        <div className="card">
          <h2>抽出・判定</h2>
          <p>OpenCV.js + ルールベース判定を組み込む予定。</p>
        </div>
        <div className="card">
          <h2>出力</h2>
          <p>JSON / PDF エクスポートをここに配置予定。</p>
        </div>
      </section>
    </div>
  );
}

export default App;
