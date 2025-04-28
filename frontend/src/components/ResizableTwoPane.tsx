// frontend/src/components/ResizableTwoPane.tsx

import React from 'react';
import { Allotment } from 'allotment';
import 'allotment/dist/style.css';

type Props = {
  left: React.ReactNode;
  right: React.ReactNode;
};

export const ResizableTwoPane: React.FC<Props> = ({ left, right }) => (
  <Allotment className="h-full w-full" defaultSizes={[50, 50]}>
    <Allotment.Pane minSize={200} className="h-full">
      {left}
    </Allotment.Pane>
    <Allotment.Pane minSize={300} className="h-full">
      {right}
    </Allotment.Pane>
  </Allotment>
);
