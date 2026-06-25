import { CopilotKit } from "@copilotkit/react-core";
import "@copilotkit/react-ui/styles.css";
import type { ReactNode } from "react";
import { apiBase } from "../lib/api";

/**
 * CopilotKit provider — Week 3 scaffold.
 * Full runtime (/copilotkit) is Week 4; chat uses FastAPI /goal directly.
 */
export function DokkebiCopilotRoot({ children }: { children: ReactNode }) {
  return (
    <CopilotKit runtimeUrl={apiBase()} showDevConsole={false}>
      {children}
    </CopilotKit>
  );
}
