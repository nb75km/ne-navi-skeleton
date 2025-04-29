import React, { useState } from 'react';

interface TranscriptToggleProps {
  transcriptId: number;
}

const TranscriptToggle: React.FC<TranscriptToggleProps> = ({ transcriptId }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [script, setScript] = useState<string>('');

  const fetchScript = async () => {
    const res = await fetch(`/minutes/api/transcripts/${transcriptId}`);
    if (!res.ok) return alert('スクリプトの取得に失敗しました');
    const data = await res.json();
    setScript(data.content);
    setIsOpen(true);
  };

  return (
    <>
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40"
          onClick={() => setIsOpen(false)}
        />
      )}
      <div
        className={`fixed right-0 bottom-0 m-4 bg-white shadow-xl rounded-lg z-50 transform transition-transform duration-300 ease-in-out
          ${isOpen ? 'translate-x-0' : 'translate-x-full'}`}
        style={{ width: '300px', height: '60%' }}
      >
        <div className="flex justify-between items-center p-2 border-b">
          <h2 className="text-lg font-semibold">音声スクリプト</h2>
          <button onClick={() => setIsOpen(false)}>✕</button>
        </div>
        <div className="p-4 overflow-auto prose max-h-full">
          {script.split('\n').map((line, i) => (
            <p key={i}>{line}</p>
          ))}
        </div>
      </div>
      <button
        onClick={fetchScript}
        className="fixed right-4 bottom-4 p-3 bg-blue-600 text-white rounded-full shadow-lg hover:bg-blue-700 focus:outline-none z-50"
        aria-label="Show Transcript"
      >
        スクリプト
      </button>
    </>
  );
};

export default TranscriptToggle;
