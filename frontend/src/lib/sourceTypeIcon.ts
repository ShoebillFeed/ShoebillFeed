const icons: Record<string, string> = {
  rss: "📰",
  reddit: "🔴",
  email: "✉️",
  mastodon: "🐘",
  arxiv: "🎓",
};

export function sourceTypeIcon(type: string): string {
  return icons[type] ?? "📄";
}
