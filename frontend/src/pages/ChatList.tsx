import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Card } from "../components/ui/card";
import { json } from "../lib/api";
import { MessageSquareText, Loader2 } from "lucide-react";

interface Conversation {
  id: number;
  conversation_uid: string;
  title: string | null;
  created_at: string;
}

export default function ChatList() {
  const [items, setItems] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    json<{ items: Conversation[] }>("/chat/api/conversations?limit=50").then((d) => {
      setItems(d.items);
      setLoading(false);
    });
  }, []);

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-2xl font-bold flex items-center gap-2">
        <MessageSquareText /> Conversations
      </h1>
      {loading ? (
        <Loader2 className="animate-spin" />
      ) : (
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {items.map((c) => (
            <Card key={c.id} className="p-4 hover:shadow-lg transition">
              <Link to={`/chat/${c.id}`} className="block space-y-1">
                <h2 className="font-semibold truncate">
                  {c.title || "(no title)"}
                </h2>
                <p className="text-sm text-gray-500">
                  {new Date(c.created_at).toLocaleString()}
                </p>
              </Link>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
