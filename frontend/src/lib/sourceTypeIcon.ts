const icons: Record<string, string> = {
  rss: "📰",
  reddit: "🔴",
  youtube: "▶️",
  email: "✉️",
  mastodon: "🐘",
  arxiv: "🎓",
  scholar: "🎓",
};

export function sourceTypeIcon(type: string): string {
  return icons[type] ?? "📄";
}
