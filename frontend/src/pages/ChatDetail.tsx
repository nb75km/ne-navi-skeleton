import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { Card } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Loader2 } from "lucide-react";
import { json } from "../lib/api";

interface Message {
  id: number;
  role: string;
  body: string;
  created_at: string;
}

interface Conversation {
  id: number;
  conversation_uid: string;
  title: string | null;
  created_at: string;
}

export default function ChatDetail() {
  const { id } = useParams<{ id: string }>();
  const [msgs, setMsgs] = useState<Message[]>([]);
  const [meta, setMeta] = useState<Conversation | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    (async () => {
      const [{ items }, conv] = await Promise.all([
        json<{ items: Message[] }>(`/chat/api/messages?conversation_id=${id}&limit=200`),
        json<{ items: Conversation[] }>(`/chat/api/conversations?limit=1&id=${id}`),
      ]);
      setMsgs(items);
      setMeta(conv.items ? conv.items[0] : null);
      setLoading(false);
    })();
  }, [id]);

  return (
    <div className="p-4 space-y-4">
      {loading ? (
        <Loader2 className="animate-spin" />
      ) : (
        <>
          <div className="flex items-center gap-2">
            <Link to="/chat" className="text-blue-600 hover:underline">
              ← Back
            </Link>
            <h1 className="text-xl font-bold truncate">
              {meta?.title || meta?.conversation_uid}
            </h1>
          </div>
          <div className="space-y-3">
            {msgs.map((m) => (
              <Card key={m.id} className="p-4">
                <Badge className="mb-2" variant="secondary">
                  {m.role}
                </Badge>
                <p className="whitespace-pre-wrap leading-relaxed">{m.body}</p>
                <p className="text-right text-xs text-gray-500 mt-2">
                  {new Date(m.created_at).toLocaleString()}
                </p>
              </Card>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
