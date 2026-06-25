import { useTranslation } from "react-i18next";
import { DokkebiChat } from "./components/DokkebiChat";
import { DokkebiCopilotRoot } from "./copilot/DokkebiCopilotRoot";
import "./App.css";

function App() {
  const { t } = useTranslation();

  return (
    <DokkebiCopilotRoot>
      <div className="dokkebi-app">
        <aside className="dokkebi-sidebar">
          <h1>{t("app.title")}</h1>
          <p className="subtitle">{t("app.subtitle")}</p>
          <nav>
            <span className="nav-active">{t("nav.chat")}</span>
            <span className="nav-muted">{t("nav.memory")}</span>
            <span className="nav-muted">{t("nav.settings")}</span>
          </nav>
        </aside>
        <main className="dokkebi-main">
          <DokkebiChat />
        </main>
      </div>
    </DokkebiCopilotRoot>
  );
}

export default App;
