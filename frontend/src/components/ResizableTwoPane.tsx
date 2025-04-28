import React from "react";
import { Allotment } from "allotment";
import "allotment/dist/style.css";

interface Props {
  left: React.ReactNode;   // チャットなど
  right: React.ReactNode;  // エディタ
}

export const ResizableTwoPane: React.FC<Props> = ({ left, right }) => (
  <Allotment defaultSizes={[50, 50]}>
    <Allotment.Pane minSize={200}>{left}</Allotment.Pane>
    <Allotment.Pane minSize={300}>{right}</Allotment.Pane>
  </Allotment>
);
